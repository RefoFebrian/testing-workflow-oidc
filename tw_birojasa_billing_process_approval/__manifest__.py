# -*- coding: utf-8 -*-
{
    'name': "TW - Birojasa Billing Process Approval",
    'summary': "Manajemen Approval Proses Tagihan Birojasa",
    'description': """
TW - Modul Manajemen Approval Proses Tagihan Birojasa
=============================================================================================

Modul ini digunakan untuk mengelola proses approval tagihan birojasa dengan fitur:
- Workflow approval multi-level
- Validasi dokumen tagihan
- Pencatatan riwayat approval
- Integrasi dengan modul birojasa billing process
""",

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories
    'category': 'Document Handling',
    'version': '1.0.0',

    # Dependencies
    'depends': [
        'base',
        'tw_approval',
        'tw_birojasa_billing_process',
    ],

    # Always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups_button.xml',
        'views/tw_birojasa_billing_process_inherit_view.xml',
    ],
    
    # Module settings
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
