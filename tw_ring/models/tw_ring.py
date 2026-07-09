# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwRing(models.Model):
    _name = "tw.ring"
    _description = "Master Ring"

    # 7: defaults methods

    # 8: fields
    name = fields.Char('Ring Name')

    active = fields.Boolean('Active?', default=True)

    # 9: relation fields

    # 10: constraints & sql constraints
    @api.constrains('name')
    def _check_name(self):
        for rec in self:
            if self.search([('name', '=', rec.name), ('id', '!=', rec.id)]):
                raise Warning(_("Ring Name sudah ada"))

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
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

    def action_ring_tree(self):
        domain = []
        list_view_id = self.env.ref('tw_ring.tw_ring_list_view').id
        search_view_id = self.env.ref('tw_ring.tw_ring_search_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Master Ring',
            'path': 'ring',
            'view_type': 'tree',
            'view_mode': 'list,form',
            'res_model': 'tw.ring',
            'domain': domain,
            'views': [(list_view_id, 'list')],
            'search_view_id': search_view_id,
            'context': {
                'search_default_fieldname': 1,
                'search_default_active': 1,
                'readonly_by_pass': 1
            },
        }

    # 14: private methods