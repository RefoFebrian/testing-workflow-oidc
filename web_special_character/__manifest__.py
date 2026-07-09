# -*- coding: utf-8 -*-
{
    'name': "Web Special Character Filter",

    'summary': """
        Custom widget untuk memfilter karakter spesial pada field char
        """,

    'description': """
        Widget field untuk menolak karakter spesial secara default.
        
        Features:
        - Memblokir input karakter spesial secara real-time
        - Support Unicode characters (untuk bahasa Indonesia)
        - Hanya allow: huruf, angka, spasi, dash (-), dan underscore (_)
        - Mendukung paste dengan auto-filter
        - Dapat di-configure dengan options untuk allow special characters
        
        Usage:
        <field name="field_name" widget="no_special_char"/>
        
        Options:
        - allow_special_char: true/false (default: false)
        - pattern: custom regex pattern (opsional)
        - normalize: normalize Unicode (default: true)
    """,

    'author': "Tunas Honda",
    'website': "",
    'license': 'LGPL-3',
    'category': 'Technical',
    'version': '18.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web'],

    'assets': {
        'web.assets_backend': [
            'web_special_character/static/src/js/no_special_char_field.js',
        ],
    },

    'installable': True,
    'application': False,
}