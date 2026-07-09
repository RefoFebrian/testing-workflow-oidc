# -*- coding: utf-8 -*-
{
    'name': "TW Partner",

    'summary': """
        Partner
        """,

    'description': """
        Partner
    """,

    'author': "Tunas Honda",
    'license': "LGPL-3",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/10.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'TW Partner / TW Partner',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base', 
        'contacts', 
        'tw_menu', 
        'base_suspend_security',
        'tw_selection',
        'tw_localization',
        'tw_sequence',
        'tw_web', 
        'l10n_id_efaktur'
    ],

    # always loaded
    'data': [
        'data/data_contact_tags.xml',
        'data/data_selection.xml',
        'data/data_partner_type.xml',
        'data/data_partner.xml',
        
        'security/ir_rule.xml',
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        
        'views/tw_partner_view.xml',
        'views/tw_all_partner_menu_view.xml',
        'wizards/tw_customer_validation_base_view.xml',
        'wizards/tw_partner_wizard_view.xml',
        'views/tw_supplier_inherit_view.xml',
        'views/tw_finco_inherit_view.xml',
        'views/tw_customer_view.xml',
        'views/tw_dealer_group_view.xml',
        'views/tw_principle_view.xml',
        'views/tw_birojasa_view.xml',
        'views/tw_partner_category_view.xml',

        'views/tw_menu_view.xml',
    ],

    'application': True,
    'installable': True,


    'external_dependencies': {'python': ['validate_email']},
}