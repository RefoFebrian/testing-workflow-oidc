# -*- coding: utf-8 -*-
{
    'name': "Tw Main Dealer Sales Report",

    'summary': "Tw_Main_Dealer_Sales_Report",

    'description': """
Tw Main Dealer Sales Report
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Sales/ TW Sales',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','sale','tw_sale','tw_sale_faktur_pajak'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'views/tw_main_dealer_sales_report_views.xml',
    ],

    'installable': True,
    'application': True,

}

