{
    'name': "TW Area HR",

    'summary': "Employee with Area",

    'description': """
        Module Employee with Area
    """,

    'author': "Tunas Honda",
    'license': "LGPL-3",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Back Office / TW Back Office',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_area','tw_hr'],

    # always loaded
    'data': [
        'views/tw_area_employee_inherit_view.xml',
    ],
}

