# -*- coding: utf-8 -*-
{
    'name': "TW - Vehicle Registration Handover Upload",

    'summary': "Upload otomatis penyerahan STNK(handover) dari Excel",

    'description': """
Long description of module's purpose
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Document Handling',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'tw_base',
        'stock',
        'tw_vehicle_document',
        'tw_vehicle_document_handover',
        'tw_vehicle_registration_process_upload'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'views/tw_vehicle_registration_handover_upload_views.xml',
        'views/tw_vehicle_registration_handover_upload_result_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

