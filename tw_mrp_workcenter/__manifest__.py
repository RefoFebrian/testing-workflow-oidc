{
    'name': 'TW MRP Work Center',
    'version': '1.0',
    'category': 'Manufacturing',
    'summary': 'Add cost calculation type to work centers',
    'description': """
        This module adds a cost calculation type to work centers, allowing
        cost calculation based on either time spent or work order quantity.
    """,
    'depends': ['mrp'],
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'views/mrp_workcenter_views.xml',
        'views/tw_menu.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
