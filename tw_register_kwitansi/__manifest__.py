{
    'name':'TW Registrasi Kwitansi',

    'summary': 'TW Registrasi Kwitansi',

    'description': """
        TW Register Kwitansi
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    'version':'0.1',
    'license': 'AGPL-3',

    'category':'Uncategorized',
    'depends':[
        'base',
        'tw_base',
        'tw_branch',
        "tw_menu",
        'tw_sequence',
        'tw_payment'
    ],
    'init_xml':[],
    'demo_xml':[],
    'data':[
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/ir_rule.xml',

        'report/tw_register_kwitansi_report_view.xml',
        'report/tw_laporan_kwitansi_view.xml',

        'views/tw_menu.xml',
        'views/tw_register_kwitansi_view.xml',
        'views/tw_generate_register_kwitansi_view.xml',

    ],
    'active':False,
    'installable':True
}
