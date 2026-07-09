# -*- coding: utf-8 -*-
{
    'name': 'Web DateTime Picker Today',
    'version': '18.0.1.0.0',
    'category': 'Web',
    'summary': 'Add a "Today" button to date and datetime picker widget',
    'description': """
        Adds a "Today" button to the bottom of the date/datetime picker.
    """,
    'depends': ['web'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'web_datetime_picker_today/static/src/core/datetime/datetime_picker.js',
            'web_datetime_picker_today/static/src/core/datetime/datetime_picker.xml',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
