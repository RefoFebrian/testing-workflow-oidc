# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResUsersAuth(models.Model):
    _inherit = "res.users"
    
    # NOTE: Azure token configuration has been moved to tw.api.configuration
    # Fields client_id, client_secret, client_scope, and get_azure_access_token method
    # are now in tw_api_config.py under tw.api.configuration model.