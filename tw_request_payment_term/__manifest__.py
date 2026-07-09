# Copyright (C) 2024 Tunas Group
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
# -*- coding: utf-8 -*-
{
    'name': 'TW Request Payment Term',
    'version': '18.0.1.0.0',
    'category': 'Back Office',
    'summary': 'Setting Payment Term untuk Partner',
    'description': """
TW Request Payment Term
==================================
Modul ini berfungsi untuk menerapkan jenis payment term
untuk setiap Partner

Features:
- Check apakah sudah ada pengajuan payment term yang sama dan berstatus draft
""",
    'author': "Tunas Group",
    'website': "https://www.tunasgroup.com",
    'depends': [
        'base',
        'tw_base',
        'account',
        'tw_selection',
        'tw_menu',
        'tw_sequence',
        ],
    'data': [
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir.model.access.csv',

        'views/tw_request_payment_term_view.xml',
        'views/tw_menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}