# -*- coding: utf-8 -*-

def post_init_hook(env):
    """Compile Document Handling output templates from mapping master on install/upgrade."""
    endpoint_codes = [
        "doch_proses_stnk",
        "doch_receipt_stnk",
        "doch_receipt_bpkb",
        "doch_handover_stnk",
        "doch_handover_bpkb",
    ]
    endpoint_obj = env["tw.endpoint.configuration"].sudo().search([
        ("code", "in", endpoint_codes),
    ])
    endpoint_obj._compile_output_template_from_mappings()
