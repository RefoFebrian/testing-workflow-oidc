# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) PySquad Informetics (<https://pysquad.com/>).
#
#    For Module Support : contact@pysquad.com
#
##############################################################################

{
    # Module Information
    "name": "Search on One2many/Many2many",
    "version": "18.0.0.0.0",
    "category": "custom",
    "description": "search option on one2many and many2many relational field",
    "summary": """Search option helps to search record from one2many and many2many field.
                  Search On Relational Fields.
                  Search on One2many/Many2many field.
                  Search using Product from multiple Lines.
                  Quick Search on One2many and Many2many""",

    # Author
    "author": "Pysquad Informatics LLP",
    "website": "https://www.pysquad.com",
    "license":"LGPL-3",

    # Dependencies
    "depends": ["base", "purchase", "sale", "sale_management", "account"],

    # Data File
    "data": [
        'views/form_view_inherits.xml'
    ],

    'assets': {
        'web.assets_backend': [
            'ps_search_one2many_many2many/static/src/css/relational_field.css',
            'ps_search_one2many_many2many/static/src/js/relational_field.js',
            'ps_search_one2many_many2many/static/src/xml/relational_field.xml',
        ],
    },
    "images": [
        'static/description/banner_img.png',
    ],

    # Technical Specif.
    'installable': True,
    'application': False,
    'auto_install': False,
}
