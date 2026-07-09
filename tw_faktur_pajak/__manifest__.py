# -*- coding: utf-8 -*-
{
    'name': "TW Faktur Pajak",

    'summary': "Faktur Pajak",

    'description': """
        This Module is used to generate, record, and manage tax invoices automatically from sales and purchase transactions.
        It helps ensure tax compliance and simplifies reporting to the relevant authorities.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','base_suspend_security','tw_menu','tw_branch','tw_partner','tw_account_tax'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir_rule.xml',

        'views/tw_faktur_pajak_view.xml',
        'views/tw_faktur_pajak_out_view.xml',
        'views/tw_menu.xml'
    ],
    'installable': True,
    'application': True,
}

