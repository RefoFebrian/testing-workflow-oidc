# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwVehicleDocumentStockOpnameOther(models.Model):
    _name = "tw.vehicle.document.stock.opname.other"
    _description = "Vehicle Document Stock Opname Other"

    # 7: defaults methods

    # 8: fields
    name_ownership = fields.Char('Customer BPKB')
    name_registration = fields.Char('Customer STNK')
    no_engine = fields.Char('No Engine')
    description = fields.Char('Keterangan')

    # 9: relation fields
    opname_id = fields.Many2one('tw.vehicle.document.stock.opname', 'Stock Opname', ondelete='cascade')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods