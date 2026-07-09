{
    'name': 'TW Upload Payment Request',
    'version': '1.0',
    'description': 'Upload line of payment request',
    'summary': 'Upload line of payment request',
    'sequence': '1',
    'category': 'TDM',
    'author': 'NAG',
    'email': 'hondakita.md@gmail.com',
    'depends': [
        'tw_branch',
        'tw_menu',
        'tw_account',
        'tw_payment_request',
        'tw_format_upload',
    ],
    'data': [
        'security/res_groups_button.xml',

        'views/tw_upload_payment_request_views.xml',
        'views/tw_payment_request_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
