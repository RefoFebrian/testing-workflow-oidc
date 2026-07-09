# -*- coding: utf-8 -*-
{
    'name': "TW Koprol",

    'summary': "Koprol Integration to TEDS 2.0",

    'description': """
        Koprol Integration to TEDS 2.0
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
                'tw_api',
                'tw_asset_management',
                'tw_asset_disposal',
                'tw_asset_mutation',
                'tw_branch',
                ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'data/tw_api_configuration_type_data.xml',
        'data/tw_endpoint_configuration_data.xml',
        
        'views/tw_product_template_view.xml',
        'views/inherit_hr_employee_view.xml',
        'views/inherit_res_company_view.xml',
        'views/inherit_tw_api_configuration_view.xml',
        'views/inherit_tw_mutation_asset_view.xml',
        'views/inherit_res_partner_view.xml',
        'views/inherit_purchase_order_view.xml',
        'views/inherit_tw_disposal_asset_view.xml',

        'wizard/tw_api_koprol_wizard_view.xml',
        'wizard/tw_menu.xml',
    ],
}

