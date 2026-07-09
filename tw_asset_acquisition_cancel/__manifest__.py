{
    'name': "TW Asset Acquisition Cancel",

    'summary': "Module to manage cancellation of Asset Acquisition.",

    'description': """
        This module provides functionality to cancel Asset Acquisition with approval workflow.
        Key features include:
            - Cancel Asset Acquisition with approval process
            - Validation to ensure Asset of Acquisition still not depreciation
            - Audit trail for cancellation process
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Back Office / TW Back Office',
    'version': '0.1',
    'license': "LGPL-3",

    # any module necessary for this one to work correctly
    'depends': [
        'tw_base',
        'tw_asset_management',
        'tw_cancellation',
        'tw_approval'
    ],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir.model.access.csv',

        'views/tw_asset_acquisition_cancel_view.xml',
        'views/tw_menu.xml',
    ],
}