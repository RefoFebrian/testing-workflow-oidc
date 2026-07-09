# -*- coding: utf-8 -*-
{
    'name': "TW - Petty Cash Approval",

    'summary': "Manajemen Approval Proses Petty Cash",

    'description': """
TW - Modul Manajemen Approval Proses Petty Cash
=============================================================================================

Modul ini digunakan untuk mengelola proses approval petty cash dengan fitur:
- Workflow approval multi-level
- Validasi dokumen
- Pencatatan riwayat approval
- Integrasi dengan modul petty cash
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting/Finance',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_approval','tw_petty_cash'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups_button.xml',
        'views/tw_reimbursement_petty_cash_approval_views.xml',
        'views/tw_petty_cash_out_approval_views.xml',
        'views/tw_petty_cash_in_approval_views.xml',
    ],
    # Module settings
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

