# Part of Flectra. See LICENSE file for full copyright and licensing details.

{
    'name': 'REST API For Flectra',
    'version': '1.0.0',
    'license': 'AGPL-3',
    'category': 'API',
    'author': 'FlectraHQ',
    'website': 'https://www.flectrahq.com',
    'summary': 'REST API For Flectra',
    'description': """
REST API For Flectra
====================
With use of this module user can enable REST API in any Flectra applications/modules

For detailed example of REST API refer *readme.md*
""",
    'depends': [
        'base',
        'web',
        'base_suspend_security',
        'tw_base',
        'tw_selection'
    ],
    "external_dependencies": {"python" : ["PyJWT","oauthlib"]},
    'data': [
        'data/ir_configparameter_data.xml',
        # 'security/ir.model.access.csv',
        'security/res_groups.xml',
        'data/grant_type_data.xml',
        'views/ir_model_view.xml',
        'views/res_user_view.xml',
        'views/tw_selection_grant_type_view.xml',
        'views/tw_menu.xml'
    ],
    'installable': True,
    'auto_install': False,
}
