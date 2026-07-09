{
    'name': "TW Sales Program",

    'summary': "Module of Sales Program",

    'description': """
        Module of Sales Program
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Sales / TW Sales',
    'version': '0.1',
    'license': "LGPL-3",

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'tw_base',
        'tw_area',
        'tw_menu',
        'tw_selection',
        'tw_format_upload'
    ],

    # always loaded
    'data': [
        "data/tw_sales_program_data.xml",

        'security/ir.model.access.csv',
        'security/res_groups.xml',
        
        'views/tw_sales_program_view.xml',
        'views/tw_sales_program_line_view.xml',
        'views/tw_selection_master_sales_program_view.xml',
        'views/tw_menu_view.xml',
        'security/ir_rule.xml',
    ],
}