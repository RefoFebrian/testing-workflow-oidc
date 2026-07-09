# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, api, fields

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwStockOpnameDirectGiftOther(models.Model):
    _name = "tw.stock.opname.direct.gift.other"
    _description = "TW Stock Opname Direct Gift Other"

    # 7: defaults methods

    # 8: fields
    product_name = fields.Char('Nama Barang')
    qty_physical_good = fields.Float('Qty Fisik Baik')
    qty_physical_broken = fields.Float('Qty Fisik Rusak')
    qty_physical_total = fields.Float('Total Qty Fisik',compute='_compute_fisik_total')
    balance_log_book = fields.Float('Saldo Logbook')

    # 9: relation fields
    opname_id = fields.Many2one('tw.stock.opname.direct.gift', ondelete='cascade')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('qty_physical_good', 'qty_physical_broken')
    def _compute_fisik_total(self):
        for record in self:
            record.qty_physical_total = record.qty_physical_good + record.qty_physical_broken

    # 12: override methods

    # 13: action methods

    # 14: private methods