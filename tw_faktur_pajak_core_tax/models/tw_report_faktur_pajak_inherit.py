# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class InheritTWReportFakturPajak(models.TransientModel):
    """Inherit report wizard untuk menambahkan awareness Coretax."""

    _inherit = "tw.report.faktur.pajak"

    # 8: fields
    is_coretax = fields.Boolean(
        string='Is Coretax?',
        compute='_compute_is_coretax',
    )

    # 11: compute/depends & on change methods
    @api.depends_context('uid')
    def _compute_is_coretax(self):
        """Compute Coretax status dari config parameter."""
        use_coretax = self.env['ir.config_parameter'].sudo().get_param(
            'tw_faktur_pajak_core_tax.use_coretax', default=False
        )
        for rec in self:
            rec.is_coretax = bool(use_coretax)
