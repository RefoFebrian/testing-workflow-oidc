# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.exceptions import ValidationError

# 5: local imports

# 6: Import of unknown third party lib

class InheritTwAssetDistribution(models.Model):
    _inherit = "tw.asset.distribution"

    # 10: constraints & sql constraints
    @api.constrains('detail_ids')
    def _check_peminjaman_detail_ids(self):
        err_msg = ""
        for x in self.detail_ids:
            if x.asset_id.sudo().rent_id:
                err_msg += "Aset [%s] - [%s] %s sedang dipinjam di %s\n" % (x.asset_id.sudo().name, x.asset_id.sudo().code, x.asset_id.sudo().name, x.asset_id.sudo().rent_id.name)
        if err_msg:
            raise ValidationError(err_msg)