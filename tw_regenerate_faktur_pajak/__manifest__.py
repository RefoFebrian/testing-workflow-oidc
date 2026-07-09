# -*- coding: utf-8 -*-
{
    'name': "TW Regenerate Faktur Pajak",

    'summary': "Regenerate Faktur Pajak",

    'description': """
        Regenerate Faktur Pajak
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
        'tw_faktur_pajak',
        'tw_dealer_sale_order_faktur_pajak',
        'tw_work_order_faktur_pajak',
        'tw_menu'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',

        'views/tw_regenerate_faktur_pajak_view.xml',
        'views/tw_menu.xml',
    ],
}

