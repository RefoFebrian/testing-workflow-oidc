# -*- coding: utf-8 -*-
{
    'name': "TW Dealer Sale Order Faktur Pajak",

    'summary': "TW Dealer Sale Order Faktur Pajak",

    'description': """
    TW Dealer Sale Order Faktur Pajak
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',
    'application': False,

    # any module necessary for this one to work correctly
    'depends': ['base','tw_dealer_sale_order','tw_faktur_pajak','tw_faktur_pajak_core_tax'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/tw_dealer_sale_order_faktur_pajak_view.xml',
    ]
}

