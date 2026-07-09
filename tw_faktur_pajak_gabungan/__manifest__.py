# -*- coding: utf-8 -*-
{
    'name': "TW Faktur Pajak Gabungan",

    'summary': "TW Faktur Pajak Gabungan",

    'description': """
TW Faktur Pajak Gabungan
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_faktur_pajak'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir_rule.xml',

        'report/tw_faktur_pajak_gabungan_report.xml',

        'wizard/tw_generate_faktur_pajak_wizard_view.xml',

        'views/tw_faktur_pajak_gabungan_view.xml',
        'views/tw_master_model_pajak_view.xml',
        'views/tw_menu.xml',
    ],
}

