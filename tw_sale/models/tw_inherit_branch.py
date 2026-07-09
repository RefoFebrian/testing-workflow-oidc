# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TWSaleBranch(models.Model):
    _inherit = "res.company"
    
    # 7: defaults methods

    # 8: fields
    is_so_unit_pick_then_invoice = fields.Boolean("SO Unit: Pick dulu sebelum Invoice")
    is_so_sparepart_pick_then_invoice = fields.Boolean("SO Sparepart: Pick dulu sebelum Invoice")
    
    @api.onchange("is_so_unit_pick_then_invoice", "is_so_sparepart_pick_then_invoice")
    def _onchange_add_account_move_line(self):
        for rec in self:
            if (rec.is_so_unit_pick_then_invoice or rec.is_so_sparepart_pick_then_invoice) and rec.warehouse_id:
                if rec.warehouse_id.delivery_steps == "ship_only":
                    raise Warning(
                        "Warehouse %s masih menggunakan Outgoing Shipments 'Deliver (1 step)'.\n\n"
                        "Jika ingin mengaktifkan opsi 'Pick dulu sebelum Invoice', "
                        "ubah Outgoing Shipments menjadi minimal 'Pick + Deliver (2 steps)'."
                        % rec.warehouse_id.name
                    )