# -*- coding: utf-8 -*-
"""
Test Cases untuk Validasi Hak Akses Module tw_p2p
Menguji berbagai skenario akses user sesuai dengan role/group mereka
"""

from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError
from datetime import datetime


class TestP2PAccessRights(TransactionCase):
    """
    Test access rights untuk berbagai role di P2P module
    
    Design:
    - UPDATE group = punya CREATE + WRITE (by design)
    - DELETE group = punya UNLINK
    - READ group = hanya READ
    """

    @classmethod
    def setUpClass(cls):
        super(TestP2PAccessRights, cls).setUpClass()
        
        # Setup Groups
        cls.group_read_unit = cls.env.ref('tw_p2p.group_p2p_purchase_order_unit_read')
        cls.group_update_unit = cls.env.ref('tw_p2p.group_p2p_purchase_order_unit_update')
        cls.group_delete_unit = cls.env.ref('tw_p2p.group_p2p_purchase_order_unit_delete')
        
        cls.group_config_read = cls.env.ref('tw_p2p.group_tw_p2p_config_read')
        cls.group_config_update = cls.env.ref('tw_p2p.group_tw_p2p_config_update')
        cls.group_config_delete = cls.env.ref('tw_p2p.group_tw_p2p_config_delete')
        
        cls.group_product_read = cls.env.ref('tw_p2p.group_tw_p2p_product_read')
        cls.group_product_update = cls.env.ref('tw_p2p.group_tw_p2p_product_update')
        cls.group_product_delete = cls.env.ref('tw_p2p.group_tw_p2p_product_delete')
        
        cls.group_periode_read = cls.env.ref('tw_p2p.group_tw_p2p_periode_read')
        cls.group_periode_update = cls.env.ref('tw_p2p.group_tw_p2p_periode_update')
        cls.group_periode_delete = cls.env.ref('tw_p2p.group_tw_p2p_periode_delete')
        
        # User SPV Logistik Unit (Read, Update, Delete)
        # Note: UPDATE = CREATE + WRITE (by design)
        cls.user_spv = cls.env['res.users'].create({
            'name': 'SPV Logistik Unit Test',
            'login': 'spv_logistik_test',
            'email': 'spv@test.com',
            'groups_id': [(6, 0, [
                cls.group_read_unit.id,
                cls.group_update_unit.id,
                cls.group_delete_unit.id,
                cls.group_config_read.id,
                cls.group_config_update.id,
                cls.group_config_delete.id,
                cls.group_product_read.id,
                cls.group_product_update.id,
                cls.group_product_delete.id,
                cls.group_periode_read.id,
                cls.group_periode_update.id,
                cls.group_periode_delete.id,
            ])]
        })
        
        # User Read-Only (hanya READ, tidak ada UPDATE/DELETE)
        cls.user_read_only = cls.env['res.users'].create({
            'name': 'Read Only User Test',
            'login': 'readonly_test',
            'email': 'readonly@test.com',
            'groups_id': [(6, 0, [
                cls.group_read_unit.id,
                cls.group_config_read.id,
                cls.group_product_read.id,
                cls.group_periode_read.id,
            ])]
        })

    # ========== TEST CASE #1: SPV dengan UPDATE group (Full Access) ==========
    
    def test_01_spv_has_full_access(self):
        """SPV dengan UPDATE group harus punya READ + CREATE + WRITE + UNLINK"""
        # Check permissions
        can_read = self.env['tw.p2p.purchase.order'].with_user(self.user_spv).check_access_rights('read', raise_exception=False)
        can_create = self.env['tw.p2p.purchase.order'].with_user(self.user_spv).check_access_rights('create', raise_exception=False)
        can_write = self.env['tw.p2p.purchase.order'].with_user(self.user_spv).check_access_rights('write', raise_exception=False)
        can_unlink = self.env['tw.p2p.purchase.order'].with_user(self.user_spv).check_access_rights('unlink', raise_exception=False)
        
        # All should be TRUE
        self.assertTrue(can_read, "SPV should have READ access")
        self.assertTrue(can_create, "SPV should have CREATE access (via UPDATE group)")
        self.assertTrue(can_write, "SPV should have WRITE access")
        self.assertTrue(can_unlink, "SPV should have UNLINK access")
    
    def test_02_spv_config_full_access(self):
        """SPV harus punya full access ke Config"""
        can_read = self.env['tw.p2p.config'].with_user(self.user_spv).check_access_rights('read', raise_exception=False)
        can_create = self.env['tw.p2p.config'].with_user(self.user_spv).check_access_rights('create', raise_exception=False)
        can_write = self.env['tw.p2p.config'].with_user(self.user_spv).check_access_rights('write', raise_exception=False)
        can_unlink = self.env['tw.p2p.config'].with_user(self.user_spv).check_access_rights('unlink', raise_exception=False)
        
        self.assertTrue(can_read, "SPV should have READ access to Config")
        self.assertTrue(can_create, "SPV should have CREATE access to Config")
        self.assertTrue(can_write, "SPV should have WRITE access to Config")
        self.assertTrue(can_unlink, "SPV should have UNLINK access to Config")
    
    def test_03_spv_product_full_access(self):
        """SPV harus punya full access ke Product"""
        can_read = self.env['tw.p2p.product'].with_user(self.user_spv).check_access_rights('read', raise_exception=False)
        can_create = self.env['tw.p2p.product'].with_user(self.user_spv).check_access_rights('create', raise_exception=False)
        can_write = self.env['tw.p2p.product'].with_user(self.user_spv).check_access_rights('write', raise_exception=False)
        can_unlink = self.env['tw.p2p.product'].with_user(self.user_spv).check_access_rights('unlink', raise_exception=False)
        
        self.assertTrue(can_read, "SPV should have READ access to Product")
        self.assertTrue(can_create, "SPV should have CREATE access to Product")
        self.assertTrue(can_write, "SPV should have WRITE access to Product")
        self.assertTrue(can_unlink, "SPV should have UNLINK access to Product")
    
    def test_04_spv_periode_full_access(self):
        """SPV harus punya full access ke Periode"""
        can_read = self.env['tw.p2p.periode'].with_user(self.user_spv).check_access_rights('read', raise_exception=False)
        can_create = self.env['tw.p2p.periode'].with_user(self.user_spv).check_access_rights('create', raise_exception=False)
        can_write = self.env['tw.p2p.periode'].with_user(self.user_spv).check_access_rights('write', raise_exception=False)
        can_unlink = self.env['tw.p2p.periode'].with_user(self.user_spv).check_access_rights('unlink', raise_exception=False)
        
        self.assertTrue(can_read, "SPV should have READ access to Periode")
        self.assertTrue(can_create, "SPV should have CREATE access to Periode")
        self.assertTrue(can_write, "SPV should have WRITE access to Periode")
        self.assertTrue(can_unlink, "SPV should have UNLINK access to Periode")

    # ========== TEST CASE #2: Read-Only User (Limited Access) ==========
    
    def test_10_readonly_has_only_read_access(self):
        """Read-only user hanya boleh READ, tidak boleh CREATE/WRITE/UNLINK"""
        can_read = self.env['tw.p2p.purchase.order'].with_user(self.user_read_only).check_access_rights('read', raise_exception=False)
        can_create = self.env['tw.p2p.purchase.order'].with_user(self.user_read_only).check_access_rights('create', raise_exception=False)
        can_write = self.env['tw.p2p.purchase.order'].with_user(self.user_read_only).check_access_rights('write', raise_exception=False)
        can_unlink = self.env['tw.p2p.purchase.order'].with_user(self.user_read_only).check_access_rights('unlink', raise_exception=False)
        
        self.assertTrue(can_read, "Read-only user should have READ access")
        self.assertFalse(can_create, "Read-only user should NOT have CREATE access")
        self.assertFalse(can_write, "Read-only user should NOT have WRITE access")
        self.assertFalse(can_unlink, "Read-only user should NOT have UNLINK access")
    
    def test_11_readonly_config_only_read(self):
        """Read-only user hanya boleh READ Config"""
        can_read = self.env['tw.p2p.config'].with_user(self.user_read_only).check_access_rights('read', raise_exception=False)
        can_create = self.env['tw.p2p.config'].with_user(self.user_read_only).check_access_rights('create', raise_exception=False)
        can_write = self.env['tw.p2p.config'].with_user(self.user_read_only).check_access_rights('write', raise_exception=False)
        can_unlink = self.env['tw.p2p.config'].with_user(self.user_read_only).check_access_rights('unlink', raise_exception=False)
        
        self.assertTrue(can_read, "Read-only should have READ")
        self.assertFalse(can_create, "Read-only should NOT have CREATE")
        self.assertFalse(can_write, "Read-only should NOT have WRITE")
        self.assertFalse(can_unlink, "Read-only should NOT have UNLINK")

    # ========== TEST CASE #3: Verify Group Configuration ==========
    
    def test_20_verify_update_group_has_create_and_write(self):
        """Verify UPDATE group punya CREATE + WRITE permissions (by design)"""
        # Check P2P Purchase Order
        access_rights = self.env['ir.model.access'].sudo().search([
            ('group_id', '=', self.group_update_unit.id),
            ('model_id.model', '=', 'tw.p2p.purchase.order'),
        ])
        
        for access in access_rights:
            # UPDATE group HARUS punya CREATE dan WRITE
            if 'update' in access.name.lower():
                self.assertTrue(access.perm_create, 
                              f"UPDATE group SHOULD have perm_create (by design): {access.name}")
                self.assertTrue(access.perm_write, 
                              f"UPDATE group SHOULD have perm_write: {access.name}")
    
    def test_21_verify_read_group_no_write_access(self):
        """Verify READ group TIDAK punya WRITE/CREATE/UNLINK"""
        access_rights = self.env['ir.model.access'].sudo().search([
            ('group_id', '=', self.group_read_unit.id),
            ('model_id.model', '=', 'tw.p2p.purchase.order'),
        ])
        
        for access in access_rights:
            # READ group TIDAK boleh punya WRITE/CREATE/UNLINK
            self.assertTrue(access.perm_read, f"READ group should have perm_read: {access.name}")
            self.assertFalse(access.perm_create, 
                           f"READ group should NOT have perm_create: {access.name}")
            self.assertFalse(access.perm_write, 
                           f"READ group should NOT have perm_write: {access.name}")
            self.assertFalse(access.perm_unlink, 
                           f"READ group should NOT have perm_unlink: {access.name}")
    
    def test_22_verify_delete_group_has_unlink(self):
        """Verify DELETE group punya UNLINK permission"""
        access_rights = self.env['ir.model.access'].sudo().search([
            ('group_id', '=', self.group_delete_unit.id),
            ('model_id.model', '=', 'tw.p2p.purchase.order'),
        ])
        
        for access in access_rights:
            # DELETE group HARUS punya UNLINK
            if 'delete' in access.name.lower():
                self.assertTrue(access.perm_unlink, 
                              f"DELETE group SHOULD have perm_unlink: {access.name}")

    # ========== TEST CASE #4: User Group Membership ==========
    
    def test_30_verify_spv_has_correct_groups(self):
        """Verifikasi SPV user memiliki group yang benar"""
        user_groups = self.user_spv.groups_id
        
        # Should have these groups
        self.assertIn(self.group_read_unit, user_groups, "SPV should have Read group")
        self.assertIn(self.group_update_unit, user_groups, "SPV should have Update group")
        self.assertIn(self.group_delete_unit, user_groups, "SPV should have Delete group")
    
    def test_31_verify_readonly_has_only_read_groups(self):
        """Verifikasi read-only user hanya punya READ groups"""
        user_groups = self.user_read_only.groups_id
        
        # Should have READ groups
        self.assertIn(self.group_read_unit, user_groups, "Should have Read group")
        
        # Should NOT have UPDATE/DELETE groups
        self.assertNotIn(self.group_update_unit, user_groups, "Should NOT have Update group")
        self.assertNotIn(self.group_delete_unit, user_groups, "Should NOT have Delete group")


# Helper untuk debugging
def print_user_permissions():
    """
    Helper function untuk print permissions user
    Jalankan dari Odoo shell:
    
    from odoo.addons.tw_p2p.tests.test_access_rights import print_user_permissions
    print_user_permissions()
    """
    pass
