# -*- coding: utf-8 -*-
{
    "name": "TW SPK BBN",
    "summary": "Connect SPK with BBN",
    "description": """
        This module is used to manage Extended process SPK from BBN.
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
        "tw_spk",
        "tw_pricelist_bbn",
    ],
    # always loaded
    "data": [
        
    ]
}
