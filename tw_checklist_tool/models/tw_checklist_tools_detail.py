# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwChecklistToolsDetail(models.Model):
    _name = "tw.checklist.tools.detail"
    _description = "Detail Checklist Tools"

    # 7: defaults methods

    # 8: fields
    tools_state = fields.Selection([('baik', '✔ Baik'), ('rusak', 'R Rusak'), ('hilang', 'H Hilang'), ('tidak_ada', 'X Tidak Ada'), ], string="Kondisi")
    filename = fields.Char('Photo')

    # 9: relation fields
    master_tool_id = fields.Many2one('tw.master.tools')
    master_tool_line_id = fields.Many2one('tw.master.tools.line', string="Master Tools Line")
    product_id = fields.Many2one('product.product', string="Product Name")
    location_id = fields.Many2one('tw.selection', string="Location", domain="[('type', '=', 'MasterToolsLocationType')]")
    line_checklist_id = fields.Many2one('tw.checklist.tools.line', string='Line Checklist', ondelete='cascade')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        return super(TwChecklistToolsDetail, self).create(vals_list)

    def write(self, vals):
        write = super(TwChecklistToolsDetail, self).write(vals)
        return write

    # 13: action methods

    # 14: private methods