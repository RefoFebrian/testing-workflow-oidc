# -*- coding: utf-8 -*-
{
    'name': 'Web Login Captcha',
    'version': '1.0',
    'summary': 'Add Google reCAPTCHA to Backend Login',
    'category': 'Website',
    'author': 'NAG',
    'depends': ['web', 'google_recaptcha'],
    'data': [
        'views/login_templates.xml',
        'views/res_config_settings_view.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'web_login_captcha/static/src/js/login_captcha.js',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
