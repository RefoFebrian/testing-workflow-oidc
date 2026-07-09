# -*- coding: utf-8 -*-
{
    'name': "TW Activity ATL/BTL Sales",

    'summary': "Module activity ATL/BTL yang merupakan tempat pengambilan/monitoring data dari Sales seperti SPK dan DSO",

    'description': """
        TW Activity ATL/BTL Sales
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'tw_base', 'tw_activity_atl_btl', 'tw_activity_sales'],

    # always loaded
    'data': [
        'views/tw_activity_atl_btl_sales_inherit_view.xml',
    ],
    'external_dependencies': {
    }

}
