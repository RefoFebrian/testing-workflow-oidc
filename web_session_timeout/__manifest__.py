{
    'name': 'Web Session Timeout',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Auto logout inactive users',
    'description': """
        Auto logout users after a configurable period of inactivity.
        Handles multiple tabs via localStorage.
    """,
    'depends': ['web'],
    'data': [
        'data/data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'web_session_timeout/static/src/js/session_timeout.js',
        ],
    },
    'installable': True,
    'license': 'LGPL-3',
}
