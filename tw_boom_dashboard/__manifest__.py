# -*- coding: utf-8 -*-
{
    'name': 'TW BOOM Dashboard',
    'summary': 'Dashboard for BOOM Task Management (Extended from Synconics BI)',
    'description': """
        BOOM Dashboard
        ===================
        Inherits from Synconics BI Dashboard to provide:
        * Custom Chart Types for BOOM
        * Extended Task Statistics
        * Specialized Leaderboards
    """,
    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",
    'category': 'Dashboard',
    'version': '1.0',
    'license': 'AGPL-3',

    # CRITICAL: Depend on the parent module
    'depends': [
        'base',
        'base_suspend_security',
        'tw_base',
        'synconics_bi_dashboard',
        'tw_boom', # Assuming we still need core BOOM logic
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_access.xml',
        
        # Views
        'views/dashboard_font_view.xml',
        'views/dashboard_chart_inherit_view.xml',
        'views/dashboard_inherit_view.xml',

        # Menu (must be before dashboard data for parent_menu_id reference)
        'views/tw_menu.xml',
        
        # Data (depends on menu XML for parent_menu_id reference)
        'data/xml/tw_boom_dashboard_header_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
             # XML (Templates)
             'tw_boom_dashboard/static/src/xml/dashboard_chart_wrapper_inherit.xml',
             'tw_boom_dashboard/static/src/xml/dashboard_amcharts_inherit.xml',
             'tw_boom_dashboard/static/src/components/KPILayoutsInherit/KpiLayoutsInherit.xml',
             'tw_boom_dashboard/static/src/components/TileLayoutsInherit/TileLayoutsInherit.xml',
             'tw_boom_dashboard/static/src/components/Greeting/dashboard_greeting_chart.xml',
             'tw_boom_dashboard/static/src/components/Quote/dashboard_quote_chart.xml',
             'tw_boom_dashboard/static/src/components/Birthday/dashboard_birthday_chart.xml',
             'tw_boom_dashboard/static/src/components/Label/dashboard_label_chart.xml',
             'tw_boom_dashboard/static/src/components/ProgressBar/dashboard_progress_bar_chart.xml',
             'tw_boom_dashboard/static/src/components/FilterLayout/dashboard_filter_layout.xml',
             'tw_boom_dashboard/static/src/components/StackedProgressBar/dashboard_stacked_progress_chart.xml',
             'tw_boom_dashboard/static/src/xml/kpi_layout_inherit.xml',
             'tw_boom_dashboard/static/src/xml/kpi_view_inherit.xml',
             'tw_boom_dashboard/static/src/xml/kpi_layouts_color_inherit.xml',
             'tw_boom_dashboard/static/src/xml/listview_inherit.xml',
             'tw_boom_dashboard/static/src/xml/listview_color_inherit.xml',
             'tw_boom_dashboard/static/src/xml/form_dashboard_preview_inherit.xml',
             'tw_boom_dashboard/static/src/components/KPILayouts/KpiLayoutSix/KpiLayoutSix.xml',
             
             # JS (Logic)
             'tw_boom_dashboard/static/src/js/dashboard_chart_wrapper_inherit.js',
             'tw_boom_dashboard/static/src/js/chart_color_patch.js',
             'tw_boom_dashboard/static/src/js/chart_font_patch.js',
             'tw_boom_dashboard/static/src/js/dashboard_amcharts_inherit.js',
             'tw_boom_dashboard/static/src/components/Greeting/dashboard_greeting_chart.js',
             'tw_boom_dashboard/static/src/components/Quote/dashboard_quote_chart.js',
             'tw_boom_dashboard/static/src/components/Birthday/dashboard_birthday_chart.js',
             'tw_boom_dashboard/static/src/components/Label/dashboard_label_chart.js',
             'tw_boom_dashboard/static/src/components/ProgressBar/dashboard_progress_bar_chart.js',
             'tw_boom_dashboard/static/src/components/FilterLayout/dashboard_filter_layout.js',
             'tw_boom_dashboard/static/src/components/StackedProgressBar/dashboard_stacked_progress_chart.js',
             'tw_boom_dashboard/static/src/components/ListViewInherit/ListViewPatch.js',
             'tw_boom_dashboard/static/src/js/fa_icon_widget_inherit.js',
             'tw_boom_dashboard/static/src/js/form_dashboard_preview_inherit.js',
             'tw_boom_dashboard/static/src/js/dynamic_font_loader.js',
             'tw_boom_dashboard/static/src/js/kpi_color_patch.js',
             'tw_boom_dashboard/static/src/js/kpi_layout_six_patch.js',
             'tw_boom_dashboard/static/src/js/stacked_chart_orientation_patch.js',
             'tw_boom_dashboard/static/src/components/KPILayouts/KpiLayoutSix/KpiLayoutSix.js',
            
            # CSS (Styles)
            'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Roboto:ital,wght@0,300;0,400;0,500;0,700;1,400&family=Open+Sans:ital,wght@0,400;0,600;1,400&family=Lato:ital,wght@0,400;0,700;1,400&display=swap',
            'tw_boom_dashboard/static/src/scss/GridStackInherit/gridstack.min.inherit.scss',
            'tw_boom_dashboard/static/src/scss/style_dashboard.scss',
        ],
    },
    'external_dependencies': {
        'python': ['pandas'],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': True,
    'auto_install': False,
}
