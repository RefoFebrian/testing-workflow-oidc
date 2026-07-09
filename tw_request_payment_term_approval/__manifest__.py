# Copyright (C) 2024 Tunas Group
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
# -*- coding: utf-8 -*-
{
    'name': 'TW Request Payment Term Approval',
    'version': '18.0.1.0.0',
    'category': 'Back Office',
    'summary': 'Approval Payment Term untuk Partner',
    'description': """
TW Request Payment Term Approval
==================================
Modul ini berfungsi untuk menambahkan feature Approval
di modul TW Request Payment Term

Features:
- Check apakah sudah ada pengajuan payment term yang sama dan berstatus draft
""",
    'author': "Tunas Group",
    'website': "https://www.tunasgroup.com",
    'depends': [
        'base',
        'tw_base',
        'tw_request_payment_term',
        'tw_approval',
        ],
    'data': [
        'security/res_groups.xml',
        'security/res_button_groups.xml',

        'views/tw_request_payment_term_approval_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
