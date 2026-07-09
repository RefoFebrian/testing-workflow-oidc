# -*- coding: utf-8 -*-
{
    'name': "TW Faktur Pajak Other",

    'summary': "TW Faktur Pajak Other",

    'description': """
TW Faktur Pajak Other

Module untuk mencatat faktur pajak untuk transaksi lain-lain yang tidak tercakup 
dalam model standar seperti Sales Order, Invoice, atau Payment.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'tw_faktur_pajak'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir_rule.xml',

        'views/tw_faktur_pajak_other_view.xml',
        'views/tw_menu.xml',
    ],
}
