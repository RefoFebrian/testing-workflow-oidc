# -*- coding: utf-8 -*-
{
    'name': "TW Faktur Pajak Report",

    'summary': "Report Faktur Pajak - Consolidated Module",

    'description': """
        Module untuk mencetak dan generate laporan Faktur Pajak.
        Termasuk:
        - Print Faktur Pajak dengan QWeb Report
        - Generate Detail Faktur Pajak Masukan
        - Laporan All Faktur Pajak (Gabungan/Generate/Others)
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    'category': 'Accounting',
    'version': '0.2',
    'license': 'LGPL-3',

    'depends': [
        'base',
        'tw_base',
        'tw_menu',
        'tw_faktur_pajak',
        'tw_signature_faktur_pajak',
        'tw_remark_faktur_pajak',
    ],

    'data': [
        # Security
        'security/res_groups.xml',
        'security/ir.model.access.csv',

        # Wizards
        'wizard/tw_faktur_pajak_print_wizard_view.xml',
        'wizard/tw_report_faktur_pajak_wizard.xml',

        # Views
        'views/tw_detail_faktur_pajak_masukan_views.xml',
        'views/tw_faktur_pajak_out_view.xml',
        'views/tw_menu_view.xml',

        # Reports
        'report/tw_faktur_pajak_report.xml',
        'report/tw_faktur_pajak_report_template.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': True,
}
