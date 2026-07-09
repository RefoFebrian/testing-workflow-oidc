# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwTargetSalesPeopleLine(models.Model):
    _name = "tw.target.sales.people.line"
    _description = "Target Sales People Line"

    # 7: defaults methods
    def _get_default_date(self):
        return self.env['res.company'].get_default_date()

    def _get_target(self):
        targets = self.env['tw.master.target'].search([])
        ids = []
        for target in targets:
            ids.append((target.name, target.name))
        return ids

    # 8: fields
    type = fields.Selection([
        ('Daily', 'Daily'), 
        ('Monthly', 'Monthly'), 
        ('Yearly', 'Yearly')
    ], string='Type')

    target = fields.Integer(string='Target', default=0)
    target_type = fields.Selection(selection=_get_target, string='Target Type')

    # 9: relation fields
    target_id = fields.Many2one(comodel_name='tw.target.sales.people', string='Target ID', help='')
    category_id = fields.Many2one(comodel_name='tw.selection', string='Category', domain=[('type', '=', 'CategoryTWTarget')], help='')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            if val.get('type') and val.get('date'):
                if val['type'] == 'monthly':
                    awal_bln = datetime.strptime(val['date'], '%Y-%m-%d').date()
                    val['date'] = str(awal_bln.replace(day=1))
                elif val['type'] == 'yearly':
                    awal_thn = datetime.strptime(val['date'], '%Y-%m-%d').date()
                    val['date'] = str(awal_thn.replace(day=1, month=1))
        return super(TwTargetSalesPeopleLine, self).create(vals)
    
    # 13: action methods

    # 14: private methods