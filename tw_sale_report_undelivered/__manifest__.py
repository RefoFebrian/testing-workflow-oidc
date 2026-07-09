# -*- coding: utf-8 -*-
{
    'name': "TW Sale Report Undelivered",

    'summary': "Sale Order Report Undelivered provides a summary of confirmed sales orders with items that have not yet been fully delivered to customers.",

    'description': """
        Sale Order Report Undelivered is used to display a list of sales orders that have not been fully delivered. This report helps the operations and logistics teams monitor the delivery status of confirmed orders where some or all items have not yet been received by the customer, making it easier to follow up and manage outstanding deliveries.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Report / TW Report',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','base_suspend_security','tw_branch','tw_selection','web_report'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'views/tw_sale_report_undelivered_view.xml',
        'views/tw_menu_view.xml',
    ],
    'installable': True,
    'application': True,
}

