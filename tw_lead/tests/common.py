# -*- coding: utf-8 -*-

"""
Common utilities and base classes for tw_lead tests
"""

from odoo.tests import TransactionCase


class TwLeadTestCase(TransactionCase):
    """Base test case class with common setup for tw_lead tests"""
    
    @classmethod
    def setUpClass(cls):
        super(TwLeadTestCase, cls).setUpClass()
        
        # Common models
        cls.Lead = cls.env['tw.lead']
        cls.Partner = cls.env['res.partner']
        cls.Selection = cls.env['tw.selection']
        cls.Company = cls.env['res.company']
        cls.Product = cls.env['product.product']
        cls.Employee = cls.env['hr.employee']
        
    @classmethod
    def create_test_selection(cls, name, value, selection_type):
        """Helper to create test selection records"""
        return cls.Selection.create({
            'name': name,
            'value': value,
            'type': selection_type
        })
    
    @classmethod
    def create_test_lead(cls, identification_number='1234567890123456', **kwargs):
        """Helper to create test lead with default values"""
        vals = {
            'customer_name': 'Test Customer',
            'mobile': '081234567890',
            'identification_number': identification_number,
        }
        vals.update(kwargs)
        return cls.Lead.create(vals)
    
    def assertStateTransition(self, record, from_state, to_state, action_method):
        """Helper to assert state transitions"""
        self.assertEqual(record.state, from_state, f"Record should be in {from_state} state")
        action_method()
        self.assertEqual(record.state, to_state, f"Record should transition to {to_state} state")
