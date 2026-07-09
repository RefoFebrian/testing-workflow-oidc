{
    'name': "TW Ring",

    'summary': "Module of Master Ring",

    'description': """
        Module of Master Ring
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Back Office / TW Back Office',
    'version': '0.1',
    'license': "LGPL-3",

    # any module necessary for this one to work correctly
    'depends': ['base', 'tw_base', 'tw_menu'],

    # always loaded
    'data': [
        'data/tw_master_ring_data.xml',
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'views/tw_ring_view.xml',
        'views/tw_ring_kecamatan_view.xml',
        'views/tw_menu_view.xml',
    ],
}

