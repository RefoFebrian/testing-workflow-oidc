# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TWMappingTitikKeramaian(models.Model):
    _name = "tw.mapping.titik.keramaian"
    _description = "Mapping Titik Keramaian"
    _rec_name = 'activity_point_id'
    _rec_names_search = ['activity_point_id','code']

    # 7: defaults methods
    def _get_default_branch(self):
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1:
            return company_ids[0].id
        return False  

    # 8: fields
    code = fields.Char(string='Code', compute='_compute_code', store=True)
    distance = fields.Integer(string='Distance (km)')
    estimated_travel_time = fields.Integer('Waktu (menit)')

    # 9: relation fields
    company_id = fields.Many2one("res.company", string="Branch", required=True)
    activity_point_id = fields.Many2one('tw.titik.keramaian', 'Titik Keramaian')
    ring_id = fields.Many2one(comodel_name='tw.ring', string='Ring', compute='_compute_ring_id', store=True)
    profile_consumen_ids = fields.Many2many(
        'tw.selection', 
        'tw_mapping_activity_consumen_rel', 
        'mapping_activity_id', 
        'consumen_id', "Profile Consumen", domain=[('type', '=', 'ProfileConsumen')], context={'default_type': 'ProfileConsumen'})
    competitor_ids = fields.Many2many(
        'tw.selection', 
        'tw_mapping_activity_competitor_rel', 
        'mapping_activity_id', 
        'competitor_id', "Competitor", domain=[('type', '=', 'DealerCompetitor')], context={'default_type': 'DealerCompetitor'})
    available_activity_point_ids = fields.Many2many('tw.titik.keramaian', string='Available Activity Points', compute='_compute_available_activity_points')

    # 10: constraints & sql constraints
    @api.constrains('company_id', 'activity_point_id')
    def _check_branch_activity_point_unique(self):
        for record in self:
            count = self.search_count([
                ('company_id', '=', record.company_id.id),
                ('activity_point_id', '=', record.activity_point_id.id),
                ('id', '!=', record.id)
            ])
            if count > 0:
                raise Warning(_(f"Mapping dengan dealer ['{record.company_id.name}'] dan titik keramaian ['{record.activity_point_id.description}'] tidak boleh sama !"))

    # 11: compute/depends & on change methods
    @api.depends('company_id')
    def _compute_available_activity_points(self):
        for record in self:
            record.available_activity_point_ids = self.env['tw.titik.keramaian'].search([('active', '=', True)])

    @api.depends('company_id', 'activity_point_id')
    def _compute_code(self):
        for record in self:
            if record.company_id and record.activity_point_id:
                record.code = f"{record.company_id.code}|{record.activity_point_id.description}"
            else:
                record.code = record.activity_point_id.description or ''

    @api.depends('activity_point_id')
    def _compute_ring_id(self):
        for record in self:
            record.ring_id = record.activity_point_id.ring_id

    # 12: override methods

    def action_tw_mapping_titik_keramaian_list(self):
        domain = []
        list_view_id = self.env.ref('tw_activity_atl_btl.view_tw_mapping_titik_keramaian_list').id
        form_view_id = self.env.ref('tw_activity_atl_btl.view_tw_mapping_titik_keramaian_form').id
        search_view_id = self.env.ref('tw_activity_atl_btl.view_tw_mapping_titik_keramaian_search').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Mapping Titik Keramaian',
            'path': 'mapping-titik-keramaian',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.mapping.titik.keramaian',
            'domain': domain,
            'views': [(list_view_id, 'list'), (form_view_id, 'form')],
            'search_view_id': search_view_id,
            'context': {
            },
        }

    # 13: action methods

    # 14: private methods
    def name_get(self):
        res = []
        for rec in self:
            name = rec.activity_point_id.name
            res.append((rec.id, name))
        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []

        if name:
            if '|' in name:
                parts = name.split('|', 1)  # split max once
                branch_code = parts[0].strip()
                titik_name = parts[1].strip()

                domain = [
                    ('company_id.code', '=', branch_code),
                    '|',
                    ('activity_point_id.name', 'ilike', titik_name),
                    ('activity_point_id.description', 'ilike', titik_name),
                ]
                records = self.search(domain + args, limit=limit)
                if records:
                    return records.name_get()

            # Fallback: normal UI search
            domain = [
                '|',
                ('activity_point_id.description', operator, name),
                ('activity_point_id.name', operator, name),
            ]
            records = self.search(domain + args, limit=limit)
            return records.name_get()

        return super().name_search(name, args=args, operator=operator, limit=limit)

    def load(self, fields, data):
        """
        Auto-create missing records during import:
        - tw.selection (profile_consumen_ids, competitor_ids)
        - tw.titik.keramaian (activity_point_id)

        Only runs during import.
        """

        ctx = dict(self.env.context)
        Selection = self.env['tw.selection']

        # Configuration for Many2many fields (tw.selection)
        field_type_map = {
            'profile_consumen_ids': 'ProfileConsumen',
            'competitor_ids': 'DealerCompetitor',
        }

        # Handle Many2many fields (tw.selection)
        for field_name, selection_type in field_type_map.items():
            if field_name not in fields:
                continue

            col_idx = fields.index(field_name)
            ctx['selection_type'] = selection_type
            SelectionCtx = Selection.with_context(ctx)

            for row in data:
                cell = row[col_idx]
                if not cell:
                    continue

                names = [x.strip() for x in cell.split(',') if x.strip()]

                for name in names:
                    exists = SelectionCtx.search([
                        ('name', '=', name),
                        ('type', '=', selection_type),
                    ], limit=1)

                    if not exists:
                        SelectionCtx.create({
                            'name': name,
                            'type': selection_type,
                        })

        return super(
            TWMappingTitikKeramaian,
            self.with_context(ctx)
        ).load(fields, data)
