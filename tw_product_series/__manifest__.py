{
    'name': 'TW Product Series',
    'version': '1.0',
    'category': 'Product',
    'summary': 'Manage Product Series for Products',
    'description': """
        This module adds product series functionality to manage product variants.
    """,
    'depends': ['base','product','tw_product'],
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'views/product_series_views.xml',
        'views/product_template_views.xml',
        'views/product_product_views.xml',
        'views/tw_menu.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
