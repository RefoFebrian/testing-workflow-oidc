from odoo import models, fields, api
import urllib
from odoo.exceptions import UserError as Warning

class TWStockPickingDeliveryGmapsWizard(models.TransientModel):
    _name = "tw.stock.picking.delivery.gmaps.wizard"
    _description = "Google Maps Wizard for Outstanding Delivery"

    def _get_default_country(self):
        return self.env.ref('base.id').id

    partner_id = fields.Many2one('res.partner', string="Customer")
    company_id = fields.Many2one('res.company', string="Branch")
    cust_address = fields.Char()
    cust_street = fields.Char()
    cust_sub_district = fields.Many2one('res.sub.district', string="Cust Kelurahan", domain="[('district_id', '=', cust_district)]")
    cust_district = fields.Many2one('res.district', string="Cust Kecamatan", domain="[('city_id', '=', cust_city)]")
    cust_city = fields.Many2one('res.city', string="Cust Kabupaten", domain="[('state_id', '=', cust_state)]")
    cust_state = fields.Many2one('res.country.state', string="Cust Provinsi", domain="[('country_id', '=', cust_country)]")
    cust_country = fields.Many2one('res.country', string="Cust Negara", default=_get_default_country)
    cust_zip = fields.Char()
    company_address = fields.Char()
    company_street = fields.Char()
    company_sub_district = fields.Many2one('res.sub.district', string="Company Kelurahan", domain="[('district_id', '=', company_district)]")
    company_district = fields.Many2one('res.district', string="Company Kecamatan", domain="[('city_id', '=', company_city)]")
    company_city = fields.Many2one('res.city', string="Company Kabupaten", domain="[('state_id', '=', company_state)]")
    company_state = fields.Many2one('res.country.state', string="Company Provinsi", domain="[('country_id', '=', company_country)]")
    company_country = fields.Many2one('res.country', string="Company Negara", default=_get_default_country)
    company_zip = fields.Char()
    map_html = fields.Html(sanitize=False, readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        partner = None
        company = None
        partner_id = self.env.context.get('default_partner_id')
        company_id = self.env.context.get('default_company_id')
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
        if company_id:
            company = self.env['res.company'].browse(company_id)

        # membuat cust address dan company address
        if partner and partner.street and partner.sub_district_id and partner.district_id and partner.city_id and partner.state_id and partner.zip:
            cust_address = f"{partner.street},{partner.sub_district_id.name},{partner.district_id.name},{partner.city_id.name},{partner.state_id.name},{partner.zip}"
        else:
            cust_address = f"{partner.street},{partner.sub_district_id.name},{partner.district_id.name},{partner.city_id.name},{partner.state_id.name}"
        
        if company and company.street and company.sub_district_id and company.district_id and company.city_id and company.state_id and company.zip:
            company_address = f"{company.street},{company.sub_district_id.name},{company.district_id.name},{company.city_id.name},{company.state_id.name},{company.zip}"
        else:
            company_address = f"{company.street},{company.sub_district_id.name},{company.district_id.name},{company.city_id.name},{company.state_id.name}"

        if cust_address and company_address:
            res["cust_address"] = cust_address
            res["company_address"] = company_address
            res["map_html"] = self._make_map_html(cust_address,company_address)

        if partner:
            res["cust_street"] = partner.street
            res["cust_sub_district"] = partner.sub_district_id.id
            res["cust_district"] = partner.district_id.id
            res["cust_city"] = partner.city_id.id
            res["cust_state"] = partner.state_id.id
            res["cust_zip"] = partner.zip
        
        if company:
            res["company_street"] = company.street
            res["company_sub_district"] = company.sub_district_id.id
            res["company_district"] = company.district_id.id
            res["company_city"] = company.city_id.id
            res["company_state"] = company.state_id.id
            res["company_zip"] = company.zip

        return res
    
    @api.onchange('cust_sub_district')
    def _onchange_cust_sub_district(self):
        if self.cust_sub_district and (not self._origin or self.cust_sub_district != self._origin.cust_sub_district):
            self.cust_zip = self.cust_sub_district.zip_code

    def _make_map_html(self, cust_address,company_address):
        if not cust_address or not company_address:
            return "<p>Perhatian.\n Masukkan alamat lalu tekan Update Map</p>"
        origin = urllib.parse.quote(company_address)
        destination = urllib.parse.quote(cust_address)
        return f"""
            <iframe
                width="100%"
                height="380"
                style="border:0; border-radius:10px;"
                loading="lazy"
                src="https://maps.google.com/maps?saddr={origin}&daddr={destination}&output=embed"
                allowfullscreen>
            </iframe>
        """

    def action_update_map(self):
        for wizard in self:
            wizard.map_html = wizard._make_map_html(wizard.cust_address,wizard.company_address)
            
            partner_id = self.env.context.get("default_partner_id")
            company_id = self.env.context.get("default_company_id")

            partner = self.env["res.partner"].browse(partner_id) if partner_id else False
            company = self.env["res.company"].browse(company_id) if company_id else False
            if partner:
                partner_vals = {}
                if wizard.cust_street:
                    partner_vals['street'] = wizard.cust_street
                if wizard.cust_sub_district:
                    partner_vals['sub_district_id'] = wizard.cust_sub_district.id
                if wizard.cust_district:
                    partner_vals['district_id'] = wizard.cust_district.id
                if wizard.cust_city:
                    partner_vals['city_id'] = wizard.cust_city.id
                if wizard.cust_state:
                    partner_vals['state_id'] = wizard.cust_state.id
                if wizard.cust_zip:
                    partner_vals['zip'] = wizard.cust_zip

                if partner_vals:
                    partner.write(partner_vals)

            if company:
                company_vals = {}

                if wizard.company_street:
                    company_vals['street'] = wizard.company_street
                if wizard.company_sub_district:
                    company_vals['sub_district_id'] = wizard.company_sub_district.id
                if wizard.company_district:
                    company_vals['district_id'] = wizard.company_district.id
                if wizard.company_city:
                    company_vals['city_id'] = wizard.company_city.id
                if wizard.company_state:
                    company_vals['state_id'] = wizard.company_state.id
                if wizard.company_zip:
                    company_vals['zip'] = wizard.company_zip

                if company_vals:
                    company.write(company_vals)

            # membuat cust address dan company address
            if wizard.cust_zip:
                cust_address = f"{wizard.cust_street},{wizard.cust_sub_district.name},{wizard.cust_district.name},{wizard.cust_city.name},{wizard.cust_state.name},{wizard.cust_zip}"
            else:
                cust_address = f"{wizard.cust_street},{wizard.cust_sub_district.name},{wizard.cust_district.name},{wizard.cust_city.name},{wizard.cust_state.name}"
            
            if wizard.company_zip:
                company_address = f"{wizard.company_street},{wizard.company_sub_district.name},{wizard.company_district.name},{wizard.company_city.name},{wizard.company_state.name},{wizard.company_zip}"
            else:
                company_address = f"{wizard.company_street},{wizard.company_sub_district.name},{wizard.company_district.name},{wizard.company_city.name},{wizard.company_state.name}"
            
            self.cust_address = cust_address
            self.company_address = company_address
            self.map_html = self._make_map_html(cust_address,company_address)
        return{
            'name': "Lokasi Pengiriman",
            "view_mode" : "form",
            "res_model" : "tw.stock.picking.delivery.gmaps.wizard",
            "res_id" : self.id,
            "type" : "ir.actions.act_window",
            "target" : "new"
        }

