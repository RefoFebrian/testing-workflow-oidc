# -*- coding: utf-8 -*-
{
    'name': 'TW Vehicle Document Approval',
    'version': '1.0.0',
    'category': 'Document Management',
    'summary': 'Approval workflow for vehicle document management',
    'description': """
        This module extends the vehicle document management with an approval workflow,
        allowing document requests to go through an approval process before being confirmed.
    """,
    'author': 'Tunas Honda',
    'website': 'https://www.honda-ku.com',
    'license': 'LGPL-3',
    
    # Dependencies
    'depends': [
        'base',
        'tw_vehicle_document',
        'tw_approval'
    ],
    
    # Always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups_button.xml',
        'views/tw_vehicle_document_approval.xml',
    ],
    
    # Auto-install
    'auto_install': True,
    'installable': True,
    'application': True,
}
