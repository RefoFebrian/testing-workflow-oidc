# -*- coding: utf-8 -*-
{
    'name': "TW NRFS",

    'summary': "NRFS For Product",

    'description': """
        NRFS For Product
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
        'stock',
        'product',
        'account',
        'hr',
        'base_suspend_security',
        'tw_menu',
        'tw_base',
        'tw_selection',
        'tw_config_files',
        'tw_localization',
        'tw_product',
        'tw_branch',
    ],

    # always loaded
    'data': [
        "data/tw_nrfs_master_gejala_data.xml",
        "data/tw_nrfs_master_penyebab_data.xml",
        "data/tw_nrfs_master_penanganan_unit_data.xml",
        "data/tw_nrfs_cron.xml",
        "data/tw_po_urgent_sequence.xml",
        "data/tw_nrfs_partner_lkuas_data.xml",
        
        "security/ir.model.access.csv",
        'security/ir_rule.xml',
        "security/res_groups.xml",
        "security/res_groups_button.xml",
        
        "views/tw_nrfs_view.xml",
        "views/tw_nrfs_vendor_view.xml",
        "views/tw_po_urgent_view.xml",
        "views/tw_master_gejala_view.xml",
        "views/tw_master_penyebab_view.xml",
        "views/tw_master_penanganan_unit_md_view.xml",
        "views/tw_master_penanganan_unit_vendor_view.xml",
        "views/tw_menu.xml"
    ],
    'installable': True,
    'application': True,
}

