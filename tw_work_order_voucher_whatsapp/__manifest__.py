# -*- coding: utf-8 -*-
{
    'name': "TW Work Order Voucher Whatsapp",

    'summary': "TW Work Order Voucher Whatsapp",

    'description': """
        TW Work Order Voucher Whatsapp
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'tw_work_order',
        'tw_work_order_approval',
        'tw_work_order_voucher',
        'tw_sales_voucher',
        'tw_whatsapp_api',
        'tw_selection'
    ],

    # always loaded
    'data': [
        'data/tw_whatsapp_content_template_type.xml',
        'data/tw_whatsapp_content_template.xml',
        
        'security/ir.model.access.csv',

        'views/tw_work_order_inherit_view.xml',
        'views/tw_work_order_confirm_voucher.xml',
    ],
}

