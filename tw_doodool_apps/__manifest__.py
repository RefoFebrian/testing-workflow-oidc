# -*- coding: utf-8 -*-
{
    'name': "TW Doodoo Apps",

    'summary': "Backend and API's for Doodool Apps",

    'description': """
        This module provides the backend infrastructure and API integrations for the Doodool Apps. 
        It is designed to facilitate seamless communication between the frontend applications and 
        the backend systems, ensuring a smooth user experience. 

        Key features of this module include:
        - API endpoints for managing user data, transactions, and other app functionalities.
        - Backend logic to handle business processes and workflows.
        - Integration with external services and systems as required.
        - Configurable views and templates for administrative purposes.

        This module is ideal for developers and administrators who need a robust backend solution 
        for managing the Doodool Apps ecosystem.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",
    "license": "LGPL-3",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'tw_base', 'tw_api', 'rest_api', 'tw_lead', 'tw_lead_activity','tw_activity_sales'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/tw_crm_lead_inherit_view.xml',
        'views/tw_res_company_inherit_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

