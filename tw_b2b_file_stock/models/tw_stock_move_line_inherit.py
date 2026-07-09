from odoo import models, fields, api, _
from odoo.exceptions import ValidationError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class B2bFileStockMoveLine(models.Model):
    _inherit = "stock.move.line"
    _description = "Stock Move Line"


    def _prepare_domain_lot(self):
        domain = super()._prepare_domain_lot()
        # If you want to add a domain to the lot, use this method to add the domain parameter. append domain from return result of this method
        is_incoming_md = self.picking_id._is_incoming_md()
        if is_incoming_md and self.picking_id.division == 'Unit':
            domain.append(('ship_list_number', '=', self.picking_id.mft_reference))
        return domain