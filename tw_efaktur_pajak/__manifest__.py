# -*- coding: utf-8 -*-
{
    'name': "TW Generate eFaktur Pajak",
    'summary': "Generate eFaktur Pajak Excel Report for DJP Import",
    'description': """
Generate eFaktur Pajak Excel Report for DJP import.
Supports multiple transaction types:
- Sale Order
- Dealer Sale Order  
- Work Order
- DN/NC
- Disposal Asset
- Faktur Pajak Other/Gabungan
    """,
    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",
    'category': 'Accounting',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',
    'depends': [
        'tw_base',
        'tw_faktur_pajak',
        'web_report',
    ],
    'data': [
        'security/res_groups.xml',
        'views/tw_efaktur_pajak_wizard_view.xml',
    ],
}
