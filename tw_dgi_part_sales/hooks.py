# -*- coding: utf-8 -*-

def post_init_hook(env):
    """Compile Part Sales output templates from mapping master on install/upgrade."""
    endpoint_obj = env["tw.endpoint.configuration"].sudo().search([
        ("code", "=", "dgi_get_part_sales"),
    ])
    endpoint_obj._compile_output_template_from_mappings()
