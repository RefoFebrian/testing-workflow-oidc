# -*- coding: utf-8 -*-
{
    'name': "TW HR",

    'summary': "Human Resource",

    'description': """
        Human Resource Modules
    """,

    'author': "Tunas Honda",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    # TODO: buat listing by excel untuk kategori dan kesepakatan
    'category': 'TW HR / TW HR',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base'
                ,'hr_skills'
                ,'hr'
                ,'tw_menu'
                ,'tw_base'
                ,'tw_branch'
                ,'tw_localization'
                ,'auth_oauth'
                ,'tw_selection'
            ],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'security/res_groups_button.xml',
        'security/res_groups_job.xml',

        'views/tw_job_view.xml',
        'views/tw_department_view.xml',
        'views/tw_employee_view.xml',
        'views/tw_selection_job_category_view.xml',
        'views/tw_selection_job_level_view.xml',
        'views/tw_selection_sales_force_view.xml',
        'views/tw_hr_menu_view.xml',

        'data/tw_selection_job.xml',
        'data/tw_employee_cron.xml',
        'data/tw_hr_config.xml',
        
        'wizards/tw_employee_import_wizard_views.xml',
    ],
    'demo': [],
    "installable": True,
	"auto_install": False,
	"application": True,
}

