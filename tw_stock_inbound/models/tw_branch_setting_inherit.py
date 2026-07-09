from odoo import models, fields, api


class TwBranchSettingInherit(models.Model):
    _inherit = "tw.branch.setting"

    expedition_id = fields.Many2one('res.partner', string='Default Expedition', domain=[('category_id.name', '=', 'Expedition')])
    