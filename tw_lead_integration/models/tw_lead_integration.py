# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date,timedelta,datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError

# 5: local imports

# 6: Import of unknown third party lib


class twLeadIntegration(models.Model):
    _inherit = "tw.lead"
    _description = 'Lead Integration'    

    # 7: defaults methods

    # 8: fields
    version_code = fields.Char('version Code')
    version_name = fields.Char('version Name')
    unique_code = fields.Char(string='Unique Code')
    source_document = fields.Char(string='Source Document')
    reference = fields.Char(string='Reference')
    integration_remark = fields.Char(string='Remark Integrasi')
    is_integration = fields.Boolean(string='Is Integration', default=False)
    integration_get_date = fields.Datetime(
        string='Integration Get Date',
        readonly=True,
        help="Date when this lead was synced from integration"
    )
    integration_get_uid = fields.Many2one(
        comodel_name='res.users',
        string='Integration Get By',
        readonly=True,
        help="User who synced this lead from integration"
    )
    integration_state = fields.Selection([
        ('draft','Draft'),
        ('error','Error'),
        ('done','Done')
    ],'Status Integrasi',default='draft')
    
    source_data_id = fields.Many2one(
        comodel_name='tw.selection',
        string='Data Source',
        domain=[('type', '=', 'LeadSourceData')]
    )
    web_source_id = fields.Many2one(
        comodel_name='tw.selection',
        string='Source Web',
        domain=[('type', '=', 'LeadWebSource')]
    )

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods