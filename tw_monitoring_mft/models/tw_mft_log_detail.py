# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

_logger = logging.getLogger(__name__)


class TwMftLogDetail(models.Model):
    """Model to store error details from Portal AHM get-data-detail-mft endpoint."""
    
    _name = "tw.mft.log.detail"
    _description = "MFT Log Detail"
    _order = "errorrow"

    # 7: defaults methods

    # 8: fields
    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True
    )
    filename = fields.Char(string='File Name')
    errorrow = fields.Integer(string='Error Row', index=True)
    errormsg = fields.Text(string='Error Message')

    # 9: relation fields
    log_id = fields.Many2one(
        'tw.mft.log',
        string='MFT Log',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    # Related fields for easy access
    fileid = fields.Char(
        related='log_id.fileid',
        string='File ID',
        store=True
    )
    config_id = fields.Many2one(
        related='log_id.config_id',
        string='Configuration',
        store=True
    )

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('errorrow')
    def _compute_name(self):
        for rec in self:
            rec.name = f"Row {rec.errorrow}" if rec.errorrow else 'Error'

    # 12: override methods

    # 13: action methods

    # 14: private methods
