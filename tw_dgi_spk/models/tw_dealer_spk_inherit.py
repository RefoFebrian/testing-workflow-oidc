# -*- coding: utf-8 -*-

from odoo import models, fields


class TwDealerSpkDGIInherit(models.Model):
    """
    Extend tw.dealer.spk for DGI specific logic.

    Fields yang digunakan untuk integrasi DGI:
    - source_document → idSpk dari DGI (unique identifier)
    - lead_reference → idProspect dari DGI (link ke Lead)
    """
    _inherit = "tw.dealer.spk"

    # DGI Integration Fields
    source_document = fields.Char(
        string='DGI SPK ID',
        help='ID SPK dari DGI (idSpk)',
        index=True,
    )
    is_dgi = fields.Boolean(
        string='Is DGI',
        default=False,
        help='Penanda data dari integrasi DGI',
    )
    
    dgi_get_date = fields.Datetime(
        string="DGI Get Date",
        copy=False,
        readonly=True,
        help="Tanggal & waktu GET data dari DGI"
    )
    dgi_get_uid = fields.Many2one(
        'res.users',
        string="DGI Get By",
        copy=False,
        readonly=True,
        help="User yang melakukan GET data dari DGI"
    )

    def action_open_dgi_spk_wizard(self):
        """Open DGI SPK sync wizard from list view button"""
        return {
            'name': 'Sync SPK dari DGI',
            'type': 'ir.actions.act_window',
            'res_model': 'tw.dgi.spk.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }

    def action_show_dgi_info(self):
        """Show DGI integration info via popup"""
        self.ensure_one()
        return {
            'name': 'DGI Info',
            'type': 'ir.actions.act_window',
            'res_model': 'tw.dgi.info.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_model': self._name,
                'default_res_id': self.id,
                'default_is_dgi': self.is_dgi,
                'default_source_document': self.source_document,
                'default_id_prospect': self.lead_reference,
                'default_dgi_get_date': self.dgi_get_date,
                'default_dgi_get_uid': self.dgi_get_uid.id,
            }
        }

    def _prepare_dealer_sale_order_vals(self):
        """Propagate lead relation to DSO generated from DGI SPK."""
        values = super()._prepare_dealer_sale_order_vals()
        if self.lead_id:
            values["lead_id"] = self.lead_id.id
            
        # Ensure SPK payment type overrides the Lead payment type if it exists
        if self.payment_type_id:
            values["payment_type_id"] = self.payment_type_id.id
        
        # Propagate DGI info to DSO
        if self.is_dgi:
            values.update({
                'source_document': self.source_document,
                'is_dgi': self.is_dgi,
                'dgi_get_date': self.dgi_get_date,
                'dgi_get_uid': self.dgi_get_uid.id if self.dgi_get_uid else False,
            })
        
        return values
