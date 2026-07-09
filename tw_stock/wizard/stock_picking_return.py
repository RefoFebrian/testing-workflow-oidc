# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning    

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwStockReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"
    _description = "Return Picking"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_create_returns(self):
        """
        Override to prevent double returns and enforce Full Return policy.
        Validates that there are no non-cancelled return pickings for the source picking.
        Also validates that the picking is at a returnable step (end of chain).
        """
        self.ensure_one()
        if self.picking_id:
            # 1. Validasi Full Return (Quantity & Completion)
            # Ambil move_ids yang valid untuk diretur (biasanya yang state 'done')
            original_moves = self.picking_id.move_ids.filtered(lambda m: m.state == 'done' and m.quantity > 0)
            return_move_ids = self.product_return_moves.mapped('move_id')

            # Cek apakah ada produk yang dihapus dari wizard (Partial by Line)
            missing_moves = original_moves - return_move_ids
            if missing_moves:
                raise Warning(_(
                    "Partial Return tidak diperbolehkan. Semua produk pada dokumen '%s' harus dikembalikan.\n"
                    "Produk yang hilang: %s"
                ) % (self.picking_id.name, ", ".join(missing_moves.mapped('product_id.display_name'))))

            for line in self.product_return_moves:
                # Cek apakah kuantitas tidak sama (Partial by Quantity)
                if line.quantity != line.move_id.quantity:
                    raise Warning(_(
                        "Partial Return tidak diperbolehkan. Kuantitas retur untuk produk '%s' (%s) "
                        "harus sama dengan kuantitas aktual pada Picking (%s)."
                    ) % (line.product_id.display_name, line.quantity, line.move_id.quantity))

            # 2. Cegatan Step Logistik: Harus di step paling ujung
            if not self.picking_id.is_returnable_step:
                raise Warning(_("Return hanya diperbolehkan pada step logistik terakhir (transit tujuan akhir)."))
            
            # 3. Cegat double return: Jika sudah ada return log yang tidak cancel, tolak.
            valid_returns = self.picking_id.return_ids.filtered(lambda p: p.state != 'cancel')
            if valid_returns:
                raise Warning(_(
                    "Dokumen Picking '%s' sudah pernah direturn sebelumnya (%s).\n"
                    "Return kedua kalinya untuk dokumen ini ditolak oleh sistem."
                ) % (self.picking_id.name, ", ".join(valid_returns.mapped('name'))))
            
            # 4. Cegat jika dokumen yang akan direturn ternyata adalah dokumen hasil return juga
            if any(move.origin_returned_move_id for move in self.picking_id.move_ids):
                raise Warning(_(
                    "Dokumen Picking '%s' adalah dokumen hasil return. "
                    "Sistem tidak mengizinkan return atas dokumen yang sudah merupakan hasil return."
                ) % self.picking_id.name)
                
        return super().action_create_returns()

    # 14: private methods
