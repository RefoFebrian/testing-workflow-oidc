# -*- coding: utf-8 -*-
{
    'name': "TW - Vehicle Registration Process Upload",

    'summary': "Upload otomatis Proses STNK dari Excel (.xlsx)",

    'description': """
        Vehicle Registration Process Upload
        - Provide import functionality for vehicle registration process
        - Wizard untuk mengunggah file Excel (.xlsx) berisi daftar Branch dan Biro Jasa,
        - kemudian otomatis membuat record tw.vehicle.registration.process per kombinasi.
        - Menampilkan wizard hasil upload setelah proses selesai.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Vehicle Registration Process',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'tw_vehicle_registration_process'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'views/tw_vehicle_registration_process_upload_wizard.xml',
        'views/tw_vehicle_registration_process_upload_result_wizard.xml',
        'views/tw_menu.xml',
    ],

    'installable': True,
    'application': False,
}

