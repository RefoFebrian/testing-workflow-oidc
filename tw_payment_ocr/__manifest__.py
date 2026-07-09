{
    'name': 'TW Payment OCR',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Localizations',
    'summary': 'OCR for Customer Payment using Google Cloud Document AI',
    'description': """
This module provides an OCR feature for Customer Payments in the tw_payment module.
It utilizes Google Cloud Document AI to extract data from uploaded files (PDF/Images)
and creates draft Customer Payment records.
    """,
    'author': 'Tunas Dwipa Matra',
    'website': 'https://www.tunasgroup.com',
    'depends': [
        'base',
        'account',
        'tw_payment',
        'tw_file_dropzone_widget',
    ],
    'external_dependencies': {
        'python': ['google-cloud-documentai'],
    },
    'data': [
        'security/ir.model.access.csv',
        'security/res_button_groups.xml',
        'data/ir_config_parameter_data.xml',
        'views/tw_payment_ocr_wizard_view.xml',
        'views/tw_customer_payment_list_inherit.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
