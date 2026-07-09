# -*- coding: utf-8 -*-
{
    "name": "TW Leads BBN",
    "summary": "Connect Leads with BBN",
    "description": """
        This module is used to manage Extended process Lead from BBN.
    """,
    "author": "TDM",
    "license": "LGPL-3",
    "website": "https://www.honda-ku.com",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "TW Sales / TW Sales",
    "version": "0.1",
    # any module necessary for this one to work correctly
    "depends": [
        "base", 
        "tw_lead",
        "tw_pricelist_bbn",
    ],
    # always loaded
    "data": [
        
    ]
}

    # NOTE:
    # these codes are copy and adjustment from tunashonda
    # but odoo officals already has crm.lead models that can be used
    # and utilised in the new teds 2.0
    
    # 'security/ir.model.access.csv',
    # 'security/ir_rule.xml',
    # 'views/tw_lead_view.xml',

