# -*- coding: utf-8 -*-
{
    'name': 'TW QRIS Display (Real-Time)',
    'version': '18.0.1.0.0',
    'summary': 'QRIS Display (Real-Time)',
    'description': """
        QRIS Display (Real-Time)
""",
    'category': 'Accounting/Payment',
    'email': 'hondakita.md@gmail.com',
    'author': '2W',
    'website': 'https://honda-ku.com',
    'depends': ['web','bus','tw_payment_approval'],
    'data': [
        "security/res_groups.xml",
        "views/tw_qris_screen_view.xml",
        ],
    'assets': {
        "web.assets_backend": [
            "tw_qris_display/static/src/js/qris_screen_client.js",
            "tw_qris_display/static/src/xml/qris_screen_template.xml",
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
