# -*- coding: utf-8 -*-
{
    'name': "TW Vehicle Document Update Data Approval",

    'description': """
TW - Modul Manajemen Approval Proses Perubahan data serial number
=============================================================================================

Modul ini digunakan untuk mengelola proses approval perubahan data serial number dengan fitur:
- Workflow approval multi-level
- Validasi dokumen perubahan
- Pencatatan riwayat approval
- Integrasi dengan modul vehicle document update data
""",
    'license': 'LGPL-3',
    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': "LGPL-3",

    # any module necessary for this one to work correctly
    'depends': ['base','tw_approval','tw_vehicle_document_update_data'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/tw_vehicle_document_update_data_approval_form_views.xml',
        'views/tw_vehicle_document_update_data_approval_search_views.xml',
        # 'data/tw_approval_config_data.xml', #Dikomen karena data sudah di import
    ],
    
    'installable': True,
}

