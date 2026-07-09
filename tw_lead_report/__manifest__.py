{
    'name': 'TW Lead Summary Report',
    'version': '1.0',
    'summary': 'Lead Summary Report by Salesperson',
    'description': '''
        This module provides an Excel report of leads summary per salesperson within a date range.
    ''',
    'category': 'Sales/CRM',
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': [
        'base',
        'crm',
        'tw_lead',
        'web',
        'tw_base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'wizards/lead_summary_report_views.xml',
        'wizards/lead_detailed_report_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
