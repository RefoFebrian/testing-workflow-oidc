# -*- coding: utf-8 -*-
{
    'name': "TW Progressive Tax Cancel",

    'summary': "TW Progressive Tax Cancel",

    'description': """
        TW Progressive Tax Cancel
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'tw_base',
        'tw_birojasa_billing_process',
        'tw_progressive_tax',
        'tw_menu',
        'tw_cancellation',
        'tw_vehicle_document_cancel',
        'tw_progressive_tax'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',

        'views/tw_account_setting_inherit_view.xml',
        'views/tw_progressive_tax_cancel_view.xml',
        'views/tw_menu.xml',
    ],
}

