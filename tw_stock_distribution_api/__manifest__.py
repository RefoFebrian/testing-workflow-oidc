{
    'name': 'TW Stock Distribution API',
    'version': '18.0.1.0.0',
    'category': 'Inventory',
    'summary': 'API for Stock Distribution Management',
    'description': """
        This module provides REST API endpoints for managing stock distribution
        operations.
    """,
    'author': 'Tunas Honda',
    'website': 'https://www.honda-ku.com',
    'depends': [
        'base',
        'stock',
        'web',
        'rest_api',
        'tw_api',
        'tw_stock_distribution',
    ],

    'data': [
        'data/tw_cron_data.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
