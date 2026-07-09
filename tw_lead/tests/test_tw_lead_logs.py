# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'tw_lead')
class TestTwLeadLogs(TransactionCase):
    """Test cases for tw.lead.logs model"""

    @classmethod
    def setUpClass(cls):
        super(TestTwLeadLogs, cls).setUpClass()
        
        cls.Lead = cls.env['tw.lead']
        cls.LeadLog = cls.env['tw.lead.logs']
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
        
        # Get or create log category selections
        cls.log_cat_general = cls.Selection.search([('type', '=', 'LogCategory'), ('value', '=', 'general')], limit=1)
        if not cls.log_cat_general:
            cls.log_cat_general = cls.Selection.create({'name': 'General', 'value': 'general', 'type': 'LogCategory'})
        
        cls.log_cat_followup = cls.Selection.search([('type', '=', 'LogCategory'), ('value', '=', 'follow_up')], limit=1)
        if not cls.log_cat_followup:
            cls.log_cat_followup = cls.Selection.create({'name': 'Follow Up', 'value': 'follow_up', 'type': 'LogCategory'})
        
        cls.log_cat_meeting = cls.Selection.search([('type', '=', 'LogCategory'), ('value', '=', 'meeting')], limit=1)
        if not cls.log_cat_meeting:
            cls.log_cat_meeting = cls.Selection.create({'name': 'Meeting', 'value': 'meeting', 'type': 'LogCategory'})
        
        # Get or create other necessary selections
        cls.interest_cold = cls.Selection.search([('type', '=', 'Interest'), ('value', '=', 'cold')], limit=1)
        if not cls.interest_cold:
            cls.interest_cold = cls.Selection.create({'name': 'Cold', 'value': 'cold', 'type': 'Interest'})
        
        cls.data_source = cls.Selection.search([('type', '=', 'DataSource'), ('value', '=', 'web')], limit=1)
        if not cls.data_source:
            cls.data_source = cls.Selection.create({'name': 'Web', 'value': 'web', 'type': 'DataSource'})
        
        # Create test lead
        cls.test_lead = cls.Lead.create({
            'customer_name': 'Test Customer for Logs',
            'mobile': '081234567890',
            'identification_number': '1234567890123456',
            'company_id': cls.test_company.id,
            'interest_id': cls.interest_cold.id,
            'data_source_id': cls.data_source.id,
        })

    def test_01_create_log_basic(self):
        """Test basic log creation"""
        log = self.LeadLog.create({
            'lead_id': self.test_lead.id,
            'name': 'Initial contact with customer',
            'category_id': self.log_cat_general.id,
        })
        
        self.assertTrue(log.id, "Log should be created")
        self.assertEqual(log.name, 'Initial contact with customer')
        self.assertTrue(log.date, "Date should be set automatically")

    def test_02_log_name_required(self):
        """Test that log name is required"""
        from psycopg2 import IntegrityError
        
        with self.assertRaises(IntegrityError, msg="Should raise IntegrityError for missing name"):
            self.LeadLog.create({
                'lead_id': self.test_lead.id,
                'category_id': self.log_cat_general.id,
            })

    def test_03_default_datetime(self):
        """Test that datetime is set to current time by default"""
        before_create = datetime.now()
        
        log = self.LeadLog.create({
            'lead_id': self.test_lead.id,
            'name': 'Test log with auto datetime',
            'category_id': self.log_cat_general.id,
        })
        
        after_create = datetime.now()
        
        self.assertTrue(log.date, "Date should be set")
        self.assertGreaterEqual(log.date, before_create)
        self.assertLessEqual(log.date, after_create)

    def test_04_multiple_logs_per_lead(self):
        """Test that multiple logs can be created for one lead"""
        log1 = self.LeadLog.create({
            'lead_id': self.test_lead.id,
            'name': 'First contact',
            'category_id': self.log_cat_general.id,
        })
        
        log2 = self.LeadLog.create({
            'lead_id': self.test_lead.id,
            'name': 'Follow up call',
            'category_id': self.log_cat_followup.id,
        })
        
        log3 = self.LeadLog.create({
            'lead_id': self.test_lead.id,
            'name': 'Meeting scheduled',
            'category_id': self.log_cat_meeting.id,
        })
        
        self.assertEqual(len(self.test_lead.log_ids), 3, "Should have 3 logs")

    def test_05_log_ordering(self):
        """Test that logs are ordered by date ascending"""
        # Create logs with different dates
        old_date = datetime.now() - timedelta(days=2)
        recent_date = datetime.now() - timedelta(days=1)
        current_date = datetime.now()
        
        log1 = self.LeadLog.create({
            'lead_id': self.test_lead.id,
            'name': 'Recent log',
            'category_id': self.log_cat_general.id,
            'date': recent_date,
        })
        
        log2 = self.LeadLog.create({
            'lead_id': self.test_lead.id,
            'name': 'Old log',
            'category_id': self.log_cat_general.id,
            'date': old_date,
        })
        
        log3 = self.LeadLog.create({
            'lead_id': self.test_lead.id,
            'name': 'Current log',
            'category_id': self.log_cat_general.id,
            'date': current_date,
        })
        
        # Search with default order
        logs = self.LeadLog.search([('lead_id', '=', self.test_lead.id)])
        
        # Should be ordered by date ascending (old to new)
        dates = [log.date for log in logs]
        self.assertEqual(dates, sorted(dates), "Logs should be ordered by date ascending")

    def test_06_lead_relationship(self):
        """Test relationship between log and lead"""
        log = self.LeadLog.create({
            'lead_id': self.test_lead.id,
            'name': 'Relationship test',
            'category_id': self.log_cat_general.id,
        })
        
        self.assertEqual(log.lead_id.id, self.test_lead.id)
        self.assertIn(log, self.test_lead.log_ids)

    def test_07_category_relationship(self):
        """Test log category selection relationship"""
        log = self.LeadLog.create({
            'lead_id': self.test_lead.id,
            'name': 'Category test',
            'category_id': self.log_cat_followup.id,
        })
        
        self.assertEqual(log.category_id.id, self.log_cat_followup.id)
        self.assertEqual(log.category_id.value, 'follow_up')

    def test_08_log_without_category(self):
        """Test that log can be created without category (optional)"""
        log = self.LeadLog.create({
            'lead_id': self.test_lead.id,
            'name': 'Log without category',
        })
        
        self.assertTrue(log.id, "Log should be created without category")
        self.assertFalse(log.category_id, "Category should be empty")

    def test_09_log_created_on_state_change(self):
        """Test that logs are automatically created on state changes"""
        # Clear any existing logs for clean test
        initial_log_count = len(self.test_lead.log_ids)
        
        # Perform action that should create log
        self.test_lead.action_deal()
        
        # Should have one more log
        self.assertGreater(
            len(self.test_lead.log_ids),
            initial_log_count,
            "Log should be created on action_deal"
        )
        
        # Check last log
        last_log = self.test_lead.log_ids.sorted('date', reverse=True)[0]
        self.assertIn('Dealing', last_log.name, "Log should mention dealing")

    def test_10_log_created_on_propose(self):
        """Test that log is created when proposing"""
        # Setup lead for proposal
        product = self.env['product.product'].search([('sale_ok', '=', True)], limit=1)
        if not product:
            product = self.env['product.product'].create({
                'name': 'Test Product for Log',
                'type': 'product',
                'sale_ok': True,
                'list_price': 25000000.0,
            })
        
        payment_type_credit = self.Selection.search([('type', '=', 'PaymentType'), ('value', '=', 'Credit')], limit=1)
        if not payment_type_credit:
            payment_type_credit = self.Selection.create({'name': 'Credit', 'value': 'Credit', 'type': 'PaymentType'})
        
        unit_availability_ready = self.Selection.search([('type', '=', 'UnitAvailability'), ('value', '=', 'ready')], limit=1)
        if not unit_availability_ready:
            unit_availability_ready = self.Selection.create({'name': 'Ready', 'value': 'ready', 'type': 'UnitAvailability'})
        
        self.test_lead.write({
            'product_id': product.id,
            'payment_type_id': payment_type_credit.id,
            'price_otr': 25000000.0,
            'unit_availability_id': unit_availability_ready.id,
        })
        
        self.test_lead.action_deal()
        initial_log_count = len(self.test_lead.log_ids)
        
        self.test_lead.action_propose()
        
        # Should have more logs after propose
        self.assertGreater(
            len(self.test_lead.log_ids),
            initial_log_count,
            "Log should be created on action_propose"
        )

    def test_11_log_created_on_reject(self):
        """Test that log is created when rejecting"""
        self.test_lead.action_deal()
        initial_log_count = len(self.test_lead.log_ids)
        
        self.test_lead = self.test_lead.with_context(rejection_reason='Test rejection')
        self.test_lead.action_reject()
        
        self.assertGreater(
            len(self.test_lead.log_ids),
            initial_log_count,
            "Log should be created on action_reject"
        )

    def test_12_log_created_on_approve(self):
        """Test that log is created when approving"""
        product = self.env['product.product'].search([('sale_ok', '=', True)], limit=1)
        if not product:
            product = self.env['product.product'].create({
                'name': 'Test Product',
                'type': 'product',
                'sale_ok': True,
                'list_price': 25000000.0,
            })
        
        payment_type_cash = self.Selection.search([('type', '=', 'PaymentType'), ('value', '=', 'cash')], limit=1)
        if not payment_type_cash:
            payment_type_cash = self.Selection.create({'name': 'Cash', 'value': 'cash', 'type': 'PaymentType'})
        
        self.test_lead.write({
            'product_id': product.id,
            'payment_type_id': payment_type_cash.id,
            'price_otr': 25000000.0,
        })
        
        self.test_lead.action_deal()
        
        # Get log count before approval (action_propose auto-approves)
        before_count = len(self.test_lead.log_ids)
        
        # Note: action_approve is called within action_propose in this implementation
        # So we test it directly
        self.test_lead.write({'state': 'dealt'})  # Reset state
        initial_log_count = len(self.test_lead.log_ids)
        
        self.test_lead.action_approved()
        
        self.assertGreater(
            len(self.test_lead.log_ids),
            initial_log_count,
            "Log should be created on action_approved"
        )

    def test_13_custom_log_entry(self):
        """Test creating custom log entry with specific details"""
        specific_date = datetime.now() - timedelta(hours=2)
        
        log = self.LeadLog.create({
            'lead_id': self.test_lead.id,
            'name': 'Customer called requesting information about payment options',
            'category_id': self.log_cat_followup.id,
            'date': specific_date,
        })
        
        self.assertEqual(log.date, specific_date, "Should use custom date")
        self.assertEqual(log.category_id.id, self.log_cat_followup.id)
