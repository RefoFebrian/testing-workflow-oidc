# -*- coding: utf-8 -*-
{
    'name': "TW NRFS Report",

    'summary': "NRFS Report",

    'description': """
        NRFS Report
    """,

    'license':'LGPL-3',
    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'base_suspend_security',
        'tw_base',
        'tw_menu',
        'web_report',
        'tw_nrfs',
        'tw_nrfs_sparepart',
        'tw_stock',
        'tw_product',
        'tw_stock_inbound',
        'tw_vehicle',
        'tw_partner',
        'tw_selection',
        ],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'views/tw_nrfs_lkuat_report_view.xml',
        'views/tw_nrfs_po_urgent_report_view.xml',
        'views/tw_nrfs_sparepart_report_view.xml',
        # TODO: Nyalakan ketika sudah ada modul report google drive
        # 'views/tw_nrfs_google_drive_report_view.xml',
        'views/tw_menu_view.xml',
    ],
    'installable': True,
    'application': True,
}

