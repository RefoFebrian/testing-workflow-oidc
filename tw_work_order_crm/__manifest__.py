# -*- coding: utf-8 -*-
{
    'name': "TW Work Order CRM",

    'summary': "TW Work Order CRM",

    'description': """
TW Work Order CRM
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
    'depends': [
        'base',
        'tw_base',
        'tw_selection',
        'tw_work_order'
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/res_groups.xml',
        'views/tw_selection_hubungan_dengan_pemilik_view.xml',
        'views/tw_selection_alasan_ke_ahass_view.xml',
        'views/tw_work_order_inherit_view.xml',
        'data/reason_to_ahass.xml',
        'data/relationship_with_the_owner.xml',
        
        'views/tw_menu.xml',
    ],
}

