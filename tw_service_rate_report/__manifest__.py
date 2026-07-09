{
    'name': "TW Service Rate Report",

    'summary': "Module of Service Rate Report",

    'description': """
        Module of Service Rate Report
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Report / TW Service',
    'version': '0.1',
    'license': "LGPL-3",
    'application': False,

    # any module necessary for this one to work correctly
    'depends': ['base', 'tw_base','tw_menu'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        
        'views/tw_service_rate_report_view.xml',
        'views/tw_menu.xml',
    ],

}