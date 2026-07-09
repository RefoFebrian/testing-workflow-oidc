# -*- coding: utf-8 -*-
{
    'name': "TW Other Receivable Approval",

    'summary': "Adds an approval workflow to the TW Other Receivable module for submitting and tracking payment requests.",

    'description': """
This module adds an approval workflow to the TW Other Receivable module. It allows users to submit other receivable requests for approval and track the status of these requests. The approval process can be customized to fit the organization's requirements, ensuring that all other receivable transactions are properly reviewed and authorized before being processed.
    """,

    'author': "Tunas Honda",
    'license': "LGPL-3",
    'website': "https://www.honda-ku.com",

    'category': 'TW Tools / TW Tools',
    'version': '0.1',

    'depends': ['base', 'tw_base', 'tw_other_receivable', 'tw_approval'],

    'data': [
        'security/res_button_groups.xml',
        'views/tw_other_receivable_approval_view.xml',
    ]
}
