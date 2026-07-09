# -*- coding: utf-8 -*-
{
    'name': 'TW DGI Document Handling',
    'version': '1.0.0',
    'category': 'Document Handling',
    'summary': 'DGI API Integration for Vehicle Document Handling',
    'description': """
        Integration module untuk sync data document handling dari DGI API
        - Proses STNK
        - Penerimaan STNK/BPKB
        - Penyerahan STNK/BPKB
    """,
    'author': 'Tunas Honda',
    'website': 'https://www.honda-ku.com',
    'license': 'LGPL-3',
    
    'depends': [
        'base',
        'base_suspend_security',
        'tw_branch',
        'tw_branch_setting',
        'tw_dgi',
        'tw_vehicle_registration_process',
        'tw_vehicle_document_handover',
        'tw_vehicle_document_receipt',
        'tw_vehicle_document',
        'tw_stock',
        'tw_api',
        'rest_api',
    ],
    
    
    'data': [
        'security/ir_rule.xml',
        'security/res_groups_button.xml',
        'security/ir.model.access.csv',

        'data/tw_endpoint_dgi_document_handling_data.xml',
        'data/tw_mapping_dgi_document_handling_data.xml',

        'wizards/tw_dgi_proses_stnk_wizard_mixin_view.xml',
        'wizards/tw_dgi_handover_stnk_wizard_mixin_view.xml',
        'wizards/tw_dgi_receipt_stnk_wizard_mixin_view.xml',
        'wizards/tw_dgi_handover_bpkb_wizard_mixin_view.xml',
        'wizards/tw_dgi_receipt_bpkb_wizard_mixin_view.xml',

        'views/tw_vehicle_registration_process_view.xml',
        'views/tw_vehicle_registration_receipt_inherit_view.xml',
        'views/tw_vehicle_registration_handover_inherit_view.xml',
        'views/tw_vehicle_ownership_handover_inherit_view.xml',
        'views/tw_vehicle_ownership_receipt_inherit_view.xml',
    ],
    
    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',
}
