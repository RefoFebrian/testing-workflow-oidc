# -*- coding: utf-8 -*-


def post_init_hook(env):
    """Compile inbound output templates from mapping master on install/upgrade."""
    env["tw.endpoint.configuration"]._compile_inbound_output_templates()
