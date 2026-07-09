# 1: imports of python lib

# 2: import of known third party lib
import re
try:
    from haversine import haversine, Unit
    HAVERSINE_AVAILABLE = True
except ImportError:
    HAVERSINE_AVAILABLE = False

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwTitikKeramaian(models.Model):
    _name = "tw.titik.keramaian"
    _description = "Master Titik Keramaian"
    _rec_name = 'description'

    # 7: defaults methods@api.model
    def _default_state_id(self): 
        param_state_name = self.env['ir.config_parameter'].sudo().get_param('param_state.default_state_name')
        return self.env['res.country.state'].suspend_security().search([('name', '=', param_state_name)], limit=1).id

    # 8: fields
    name = fields.Char('Titik Keramaian')
    responsibility = fields.Char(string='Responsibility', help="Diisi dengan Job PIC yang bertanggung jawab untuk titik keramaian ini\nNote: hanya diperuntikkan sebagai note saja untuk saat ini ")
    description = fields.Char(string='Description')
    street = fields.Char(string='Alamat')
    rt = fields.Char(string='RT')
    rw = fields.Char(string='RW')
    lat = fields.Char('Latitude')
    long = fields.Char('Longitude')
    map_location = fields.Json(string='Map Location')

    max_qty_unit_display = fields.Integer(string='Max Qty Unit Display')
    target = fields.Integer(string='Target')

    active = fields.Boolean('Active', default=True)

    # 9: relation fields
    category_id = fields.Many2one(comodel_name='tw.selection', string='Kategori', domain=[('type', '=', 'TitikKeramaianCategory')])
    ring_id = fields.Many2one(comodel_name='tw.ring', string='Ring', domain=[('active', '=', True)])
    
    state_id = fields.Many2one('res.country.state', 'Provinsi', default=_default_state_id)
    city_id = fields.Many2one('res.city', 'Kabupaten', domain="[('state_id', '=', state_id)]")
    district_id = fields.Many2one(comodel_name='res.district', string='Kecamatan', domain="[('city_id', '=', city_id)]")
    sub_district_id = fields.Many2one(comodel_name='res.sub.district', string='Kelurahan', domain="[('district_id', '=', district_id)]")
    
    # 10: constraints & sql constraints
    @api.constrains('description')
    def _check_name_unique(self):
        for record in self:
            count = self.search_count([
                ('description', '=', record.description),
                ('id', '!=', record.id)
            ])
            if count > 0:
                raise Warning(_(f"Titik Keramaian dengan nama ['{record.description}'] tidak boleh sama !"))
            
    @api.constrains('lat', 'long')
    def _check_distance_lat_long(self):
        for record in self:
            if not record.lat or not record.long:
                continue  # Skip check if lat/long is empty

            # Get all other records excluding current one
            other_records = self.search([
                ('id', '!=', record.id),
                ('lat', '!=', False),
                ('long', '!=', False),
            ])

            for other in other_records:
                point1 = (float(record.lat), float(record.long))
                point2 = (float(other.lat), float(other.long))
                if HAVERSINE_AVAILABLE:
                    distance_m = haversine(point1, point2, unit=Unit.METERS)

                    if distance_m <= 200:
                        raise Warning(
                            f"Terdapat data dengan lokasi dalam radius 200 meter dari data ini (lat: {record.lat}, long: {record.long})."
                        )
                
    @api.constrains('lat')
    def check_lat(self):
        for record in self:
            if record.lat:
                # Check if the latitude is a valid decimal number
                if not re.match(r'^-?\d*\.?\d+$', record.lat):
                    raise Warning('Format koordinat latitude tidak valid. Harap isi dengan angka desimal !\ncontoh: -6.2001, 106.8167')
    
    @api.constrains('long')
    def check_long(self):
        for record in self:
            if record.long:
                if not re.match(r'^-?\d*\.?\d+$', record.long):
                    raise Warning('Format koordinat latitude tidak valid. Harap isi dengan angka desimal !\ncontoh: -6.2001, 106.8167')

    # 11: compute/depends & on change methods
    @api.onchange('state_id')
    def _onchange_province(self):
        if self.state_id:
            return {
                'domain': {'city_id': [('state_id', '=', self.state_id.id)]},
                'value': {'city_id': False}
            }
        return {
            'domain': {'city_id': [('state_id', '=', False)]},
            'value': {'city_id': False}
        }

    @api.onchange('city_id')
    def _onchange_city(self):
        if self.city_id:
            return {
                'domain': {'district_id': [('city_id', '=', self.city_id.id)]},
                'value': {'district_id': False}
            }
        return {
            'domain': {'district_id': [('city_id', '=', False)]},
            'value': {'district_id': False}
        }

    @api.onchange('district_id')
    def _onchange_kecamatan(self):
        if self.district_id:
            return {
                'domain': {'sub_district_id': [('district_id', '=', self.district_id.id)]},
                'value': {'sub_district_id': False}
            }
        return {
            'domain': {'sub_district_id': [('district_id', '=', False)]},
            'value': {'sub_district_id': False}
        }

    # 12: override methods
    @api.model
    def name_get(self):
        if self._context is None:
            self._context = {}
        res = []
        for record in self:
            a = record.name
            b = record.description 
            tit = "[%s] %s" % (a, b)
            res.append((record.id, tit))
        return res
    
    @api.model_create_multi
    def create(self, vals):
        if isinstance(vals, list): 
            vals = vals[0]

        sub_district_obj = self.env['res.sub.district'].search([('id', '=', vals['sub_district_id'])], limit=1)
        company_obj = self.env.company.parent_id if self.env.company.parent_id else self.env.company
        sequence_code = str(company_obj.code or 'TK')
        vals['name'] = self.env['ir.sequence'].get_sequence_code(sequence_code, str(sub_district_obj.code))
        return super(TwTitikKeramaian, self).create(vals)

    def write(self, vals):
        return super(TwTitikKeramaian, self).write(vals)

    # 13: action methods
    def action_titik_keramaian_tree(self):
        domain = []
        list_view_id = self.env.ref('tw_activity_atl_btl.tw_titik_keramaian_list_view').id
        form_view_id = self.env.ref('tw_activity_atl_btl.tw_titik_keramaian_form_view').id
        search_view_id = self.env.ref('tw_activity_atl_btl.tw_titik_keramaian_search_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Titik Keramaian',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.titik.keramaian',
            'domain': domain,
            'views': [(list_view_id, 'list'), (form_view_id, 'form')],
            'search_view_id': search_view_id,
            'context': {
                'search_default_fieldname': 1,
                'search_default_active': 1,
                'readonly_by_pass': 1
            },
        }
    
    def action_activate(self):
        for rec in self:
            rec.active = True

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    
    def action_deactivate(self):
        for rec in self:
            rec.active = False

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    # 14: private methods
    def load(self, fields, data):
        """
        CATATAN PENTING (IMPORT DATA):

        Method load() ini DIPANGGIL Odoo HANYA saat proses Import
        (CSV / Excel melalui menu Import), TIDAK dipanggil pada:
        - create()
        - write()
        - form view
        - business logic biasa

        Tujuan override load():
        ----------------------
        Saat import, Odoo akan mengisi field Many2one / Many2many
        dengan cara memanggil method name_search() pada comodel.

        Dalam kasus ini:
        - Field category_id mengarah ke model tw.selection
        - Data di tw.selection memiliki name yang sama
        tetapi dibedakan oleh field 'type'
        (contoh: "Perkampungan" ada di beberapa type)

        Masalah:
        --------
        Import TIDAK memperhatikan domain field dan context field,
        sehingga name_search() akan menemukan lebih dari satu data
        dan menyebabkan error:
            "Found multiple matches"

        Solusi:
        --------
        Context 'selection_type' disuntikkan di sini agar:
        - name_search() di model tw.selection tahu
        hanya boleh mencari data dengan type tertentu
        - Proses import menjadi deterministic (tidak ambigu)

        Context ini HANYA berlaku selama proses import,
        tidak mempengaruhi UI, create(), atau write().
        """
        ctx = dict(self.env.context)
        ctx['selection_type'] = 'TitikKeramaianCategory'
        return super(
            TwTitikKeramaian,
            self.with_context(ctx)
        ).load(fields, data)
