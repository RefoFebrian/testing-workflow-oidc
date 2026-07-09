# -*- coding: utf-8 -*-
{
    'name': "TW Base",

    'summary': "Custom Base. All module of custom will depends in this module",

    'description': """
        Custom Base. All module of custom will depends in this module
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Tools / TW Tools',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'web',
        'web_report',
        'tw_web',
        'mandatory_field_highlight',
        'web_special_character',
    ],
    # always loaded
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'data/ir_configparameter_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'tw_base/static/src/js/inherit_error_dialogs.js',
            'tw_base/static/src/js/form_controller_patch.js',
            'tw_base/static/src/scss/discount_listview.scss',
            'tw_base/static/src/scss/fields.scss',
            'tw_base/static/src/scss/form_status_indicator.scss',
            'tw_base/static/src/views/form_status_indicator.xml',
        ],
    },

}

