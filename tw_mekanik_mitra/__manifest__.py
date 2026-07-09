{
    'name':"TW Mekanik Mitra",
    'summary': "TW Mekanik Mitra",
    'description': """
        TW Mekanik Mitra
    """,
    'author':"Tunas Honda",
    'website': "https://www.honda-ku.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'AGPL-3',
    'depends':['base','tw_base','tw_work_order'],
    'init_xml':[],
    'demo_xml':[],
    'data':[
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'report/tw_report_mekanik_mitra_view.xml',
        'views/tw_hr_employee_view.xml',
        'views/tw_matrix_mekanik_mitra_view.xml',

        'views/tw_menu.xml',

        'data/hr_employee_category_data.xml',
    ],
    'active':False,
    'installable':True
}
