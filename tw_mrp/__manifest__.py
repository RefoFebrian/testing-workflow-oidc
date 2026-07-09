# -*- coding: utf-8 -*-
{
    'name': "TW MRP",

    'summary': "Base module for custom MRP functionalities",

    'description': """
This module serves as the foundation for custom Manufacturing Resource Planning (MRP) functionalities. It extends the capabilities of the standard MRP module in Odoo to meet specific business requirements.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",
    'license': 'LGPL-3',

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base', 'tw_base', 'mrp', 'tw_menu'],

    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',

        'wizard/tw_mrp_copy_wizard_view.xml',

        'views/tw_menu.xml',
        'views/tw_mrp_view.xml',
    ],
}

