# -*- coding: utf-8 -*-
{
    'name': "TW Stock Opname Asset",

    'summary': "TW Stock Opname Asset",

    'description': "TW Stock Opname Asset",

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_base','tw_web','tw_menu','tw_asset_management','tw_attachment'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir_rule.xml',
        
        'views/tw_stock_opname_asset_view.xml',
        'views/tw_menu.xml',

        'reports/tw_stock_opname_asset_baso_template.xml',
        'reports/tw_stock_opname_asset_baso_wizard.xml',
        'reports/tw_stock_opname_asset_print_validasi_template.xml',

    ]
}

