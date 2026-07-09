# -*- coding: utf-8 -*-

def post_init_hook(env):
    """Compile Lead output templates from mapping master on install/upgrade."""
    endpoint_obj = env["tw.endpoint.configuration"].sudo().search([
        ("code", "=", "dgi_prospect"),
    ])
    endpoint_obj._compile_output_template_from_mappings()
