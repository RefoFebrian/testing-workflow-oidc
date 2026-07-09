# Create a script to inspect hr.job records in Odoo database
import os
import sys

# Add Odoo path
sys.path.append('/Users/liong/Documents/odoo18')
import odoo
config_path = '/Users/liong/Documents/odoo18_teds.conf'
odoo.tools.config.parse_config(['-c', config_path])
# Connect to DB
db_name = 'teto_staging_may'
registry = odoo.registry(db_name)

with registry.cursor() as cr:
    env = odoo.api.Environment(cr, 2, {}) # User 2
    
    # Test case sensitive search
    cs = env['hr.job'].search([('name', '=', 'Team Leader Partner Digital')])
    print(f"Case-sensitive search ('='): {cs}")

    # Test case-insensitive search
    ci = env['hr.job'].search([('name', '=ilike', 'Team Leader Partner Digital')])
    print(f"Case-insensitive search ('=ilike'): {ci}")
