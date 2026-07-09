# -*- coding: utf-8 -*-
import json
import os
import logging

_logger = logging.getLogger(__name__)

# Dashboard mapping: JSON filename (without .json) -> XML ref ID
# Add new dashboards here as they are created
DASHBOARD_MAPPING = {
    'dashboard_user': 'tw_boom_dashboard.tw_boom_dashboard_header_user',
    'dashboard_admin_area': 'tw_boom_dashboard.tw_boom_dashboard_header_admin_area',
    'dashboard_area_manager': 'tw_boom_dashboard.tw_boom_dashboard_header_area_manager',
    'dashboard_admin_manager': 'tw_boom_dashboard.tw_boom_dashboard_header_admin_manager',
    'dashboard_gm_coo': 'tw_boom_dashboard.tw_boom_dashboard_header_gm_coo',
}


def import_dashboard_json(env, force=False):
    """
    Import dashboard charts from JSON files.
    
    Args:
        env: Odoo environment
        force: If True, import even if dashboard already has charts
    
    This supports multiple dashboards by mapping JSON filenames to their XML ref IDs.
    Each JSON file should be named after the dashboard key in DASHBOARD_MAPPING.
    
    Directory structure:
        data/json/
            dashboard_user.json    -> imports to tw_boom_dashboard_header_user
            dashboard_admin_area.json -> imports to tw_boom_dashboard_header_admin_area
    """
    
    # Look for JSON files in data/json directory
    module_path = os.path.dirname(os.path.abspath(__file__))
    json_dir = os.path.join(module_path, 'data', 'json')
    
    if not os.path.exists(json_dir):
        _logger.info("TW BOOM Dashboard: No JSON directory found at %s, skipping import.", json_dir)
        return
    
    imported_count = 0
    
    # Process each JSON file and import to its corresponding dashboard
    for filename in sorted(os.listdir(json_dir)):
        if not filename.endswith('.json'):
            continue
            
        # Get dashboard key from filename (e.g., "dashboard_user.json" -> "dashboard_user")
        dashboard_key = filename[:-5]  # Remove .json extension
        
        # Find the corresponding dashboard XML ref
        dashboard_ref = DASHBOARD_MAPPING.get(dashboard_key)
        if not dashboard_ref:
            continue
        
        # Get the dashboard record from XML ref
        dashboard = env.ref(dashboard_ref, raise_if_not_found=False)
        if not dashboard:
            continue
        
        # Create/update menu FIRST so dashboard is properly initialized
        # Skip this if we are upgrading and menu already exists to avoid concurrent update errors
        try:
            if not dashboard.created_menu_id:
                dashboard.create_update_menu()
            else:
                pass
        except Exception as e:
            continue
        
        # Skip import if dashboard already has charts (unless force=True)
        # In INTELLIGENT SYNC, we don't unlink. We update existing standard charts.
        if dashboard.chart_ids and not force:
            continue
        
        # Import the JSON file
        filepath = os.path.join(json_dir, filename)
        try:
            # Use utf-8-sig to handle BOM (Byte Order Mark) in JSON files
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                json_data = json.load(f)
            
            # Call the dashboard sync method (we use a new key 'is_sync' to signal intelligent merge)
            result = dashboard.dashboard_import_json({
                'json_payload': json_data,
                'is_sync': True,
                'force': force
            })
            
            if result.get('type') == 'success':
                imported_count += 1
            else:
                continue
                
        except Exception as e:
            continue

    return imported_count


def post_init_hook(env):
    """
    Post-init hook - runs on module INSTALL only.
    Calls the shared import function.
    """
    import_dashboard_json(env)

