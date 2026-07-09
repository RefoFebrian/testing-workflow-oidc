# -*- coding: utf-8 -*-
{
    'name': "TW Vehicle Document Handover",
    'summary': "Management of Vehicle Document Handover (STNK & BPKB)",
    'description': """
        This module handles the management of vehicle document handovers including:
        - STNK (Surat Tanda Nomor Kendaraan) handover process
        - BPKB (Buku Pemilik Kendaraan Bermotor) handover process
        - Multi-company support
        - User access control and security
    """,
    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",
    'category': 'Document Handling',
    'version': '1.0.0',
    'depends': [
        'base',
        'tw_base',
        'stock',
        'tw_vehicle_document',
        'tw_birojasa_billing_process',
        'tw_web'
    ],
    'data': [
        # Report
        'report/tw_vehicle_registration_handover_view.xml',
        'report/tw_vehicle_ownership_handover_view.xml',
        'report/tw_vehicle_ownership_handover_company_view.xml',
        'report/tw_vehicle_document_handover_report.xml',

        # Security
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir_rule.xml',

        # Views
        'views/tw_vehicle_ownership_handover_view.xml',
        'views/tw_vehicle_registration_handover_view.xml',
        'views/tw_stock_lot_inherit_view.xml',

        # Menus
        'views/tw_menu.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}