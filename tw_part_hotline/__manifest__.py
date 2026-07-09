{
    "name": "TW Part Hotline",
    'summary': "TW Part Hotline",

    'description': """
TW Part Hotline
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",
    "version": "1.0",
    "license": "AGPL-3",
    'category': 'Uncategorized',
    'depends': [
        'base',
        'tw_base',
        'mail',
        'product',
        'stock',
        'sale',
        'purchase',
        'account',
        'tw_branch',
        'tw_branch_setting',
        'tw_consolidate_invoice',
        'tw_purchase_order_pricelist',
        'tw_work_order',
        'tw_work_order_approval',
        'tw_part_sales',
        'tw_part_sales_approval',
        'tw_menu'
    ],
    'data': [
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        
        'report/tw_part_hotline_print.xml',
        'views/tw_part_hotline_view.xml',
        'views/tw_purchase_order_view.xml',
        'views/tw_work_order_view.xml',
        'views/tw_part_sales_view.xml',
        'views/tw_branch_setting_inherit_view.xml',
        'views/tw_stock_warehouse_inherit_view.xml',
        'views/tw_stock_picking_inherit_view.xml',
        'report/tw_part_hotline_monitoring_view.xml',
        'report/tw_laporan_part_hotline.xml',
        # 'report/tw_part_hotline_cancel_print.xml',
        
        'views/tw_menu_view.xml',

        'data/master_data_po_type.xml'
    ],
    'installable': True,
    'application': True,
}