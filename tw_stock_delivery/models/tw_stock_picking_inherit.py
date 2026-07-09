# -*- coding: utf-8 -*-
import requests
import re

from odoo.exceptions import UserError as Warning

from odoo import models, fields, api

class InheritStockPicking(models.Model):
    _inherit = "stock.picking"

    street = fields.Char(related="partner_id.street")
    kabupaten = fields.Char(related="partner_id.city_id.name")
    kecamatan = fields.Char(related="partner_id.district_id.name")
    kelurahan = fields.Char(related="partner_id.sub_district_id.name")
    customer_phone = fields.Char(related="partner_id.mobile")
    customer_phone_html = fields.Html(
        compute='_compute_whatsapp_link',
        sanitize=False,
    )
    def _compute_whatsapp_link(self):
        for rec in self:
            if rec.customer_phone:
                phone = rec.customer_phone.replace('+', '').replace('-', '').replace(' ', '')
                rec.customer_phone_html = f'<a href="https://wa.me/{phone}" target="_blank">{rec.customer_phone}</a>'
            else:
                rec.customer_phone_html = ''
     
    def action_open_map(self):
        for rec in self:
            if not rec.partner_id:
                raise Warning("Tidak ada alamat customer")
            if not rec.company_id:
                raise Warning("Tidak ada company")

            if not rec.partner_id.street or not rec.partner_id.sub_district_id.name or not rec.partner_id.district_id.name or not rec.partner_id.city_id.name or not rec.partner_id.state_id.name:
                raise Warning("Perhatian.\nAlamat Customer Tidak ada atau Tidak lengkap. \nMohon Lengkapi data jalan, kelurahan, kecamatan, kota/kabupaten, provinsi, kode pos.")
            if not rec.company_id.street or not rec.company_id.sub_district_id.name or not rec.company_id.district_id.name or not rec.company_id.city_id.name or not rec.company_id.state_id.name:
                raise Warning("Perhatian.\nAlamat Company Tidak ada atau Tidak lengkap. \nMohon Lengkapi data jalan, kelurahan, kecamatan, kota/kabupaten, provinsi, kode pos.")
            
            # Tampilkan maps di browser
            return {
                'name': "Lokasi Pengiriman",
                'type': 'ir.actions.act_window',
                'res_model': 'tw.stock.picking.delivery.gmaps.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_partner_id': rec.partner_id.id,
                    'default_company_id': rec.company_id.id,
                }
            }
    def _clean_region_name(self, name):
        if not name:
            return ""
        clean = re.sub(r'^(Kota|Kabupaten|Kab\.?|Kab)\s+', '', name, flags=re.IGNORECASE)
        return clean.strip()
            