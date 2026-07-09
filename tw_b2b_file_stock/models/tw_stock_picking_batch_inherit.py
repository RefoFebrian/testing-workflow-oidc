# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError as Warning

# 4:  imports from odoo modules
from odoo.exceptions import UserError

# 5: local imports

# 6: Import of unknown third party lib

class B2bFileStockPickingBatchInherit(models.Model):
    _inherit = "stock.picking.batch"

    # 7: defaults methods

    # 8: fields

    # Audit Trail

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    
    # 14: private methods
    def _find_pickings_for_unit_line(self, line):
        """
        Find pickings for a unit line by ship_list_number.
        
        :param line: tw.stock.picking.batch.line record
        :return: stock.picking recordset
        :raises Warning: if no picking found
        """
        pickings = self.env['stock.picking'].suspend_security().search([
            ('mft_reference', '=', line.lot_id.ship_list_number),
            ('state', 'in', ['assigned', 'confirmed']),
        ])
        if not pickings:
            raise Warning(f"Picking {line.lot_id.ship_list_number} Not Found!")
        return pickings
