# -*- coding: utf-8 -*-
{
    'name': "TW MFT Monitoring with Telegram",

    'summary': "Integrasi notifikasi Telegram untuk MFT Monitoring",

    'description': """
        Module untuk mengirim notifikasi Telegram terkait MFT Monitoring.
        
        Fitur:
        - Notifikasi saat ada file dengan error
        - Notifikasi summary harian
        - Konfigurasi penerima notifikasi per config
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    'category': 'Technical',
    'version': '18.0.0.1',
    'license': 'LGPL-3',

    'depends': [
        'tw_monitoring_mft',
        'tw_telegram',
    ],

    'data': [
        'views/tw_mft_config_telegram_views.xml',
        'data/scheduled_actions.xml',
    ],

    'installable': True,
    'application': False,
}
