# -*- coding: utf-8 -*-
{
    'name': "TW RPA Sparepart Distribution Whatsapp",

    'summary': """
        Notification RPA Sparepart Distribution with Whatsapp Integration
        """,

    'description': """
        Checking whether the function of the RPA Sparepart Distribution Module is running or not. 
        If it is not running, the system will send a notification message using Whatsapp to the PIC RPA Sparepart Distribution.
    """,

    'author': "Tunas Honda",
    'license': "LGPL-3",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/10.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'TW Sales/ TW Sales',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'tw_rpa_sparepart_distribution',
        'tw_whatsapp_api',
    ],

    # always loaded
    'data': [
        'data/scheduled_actions.xml',
        'data/tw_rpa_distribution_whatsapp_template.xml',
    ],

    'application':True,
    'installable':True, 
}