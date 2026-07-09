{
    'name': 'TW Purchase Returns Approval',
    'version': '1.0',
    'category': 'Inventory/Purchase',
    'summary': 'Approval workflow for purchase returns',
    'description': """
        This module adds an approval workflow for purchase returns.
        It allows you to set up approval rules based on amount, department, etc.
    """,
    'depends': [
        'base',
        'tw_base',
        'tw_purchase_return',
        'tw_approval',
    ],
    'data': [
        'security/res_groups_button.xml',
        'security/ir.model.access.csv',
        'views/tw_purchase_return_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
