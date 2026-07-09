# -*- coding: utf-8 -*-

{
    'name': 'TW Attachment',
    'version': '18.0.1.0.0',
    'category': 'Tools',
    'summary': 'Advanced attachment management with custom storage locations',
    'description': """
        This module provides advanced attachment management
        with custom storage locations based on tw.config.files.
        if need to convert to url : '/web/content/tw.attachment/[id_attachment]/datas'
    """,

    'author': 'Tunas Honda',
    'website': 'https://www.honda-ku.com',
    'depends': ['base', 'tw_config_files'],
    'data': [
        'security/ir.model.access.csv',

        'views/tw_attachment_view.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'tw_attachment/static/src/xml/pdf_url_viewer.xml',
            'tw_attachment/static/src/js/pdf_url_viewer.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': True,
    'license': 'LGPL-3',
}