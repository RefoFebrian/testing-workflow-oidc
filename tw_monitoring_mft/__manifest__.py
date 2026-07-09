# -*- coding: utf-8 -*-
{
    'name': "TW MFT Monitoring",

    'summary': "Monitor dan logging data MFT dari Portal AHM.",

    'description': """
        Module untuk memonitor dan mencatat data MFT (Monitoring File Transfer) dari Portal AHM.
        
        Fitur:
        - Konfigurasi tipe file (FILETYPE) yang akan di-monitor
        - Fetch data MFT secara manual atau otomatis via scheduled action
        - Logging hasil transfer file dengan detail error
        - Integrasi dengan tw.api.configuration untuk autentikasi
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    'category': 'Technical',
    'version': '18.0.0.1',
    'license': 'AGPL-3',

    'depends': [
        'base',
        'tw_base',
        'tw_api',
        'tw_menu',
    ],
    
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',

        'data/ir_sequence_data.xml',
        'data/tw_cron_data.xml',
        
        'views/tw_mft_config_views.xml',
        'views/tw_mft_log_views.xml',
        'views/tw_menu.xml',
    ],

    'installable': True,
    'application': False,
}
