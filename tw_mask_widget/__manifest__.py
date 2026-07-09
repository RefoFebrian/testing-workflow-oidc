{
    'name': "TW Mask Widget",

    'summary': """Widget to mask sensitive information in form views""",

    'description': """
        This module provides a custom widget 'mask_sensitive' that masks 
        sensitive information like phone numbers, emails, and IDs in view mode.
        
        Features:
        - Masks values in view mode (e.g., 08*********2)
        - Shows masked value in edit mode until user clicks the field
        - On focus, field becomes blank for user input
        - If user doesn't enter anything, original value is preserved
        - Users with 'Admin Data Pribadi' group can see unmasked values
        
        Usage in XML:
        <field name="mobile" widget="mask_sensitive" options="{'mask_type': 'phone'}"/>
        <field name="work_email" widget="mask_sensitive" options="{'mask_type': 'email'}"/>
        <field name="identification_id" widget="mask_sensitive" options="{'mask_type': 'id'}"/>
    """,

    'author': "TW",
    'website': "http://www.tunas.honda.com",
    'category': 'Web',
    'version': '18.0.1.0.0',

    'depends': ['web', 'tw_base'],

    'data': [
        'security/res_groups.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'tw_mask_widget/static/src/**/*',
        ],
    },

    'license': 'LGPL-3',
}
