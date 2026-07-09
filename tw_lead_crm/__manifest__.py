{
    'name': "TW Lead CRM",

    'summary': "Module of Leads CRM",

    'description': """
        Module of Leads CRM
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Sales / TW Sales',
    'version': '0.1',
    'license': "LGPL-3",

    # any module necessary for this one to work correctly
    'depends': ['tw_base', 'tw_lead', 'tw_lead_activity'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        
        'views/tw_lead_crm_matrix_assignment_view.xml',
        'views/tw_lead_crm_view.xml',
        'report/tw_lead_crm_report_view.xml',
        'views/tw_menu_view.xml',
    ],
}

