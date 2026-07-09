# -*- coding: utf-8 -*-
{
    'name': "TW Upload Supplier Payment",

    'summary': "TW Upload Supplier Payment",

    'description': """
TW Upload Supplier Payment
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_base','tw_menu','tw_payment'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'views/tw_upload_supplier_payment_view.xml',
        'views/tw_menu.xml'
    ],
}

