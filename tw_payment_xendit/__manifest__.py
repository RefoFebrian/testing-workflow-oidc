# -*- coding: utf-8 -*-
{
    'name': 'TW Payment Xendit',
    'version': '18.0.1.0.0',
    'summary': 'Payment Integration to Xendit',
    'description': """
        Integrates payment processing with Odoo Invoices using Xendit.
    """,
    'category': 'Accounting/Payment',
    'email': 'hondakita.md@gmail.com',
    'author': '2W',
    'website': 'https://honda-ku.com',
    'depends': ['account','tw_account','tw_payment', 'payment', 'payment_xendit'],
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups_button.xml',
        'views/tw_account_payment_views.xml',
        'views/tw_payment_transaction_views.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
