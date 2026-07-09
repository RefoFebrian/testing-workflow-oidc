# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TWBranchSettingBirojasa(models.Model):
    _name = "tw.branch.setting.birojasa"
    _description = 'Birojasa Branch Setting'

    # 7: defaults methods

    # 8: fields
    name = fields.Char(string="Name", compute='_compute_name', store=True, help="Name of the Biro Jasa setting. This can be used to identify the setting in the UI.")
    default = fields.Boolean(string='Default', help="Set this as the default Biro Jasa for the branch. Only one Biro Jasa can be set as default per branch.")

    # 9: relation fields
    branch_setting_id = fields.Many2one(comodel_name='tw.branch.setting', string='Branch Setting', required=True, ondelete='cascade')
    biro_jasa_id = fields.Many2one(comodel_name='res.partner', string='Biro Jasa', domain=[('category_id.name', '=', 'Birojasa')])
    pricelist_ids = fields.Many2many(comodel_name='product.pricelist', string='Pricelists', column1='birojasa_id', column2='pricelist_id',
                                     domain="[('partner_id', '=', biro_jasa_id), ('type', '=', 'bbn_purchase')]",
                                     help="Pricelists associated with this Biro Jasa. If not set, the default pricelist will be used.")

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    def _compute_name(self):
        for record in self:
            record.name = f"{record.biro_jasa_id.name} - {record.branch_setting_id.company_id.name}" if record.biro_jasa_id and record.branch_setting_id else "Unnamed Biro Jasa Setting"

    # 12: override methods

    # 13: action methods
    def action_open_pricelist(self):
        for record in self:
            view_mode = 'tree,form'
            res_id = False
            if len(record.pricelist_ids) == 1:
                view_mode = 'form'
                res_id = record.pricelist_ids.id
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'product.pricelist',
                'domain': [('id', 'in', record.pricelist_ids.ids)],
                'view_mode': view_mode,
                'res_id': res_id,
                'target': 'current',
            }

    # 14: private methods
