# -*- coding: utf-8 -*-
{
    'name': "TW Vehicle Document Stock Opname",
    'version': '1.0.0',
    'summary': "Vehicle Document Stock Opname (STNK/BPKB)",

    'description': """
Long description of module's purpose
    """,

    'author': "Tunas Honda",
    'company': 'PT. Tunas Dwipa Matra',
    'website': 'https://www.honda-ku.com',

    'category': 'Uncategorized',

    'depends': [
        'base',
        'tw_base',
        'tw_attachment', 
        'tw_vehicle_document', 
        'tw_selection', 
        'tw_pilot_project',
        'tw_stock_document'
    ],

    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir_rule.xml',

        'data/tw_vehicle_document_selection.xml',

        'views/tw_vehicle_document_stock_opname_view.xml',
        'views/tw_vehicle_document_selection_view.xml',
        'views/tw_menu.xml',

        'reports/tw_stock_opname_report.xml',
        'reports/tw_stock_opname_bpkb_print_bakso_view.xml',
        'reports/tw_stock_opname_stnk_print_bakso_view.xml',
        'reports/tw_stock_opname_bpkb_print_validasi_view.xml',
        'reports/tw_stock_opname_stnk_print_validasi_view.xml',

        'wizards/tw_vehicle_document_bakso_ownership_view.xml',
        'wizards/tw_vehicle_document_bakso_registration_view.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
