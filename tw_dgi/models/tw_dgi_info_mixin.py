# -*- coding: utf-8 -*-

from odoo import models, fields

class TwDgiInfoMixin(models.AbstractModel):
    """
    Mixin model to provide standard DGI integration fields and a smart button action.
    """
    _name = 'tw.dgi.info.mixin'
    _description = 'DGI Information Mixin'

    is_dgi = fields.Boolean(string='Is DGI', default=False, copy=False)
    dgi_get_date = fields.Datetime(string='DGI Get Date', copy=False)
    dgi_get_uid = fields.Many2one('res.users', string='DGI Get By', copy=False)

    def action_show_dgi_info(self):
        """Action called by the 'From DGI' smart button"""
        self.ensure_one()
        
        return {
            'name': 'DGI Information',
            'type': 'ir.actions.act_window',
            'res_model': 'tw.dgi.info.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_dgi_get_date': self.dgi_get_date,
                'default_dgi_get_uid': self.dgi_get_uid.id if self.dgi_get_uid else False,
            }
        }
