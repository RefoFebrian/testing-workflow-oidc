{
    'name': "TW MFT File STO",

    'summary': "MFT File STO",

    'description': """
        Generate STO file data for send to AHM
    """,

    'license': 'LGPL-3',
    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'tw_base',
        'tw_menu',
        'tw_config_files',
        'tw_api',
        'tw_stock',
        'tw_branch',
        'tw_partner',
        'tw_product',
        'tw_purchase_order',
        'tw_monitoring_mft'
    ],

    # always loaded
    'data': [
        'data/tw_cron_data.xml',

        'security/ir.model.access.csv',
        'security/res_groups.xml',
        
        'views/tw_export_mft_file_sto_view.xml',
        'views/tw_menu_view.xml',
    ],
}
