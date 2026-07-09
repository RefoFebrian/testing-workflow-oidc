{
    'name': "TW Sales Program Product",

    'summary': "Module of Sales Program using Product",

    'description': """
        Module of Sales Program using Product
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
    'depends': ['base', 'tw_sales_program', 'tw_product'],

    # always loaded
    'data': [
        'views/tw_sales_program_inherit_view.xml',
        'views/tw_sales_program_line_inherit_view.xml'
    ],
}