{
    'name': 'TW Sale Order Discount',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Dynamic discount management for sale orders',
    'description': """
        This module allows adding multiple dynamic discounts to sale orders
        with different types and amounts based on tw.account.discount.
        Only shows out_receipt type discounts from the discount master.
    """,
    'author': 'Tunas Honda',
    'website': 'https://www.honda-ku.com',
    'depends': [
        'base',
        'tw_account_discount',
        'tw_sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'views/tw_sale_order_views.xml',
        'report/tw_sale_order_report_template_inherit.xml',
        'views/tw_sale_discount_items_view.xml',
        'views/tw_sale_discount_cash_view.xml',
        'views/tw_sale_discount_upload_view.xml',
        'views/tw_master_ahass_top_view.xml',

        'views/tw_menu.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
