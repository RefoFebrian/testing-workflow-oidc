{
    'name': 'TW HR Auth Signup',

    'summary': 'Allow users of employee to reset their password with link',

    'description': """
        Allow users of employee to reset their password with link
    """,

    'author': "Tunas Honda",
    'license': "LGPL-3",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW HR / TW HR',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'auth_signup', 'tw_hr'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'data/ir_config_parameter_data.xml',

        'views/tw_res_users_inherit_view.xml',
        'views/tw_reset_password_templates_email.xml',
    ],
}