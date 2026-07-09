# -*- coding: utf-8 -*-
{
    'name': "Utilisasi DGI TDM Retail Report",
    'summary': "Consolidated report for DGI Integration (Unit, Part, Service, Document Handling)",
    'description': """
        Report module to monitor the utilization of DGI Integration.
        This module consolidates data from various DGI sub-modules:
        - Unit Inbound
        - Part Inbound
        - Service (Work Order)
        - Document Handling (STNK/BPKB)
        - Prospect & Sales (SPK)
    """,
    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",
    'category': 'API Integration',
    'version': '18.0.0.0',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
        'tw_dgi',
        'tw_dgi_inbound',
        'tw_dgi_lead',
        'tw_dgi_spk',
        'tw_dgi_bast',
        'tw_dgi_document_handling',
        'tw_dgi_work_order',
        'tw_dgi_account',
        'tw_dealer_sale_order',
        'tw_work_order',
        'tw_purchase_order',
        'tw_vehicle_registration_process',
        'tw_vehicle_document_receipt',
        'tw_vehicle_document_handover',
        'web_report',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'views/tw_dgi_report_view.xml',
        'views/tw_menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
