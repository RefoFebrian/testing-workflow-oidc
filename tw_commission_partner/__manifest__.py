# -*- coding: utf-8 -*-
{
    'name': "TW Partner Commission",

    'summary': "Extends Odoo Partner with custom partner commission features",

    'description': """
    This module extends the functionality of the Odoo Partner module by adding custom features for managing partner commission. It includes custom views and additional fields to enhance the user experience and provide more detailed information about partners.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'AGPL-3',

    'depends': ['base','tw_base','tw_partner'],

    'data': [
        'views/tw_partner_inherit_view.xml',
    ],
}

