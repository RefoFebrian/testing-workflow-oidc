{
    'name': 'TW Partner CDB Management',
    'version': '1.0',
    'category': 'Customer Relationship Management',
    'summary': 'Manage Partner Customer Database (CDB)',
    'description': """
        Partner CDB Management Module
        ============================
        
        This module provides functionality to manage Customer Database (CDB) information
        for partners in the system. It includes fields for contact details, social media,
        address information, and vehicle details.
        
        Key Features:
        - Store comprehensive customer data
        - Track contact information
        - Manage social media profiles
        - Record vehicle details
    """,
    'author': "Tunas Honda",
    'license': "LGPL-3",
    'website': "",

    'depends': [
        'base',
        'tw_partner',
        'base_suspend_security',
        'tw_selection',
        'tw_hr',
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/ir_rule.xml',

        'views/tw_partner_cdb_view.xml',
        'views/tw_partner_customer_inherit_view.xml',
        'views/tw_stock_lot_inherit_view.xml',
        'views/tw_menu_view.xml',
    ],


    'application':True,
    'installable':True,
}
