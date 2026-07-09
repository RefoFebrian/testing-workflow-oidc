# -*- coding: utf-8 -*-
{
    'name': "TW Print Counter",

    'summary': "Print Counter Report",

    'description': """
        Helps track the number of times reports have been printed. 
        It records each print action, ensuring accurate monitoring of report usage and preventing unnecessary reprints.
        This module is useful for maintaining print logs, auditing print history, and optimizing document management within the organization.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Report',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','base_suspend_security'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
}

