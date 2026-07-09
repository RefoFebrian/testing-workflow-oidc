# -*- coding: utf-8 -*-
{
    'name': "TW DGI BAST",

    'summary': "DGI Integration - BAST (Batch Transfer Out / Surat Jalan)",

    'description': """
        DGI Integration module for syncing BAST (Berita Acara Serah Terima) data
        from Main Dealer. Used to process batch delivery (packing) from
        Dealer Sale Order transactions for Unit division.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",
    'category': 'TW Sale / TW Sale',
    'version': '18.0.1.0.0',
    'license': 'AGPL-3',

    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',

    'depends': [
        'tw_dgi',
        'tw_dgi_spk',
        'tw_dealer_sale_order',
        'stock_picking_batch',
        'tw_stock',
    ],

    'data': [
        'security/res_groups_button.xml',
        'security/ir.model.access.csv',
        'data/tw_endpoint_dgi_bast_data.xml',
        'data/tw_mapping_dgi_bast_data.xml',
        'wizards/tw_dgi_bast_wizard_view.xml',
        'views/tw_stock_picking_batch_inherit_view.xml',
    ],
}
