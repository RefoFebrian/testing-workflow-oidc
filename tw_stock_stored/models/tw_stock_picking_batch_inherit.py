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

class TwStockStoredStockPickingBatchInherit(models.Model):
    _inherit = "stock.picking.batch"

    # 7: defaults methods  

    # 8: fields
    state = fields.Selection(selection_add=[('stored', 'Stored'),('done',)], ondelete={"stored": "cascade"},
        help=" * Draft: The transfer is not confirmed yet. Reservation doesn't apply.\n"
             " * Waiting another operation: This transfer is waiting for another operation before being ready.\n"
             " * Waiting: The transfer is waiting for the availability of some products.\n(a) The shipping policy is \"As soon as possible\": no product could be reserved.\n(b) The shipping policy is \"When all products are ready\": not all the products could be reserved.\n"
             " * Ready: The transfer is ready to be processed.\n(a) The shipping policy is \"As soon as possible\": at least one product has been reserved.\n(b) The shipping policy is \"When all products are ready\": all product have been reserved.\n"
             " * Stored: The transfer has been Received but the stock is not updated.\n"
             " * Done: The transfer has been processed.\n"
             " * Cancelled: The transfer has been cancelled."
    )
    
    # Audit Trail
    store_date = fields.Datetime(string="Stored Date")
    store_uid = fields.Many2one('res.users', string="Stored By")

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    def action_done(self):
        self.ensure_one()
        res = super(TwStockStoredStockPickingBatchInherit, self).action_done()
        if any(picking.state == 'stored' for picking in self.picking_ids):
            self.action_stored()
        return res

    # 13: action methods
    def action_check_stored_done(self):
        for batch in self:
            if all(picking.state == 'stored' for picking in batch.picking_ids):
                batch.action_stored_done()

    def action_stored_done(self):
        return self.write({
            'state': 'done', 
            'validate_date': datetime.now(), 
            'validate_uid': self.env.user.id
        })

    def action_stored(self):
        return self.write({
            'state': 'stored', 
            'store_date': datetime.now(), 
            'store_uid': self.env.user.id
        })