# -*- coding: utf-8 -*-
{
    'name': "TW birojasa billing process upload",

    'summary': "Upload otomatis Tagihan Birojasa dari Excel (.xlsx)",

    'description': """
        Upload otomatis Tagihan Birojasa dari Excel (.xlsx)
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",
    'license': 'LGPL-3',
    
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Document Handling',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_birojasa_billing_process','tw_vehicle_registration_process_upload'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'views/tw_birojasa_biling_upload_wizard.xml',
        'views/tw_birojasa_billing_result_wizard.xml',
    ],
    'installable': True,
    'application': False,
}

