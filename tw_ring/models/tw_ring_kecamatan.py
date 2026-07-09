# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwRingKecamatan(models.Model):
    _name = "tw.ring.kecamatan"
    _description = "Master Ring Kecamatan"

    # 7: defaults methods
    def _get_default_company(self):
        company_ids = False
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1:
            return company_ids[0].id
        return False

    # 8: fields
    name = fields.Char('Ring Kecamatan')

    # 9: relation fields
    ring_kecamatan_line_ids = fields.One2many('tw.ring.kecamatan.line', 'ring_kecamatan_id')
    company_id = fields.Many2one(comodel_name='res.company', default=_get_default_company, string='Branch', domain="[('parent_id','!=',False)]")

    # 10: constraints & sql constraints
    @api.constrains('ring_kecamatan_line_ids')
    def _check_ring_kecamatan_line(self):
        if len(self.ring_kecamatan_line_ids) < 1:
            raise ValidationError(_('Ring Kecamatan Detail harus diisi.'))
        
    @api.constrains('company_id')
    def _check_company_id(self):
        if not self.company_id:
            raise ValidationError(_('Branch harus diisi.'))
        # Ensure company_id is unique
        for rec in self:
            domain = [
                ('company_id', '=', rec.company_id.id),
                ('id', '!=', rec.id)
            ]
            if self.search_count(domain):
                raise ValidationError(_('Branch harus unik per Ring Kecamatan.'))

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_ring_kecamatan_tree(self):
        domain = []
        list_view_id = self.env.ref('tw_ring.tw_ring_kecamatan_list_view').id
        form_view_id = self.env.ref('tw_ring.tw_ring_kecamatan_form_view').id
        search_view_id = self.env.ref('tw_ring.tw_ring_kecamatan_search_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ring Kecamatan',
            'path': 'ring-kecamatan',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.ring.kecamatan',
            'domain': domain,
            'views': [(list_view_id, 'list'), (form_view_id, 'form')],
            'search_view_id': search_view_id,
            'context': {
                'search_default_fieldname': 1,
                'readonly_by_pass': 1
            },
        }

    # 14: private methods

