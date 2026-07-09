# -*- coding: utf-8 -*-
{
    'name': "TW Faktur Pajak Core TAX",

    'summary': "Generate E-Faktur Pajak Core TAX",

    'description': """
Generate E-Faktur Pajak Core TAX
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.2',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'tw_base',
        'tw_faktur_pajak',
        'tw_faktur_pajak_report',
        'tw_product',
        'web_report',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'data/ir_config_parameter.xml',

        'views/tw_faktur_pajak_out_view.xml',
        'views/res_config_settings_views.xml',
        'views/tw_report_faktur_pajak_wizard_inherit.xml',

        'report/tw_e_faktur_pajak_core_tax_wizard_view.xml',
    ]
}
