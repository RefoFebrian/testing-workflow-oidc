# -*- coding: utf-8 -*-
{
    'name': "TW dgi mapping master jasa",

    'summary': "Master data untuk mapping jasa per main dealer dan cabang",

    'description': """
        Master Mapping Jasa
        ===================
        Modul ini menyediakan master data untuk memetakan produk jasa terhadap main dealer dan cabang tertentu.

        **Desain Data:**
        - **Header:**
        - Main Dealer (`res.partner`) - Mandatory
        - Branch (`res.company`) - Optional
        - Active (`Boolean`)

        - **Line:**
        - Product Jasa (`product.product` dengan kategori jasa) - Mandatory
        - Product MD (`Char`) - Mandatory
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_branch','tw_product','tw_partner','tw_menu'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir_rule.xml',
        'views/tw_dgi_mapping_master_jasa_view.xml',
        'views/tw_dgi_mapping_master_jasa_upload_view.xml',
        'views/tw_dgi_mapping_master_jasa_upload_result_view.xml',
        'views/tw_menu.xml',
    ],
    'installable': True,
    'application': False,
}

