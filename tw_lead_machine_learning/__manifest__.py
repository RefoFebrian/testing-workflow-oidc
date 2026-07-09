{
    'name': "TW Lead Machine Learning",

    'summary': "Module of Leads Machine Learning",

    'description': """
        Module of Leads Machine Learning
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
    'depends': [
        'tw_base',
        'tw_api',
        'tw_work_order',
        'tw_dealer_sale_order_program',
        'tw_firebase',
        'tw_activity_sales',
        'tw_sp_digital',
        'tw_lead_crm'
    ],

    # always loaded
    'data': [
        'data/tw_cron_data.xml',
        'data/tw_firebase_content_template_data.xml',
        'data/tw_firebase_notification_category_data.xml',
        
        'views/tw_api_configuration_inherit_view.xml',
    ],
}