{
    'name': 'TW Vehicle Document Mutation',
    'version': '1.1.0',
    'category': 'Operations/Documents',
    'summary': 'Handle mutation of document locations for STNK and BPKB',
    'description': """
        This module handles the mutation of document locations for STNK and BPKB documents.
        It allows tracking the movement of documents between different locations.
        
        Features:
        - Internal mutation (within same branch)
        - Inter-branch mutation with outgoing/incoming flow
        - Stock document integration
    """,
    'author': 'Tunas Honda',
    'website': 'https://www.honda-ku.com',
    'depends': [
        'base',
        'stock',
        'tw_web',
        'tw_stock',
        'tw_vehicle_document',
        'tw_vehicle_document_location',
        'tw_vehicle_document_receipt',
    ],
    'data': [
        'report/tw_document_mutation_registration_view.xml',
        'report/tw_document_mutation_ownership_view.xml',
        'report/tw_document_mutation_ownership_request_report_template.xml',
        'report/tw_vehicle_document_mutation_report.xml',

        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir.model.access.csv',
        'security/ir_rules.xml',

        'views/tw_document_mutation_views.xml',
        'views/tw_document_mutation_outgoing_views.xml',
        'views/tw_document_mutation_incoming_views.xml',
        'views/tw_vehicle_request_bpkb_views.xml',
        'views/tw_request_document_wizard.xml',
        'views/tw_menu.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

