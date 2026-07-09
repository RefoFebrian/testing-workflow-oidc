# -*- coding: utf-8 -*-
{
    'name': "TW - Birojasa Billing Process",
    'summary': "Manajemen Proses Tagihan Birojasa",
    'description': """
TW - Modul Manajemen Proses Tagihan Birojasa
==========================================

Modul ini digunakan untuk mengelola proses tagihan birojasa dengan fitur:
- Pembuatan dan pengelolaan dokumen tagihan birojasa
- Proses approval multi-level
- Integrasi dengan modul akuntansi
- Pelacakan status pembayaran
- Laporan tagihan birojasa

Fitur Utama:
- Workflow lengkap dari Draft sampai Done
- Approval multi-level
- Pencatatan riwayat perubahan
- Integrasi dengan modul lain yang terkait
""",

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories
    'category': 'Document Handling',
    'version': '1.0.0',

    # Dependencies
    'depends': [
        'base',
        'tw_base',
        'account',
        'tw_vehicle_document',
        'tw_vehicle_document_receipt',
        'tw_account_setting',
    ],

    # Always loaded
    'data': [
        'report/tw_birojasa_billing_process_report.xml',
        'report/tw_birojasa_view.xml',

        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir_rule.xml',
        
        'views/tw_birojasa_billing_process_view.xml',
        'views/tw_menu.xml',
        'views/tw_stock_lot_inherit_view.xml',
        'views/tw_account_setting_inherit_view.xml',
    ],
    
    # Only loaded in demonstration mode
    'demo': [],
    
    # Module settings
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
