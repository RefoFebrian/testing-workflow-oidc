# -*- coding: utf-8 -*-
{
    'name': "TW Account Partner",

    'summary': "Extends Odoo accounting with custom partner account features",

    'description': """
    This module extends the functionality of the Odoo accounting module by adding custom features for managing partner accounts. It includes custom views and additional fields to enhance the user experience and provide more detailed information about partners.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'AGPL-3',

    'depends': ['base','tw_base','account','tw_partner'],

    'data': [
        'views/tw_account_partner_views.xml',
    ],
}

