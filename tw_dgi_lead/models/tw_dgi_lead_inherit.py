# -*- coding: utf-8 -*-

from odoo import models, fields


class TwLeadDGIInherit(models.Model):
    _name = "tw.lead"
    _inherit = ["tw.lead", "tw.dgi.info.mixin"]

    def action_open_dgi_wizard(self):
        """Open DGI Lead sync wizard from list view button"""
        return {
            'name': 'Sync Lead dari DGI',
            'type': 'ir.actions.act_window',
            'res_model': 'tw.dgi.lead.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }

    def action_show_dgi_info(self):
        """Override to pass Lead specific context to DGI Info Wizard"""
        res = super().action_show_dgi_info()
        res['context'].update({
            'default_id_prospect': self.source_document,
        })
        return res
