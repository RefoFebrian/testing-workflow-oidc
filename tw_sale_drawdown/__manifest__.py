# -*- coding: utf-8 -*-
{
    'name': "TW Sale Drawdown",

    'summary': "Partner Drawdown Field Adjustment in Sales Module",

    'description': """
        Partner Drawdown Field Adjustment in Sales Module
        - Add drawdown_unit and drawdown_sparepart fields to partners
        - Provide import/export functionality for drawdown values
        - Add menu items in Showroom and Master for easy access
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Sales / TW Sales',
    'version': '0.2',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'base_suspend_security',
        'tw_sale',
        'tw_partner',
        'tw_sale_plafond',
        'web'
    ],
    
    # always loaded
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'views/tw_sale_drawdown_view.xml',
        'views/tw_sale_drawdown_partner_view.xml',
        'views/tw_partner_drawdown_upload_views.xml',
        'views/tw_menu_views.xml',
    ],
    'installable': True,
    'application': True,
}

