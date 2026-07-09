# -*- coding: utf-8 -*-
{
    'name': "TW API Log Partition",

    'summary': "PostgreSQL table partitioning for API Log Detail",

    'description': """
        Enables monthly range partitioning on tw_api_log_detail (by create_date).
        - Instant retention cleanup via DETACH PARTITION + DROP (no row-level DELETE)
        - Auto-creates future monthly partitions via cron
        - Admin UI to view partition status and manage retention
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",
    'license': 'LGPL-3',

    'category': 'TW Tools / TW Tools',
    'version': '18.0.1.0.0',

    'depends': ['tw_api'],

    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'views/tw_menu.xml',
        'views/tw_api_log_partition_view.xml',
    ],

    'post_init_hook': '_post_init_hook',

    'application': False,
    'installable': True,
}
