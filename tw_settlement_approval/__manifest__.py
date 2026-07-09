# -*- coding: utf-8 -*-
{
    'name': "TW Settlement Approval",

    'summary': """
    This module adds the approval workflow on the settlement process. 
    """,

    'description': """
    This module adds the approval workflow on the settlement process. The approval
    workflow will be used to ensure that the settlement is properly reviewed and
    authorized before being processed. The approval process can be customized to
    fit the organization's requirements.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_base','tw_settlement','tw_approval'],

    # always loaded
    'data': [
        'security/res_groups_button.xml',
        
        'views/tw_settlement_view.xml',
    ],
}

