# -*- coding: utf-8 -*-
{
    'name': "Website Self Register (WhatsApp)",

    'summary': "Website Self Register with WA Configurations",

    'description': """
Website Self Register with WA Configurations
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
    'depends': ['base', 'website_self_register', 'tw_whatsapp_api'],

    # always loaded
    'data': [
        'data/self_register_content_wa.xml',
    ],
}

