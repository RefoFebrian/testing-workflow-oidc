# -*- coding: utf-8 -*-
{
    'name': 'TW File Dropzone Widget',
    'summary': 'Reusable drag and drop file widgets for Odoo forms',
    'description': """
Shared frontend widgets for file upload fields, including single binary
dropzone support and multi-file attachment dropzone support.
    """,
    'author': 'Tunas Dwipa Matra',
    'website': 'https://www.tunasgroup.com',
    'category': 'TW',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['web'],
    'assets': {
        'web.assets_backend': [
            'tw_file_dropzone_widget/static/src/components/file_dropzone/file_dropzone_field.xml',
            'tw_file_dropzone_widget/static/src/components/file_dropzone/file_dropzone_field.scss',
            'tw_file_dropzone_widget/static/src/components/file_dropzone/file_dropzone_field.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
