# -*- coding: utf-8 -*-
{
    'name': "TW Cron Log",

    'summary': "Log error dari scheduled actions (cron) dengan pencegahan duplikasi.",

    'description': """
        Module untuk mencatat log error dari scheduled actions (cron).
        
        Fitur:
        - Menangkap dan mencatat error saat cron dijalankan
        - Mencatat detail error termasuk traceback
        - Pencegahan duplikasi log berdasarkan delay waktu (configurable via System Parameter)
        - Relasi ke cron job untuk tracking
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    'category': 'Technical',
    'version': '18.0.0.1',
    'license': 'AGPL-3',

    'depends': [
        'base',
    ],
    
    'data': [
        'data/tw_system_parameter.xml',
        
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'views/tw_cron_log_views.xml',
        'views/tw_menu.xml',
    ],
}
