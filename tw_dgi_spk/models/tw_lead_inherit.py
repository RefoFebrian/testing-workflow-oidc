# -*- coding: utf-8 -*-

from odoo import models, fields, api

class TwLeadInherit(models.Model):
    _inherit = 'tw.lead'

    is_dgi_dso_required = fields.Boolean(
        string='Is DGI DSO Required',
        compute='_compute_is_dgi_dso_required',
    )

    @api.depends('company_id.branch_setting_id.is_dgi_dso_required')
    def _compute_is_dgi_dso_required(self):
        for lead in self:
            branch_setting = lead.company_id.branch_setting_id
            lead.is_dgi_dso_required = branch_setting.is_dgi_dso_required if branch_setting else False

    def action_save_dgi_popup(self):
        """Called when saving DGI data from the DSO confirmation popup"""
        # The form is automatically saved by the Odoo web client before calling this method
        return {'type': 'ir.actions.act_window_close'}

    def action_open_dgi_required_form(self):
        """Open the popup form to manually complete DGI required data"""
        self.ensure_one()
        return {
            'name': 'Lengkapi Data Lead DGI',
            'type': 'ir.actions.act_window',
            'res_model': 'tw.lead',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('tw_dgi_spk.view_tw_lead_dgi_edit_primary_form').id,
            'target': 'new',
        }
