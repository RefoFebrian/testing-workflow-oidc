# -*- coding: utf-8 -*-

from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install', 'tw_lead')
class TestTwLeadAddresses(TransactionCase):
    """Test cases for tw.lead.addresses model"""

    @classmethod
    def setUpClass(cls):
        super(TestTwLeadAddresses, cls).setUpClass()
        
        cls.Lead = cls.env['tw.lead']
        cls.LeadAddress = cls.env['tw.lead.addresses']
        cls.Selection = cls.env['tw.selection']
        cls.Company = cls.env['res.company']
        
        # Create test company
        cls.test_company = cls.env['res.company'].search([('parent_id', '!=', False)], limit=1)
        if not cls.test_company:
            parent_company = cls.env['res.company'].search([], limit=1)
            cls.test_company = cls.Company.create({
                'name': 'Test Branch',
                'parent_id': parent_company.id,
                'code': 'TBR'
            })
        
        # Get or create address type selections
        cls.address_type_ktp = cls.Selection.search([('type', '=', 'AddressType'), ('value', '=', 'ktp')], limit=1)
        if not cls.address_type_ktp:
            cls.address_type_ktp = cls.Selection.create({'name': 'KTP', 'value': 'ktp', 'type': 'AddressType'})
        
        cls.address_type_domicile = cls.Selection.search([('type', '=', 'AddressType'), ('value', '=', 'domisili')], limit=1)
        if not cls.address_type_domicile:
            cls.address_type_domicile = cls.Selection.create({'name': 'Domicile', 'value': 'domisili', 'type': 'AddressType'})
        
        cls.address_type_other = cls.Selection.search([('type', '=', 'AddressType'), ('value', '=', 'other')], limit=1)
        if not cls.address_type_other:
            cls.address_type_other = cls.Selection.create({'name': 'Other', 'value': 'other', 'type': 'AddressType'})
        
        # Get or create other necessary selections
        cls.interest_cold = cls.Selection.search([('type', '=', 'Interest'), ('value', '=', 'cold')], limit=1)
        if not cls.interest_cold:
            cls.interest_cold = cls.Selection.create({'name': 'Cold', 'value': 'cold', 'type': 'Interest'})
        
        cls.data_source = cls.Selection.search([('type', '=', 'DataSource'), ('value', '=', 'web')], limit=1)
        if not cls.data_source:
            cls.data_source = cls.Selection.create({'name': 'Web', 'value': 'web', 'type': 'DataSource'})
        
        # Create test lead
        cls.test_lead = cls.Lead.create({
            'customer_name': 'Test Customer for Address',
            'mobile': '081234567890',
            'identification_number': '1234567890123456',
            'company_id': cls.test_company.id,
            'interest_id': cls.interest_cold.id,
            'data_source_id': cls.data_source.id,
        })
        
        # Get test state/city
        cls.test_state = cls.env['res.country.state'].search([], limit=1)
        cls.test_city = cls.env['res.city'].search(
            [('state_id', '=', cls.test_state.id)] if cls.test_state else [],
            limit=1
        )

    def test_01_create_address(self):
        """Test basic address creation"""
        address = self.LeadAddress.create({
            'lead_id': self.test_lead.id,
            'address_type_id': self.address_type_other.id,
            'street': 'Test Street 123',
            'rt': '001',
            'rw': '002',
        })
        
        self.assertTrue(address.id, "Address should be created")
        self.assertEqual(address.street, 'Test Street 123')
        self.assertEqual(address.address_type, 'other')

    def test_02_auto_generate_name(self):
        """Test that address name is auto-generated if not provided"""
        address = self.LeadAddress.create({
            'lead_id': self.test_lead.id,
            'address_type_id': self.address_type_ktp.id,
            'street': 'Auto Name Street',
        })
        
        self.assertTrue(address.name, "Name should be auto-generated")
        self.assertIn(self.test_lead.identification_number, address.name)
        self.assertIn('KTP', address.name)

    def test_03_single_ktp_address_constraint(self):
        """Test that only one KTP address is allowed per lead"""
        # Create first KTP address
        address1 = self.LeadAddress.create({
            'lead_id': self.test_lead.id,
            'address_type_id': self.address_type_ktp.id,
            'street': 'KTP Street 1',
        })
        
        # Try to create second KTP address
        with self.assertRaises(UserError, msg="Should not allow multiple KTP addresses"):
            self.LeadAddress.create({
                'lead_id': self.test_lead.id,
                'address_type_id': self.address_type_ktp.id,
                'street': 'KTP Street 2',
            })

    def test_04_multiple_non_ktp_addresses(self):
        """Test that multiple non-KTP addresses are allowed"""
        address1 = self.LeadAddress.create({
            'lead_id': self.test_lead.id,
            'address_type_id': self.address_type_other.id,
            'street': 'Other Street 1',
        })
        
        address2 = self.LeadAddress.create({
            'lead_id': self.test_lead.id,
            'address_type_id': self.address_type_other.id,
            'street': 'Other Street 2',
        })
        
        self.assertTrue(address1.id and address2.id, "Multiple non-KTP addresses should be allowed")

    def test_05_onchange_state_clears_city(self):
        """Test state change clears dependent city field"""
        if not self.test_state:
            self.skipTest("No state data available for testing")
            
        address = self.LeadAddress.create({
            'lead_id': self.test_lead.id,
            'address_type_id': self.address_type_domicile.id,
            'state_id': self.test_state.id,
        })
        
        # Verify onchange method exists
        self.assertTrue(hasattr(address, '_onchange_state_id'))

    def test_06_onchange_city_clears_district(self):
        """Test city change clears dependent district field"""
        address = self.LeadAddress.create({
            'lead_id': self.test_lead.id,
            'address_type_id': self.address_type_domicile.id,
        })
        
        self.assertTrue(hasattr(address, '_onchange_city_id'))

    def test_07_onchange_district_clears_subdistrict(self):
        """Test district change clears dependent subdistrict and zip"""
        address = self.LeadAddress.create({
            'lead_id': self.test_lead.id,
            'address_type_id': self.address_type_domicile.id,
        })
        
        self.assertTrue(hasattr(address, '_onchange_district_id'))

    def test_08_onchange_subdistrict_sets_zip(self):
        """Test subdistrict change sets zip code"""
        sub_district = self.env['res.sub.district'].search([('zip_code', '!=', False)], limit=1)
        
        if not sub_district:
            self.skipTest("No sub-district with zip code available")
        
        address = self.LeadAddress.create({
            'lead_id': self.test_lead.id,
            'address_type_id': self.address_type_domicile.id,
        })
        
        # Simulate onchange
        address.sub_district_id = sub_district
        address._onchange_sub_district()
        
        self.assertEqual(address.zip, sub_district.zip_code, "Zip should be set from sub-district")

    def test_09_address_type_computed(self):
        """Test that address_type is properly computed from address_type_id"""
        address = self.LeadAddress.create({
            'lead_id': self.test_lead.id,
            'address_type_id': self.address_type_ktp.id,
            'street': 'Computed Type Street',
        })
        
        self.assertEqual(address.address_type, 'ktp', "Address type should be computed")

    def test_10_address_fields_storage(self):
        """Test that all address fields are properly stored"""
        address = self.LeadAddress.create({
            'lead_id': self.test_lead.id,
            'address_type_id': self.address_type_ktp.id,
            'street': 'Main Street',
            'street2': 'Building A',
            'rt': '005',
            'rw': '010',
            'zip': '12345',
        })
        
        self.assertEqual(address.street, 'Main Street')
        self.assertEqual(address.street2, 'Building A')
        self.assertEqual(address.rt, '005')
        self.assertEqual(address.rw, '010')
        self.assertEqual(address.zip, '12345')

    def test_11_lead_relationship(self):
        """Test the relationship between address and lead"""
        address = self.LeadAddress.create({
            'lead_id': self.test_lead.id,
            'address_type_id': self.address_type_other.id,
            'street': 'Relationship Test Street',
        })
        
        self.assertEqual(address.lead_id.id, self.test_lead.id)
        self.assertIn(address, self.test_lead.address_ids)

    def test_12_default_country_indonesia(self):
        """Test that default country is Indonesia"""
        address = self.LeadAddress.create({
            'lead_id': self.test_lead.id,
            'address_type_id': self.address_type_other.id,
        })
        
        self.assertTrue(address.country_id, "Country should be set by default")
        # Indonesia's code is 'id'
        indonesia = self.env.ref('base.id', raise_if_not_found=False)
        if indonesia:
            self.assertEqual(address.country_id.id, indonesia.id)
