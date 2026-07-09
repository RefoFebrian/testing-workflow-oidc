# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class Selection(models.Model):
    _name = "tw.selection"
    _description = 'Base Selection List'
    _rec_names_search = ['name', 'value','code']
    _order = 'sequence, id'

    # 7: defaults methods

    # 8: fields
    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(string='Name')
    type = fields.Char(string='Type', index=True)
    value = fields.Char(string='Value')
    internal_value = fields.Char('Internal Value')
    code = fields.Char(string='Code', compute='_compute_selection_code', store=True)
    context = fields.Text(string='Context')
    
    active = fields.Boolean(string='Active', default=True)

    # 9: relation fields

    # 10: constraints & sql constraints
    _sql_constraints = [('tipe_value_uniq', 'unique(type, value)', 'Value untuk Type yang sama tidak boleh ada yang sama.')]

    # 11: compute/depends & on change methods
    @api.depends('type', 'value')
    def _compute_selection_code(self):
        for record in self:
            if record.type:
                record.code = f"{record.type}|{record.value}"
            else:
                record.code = record.name or ''

    @api.onchange('name')
    def _onchange_name(self):
        if self.name:
            self.value = "".join(self.name.title().split())
    
    # 12: override methods
    def context_get(self, key, default=False):
        """Safely parse JSON context and return the value for the given key."""
        self.ensure_one()
        if not self.context:
            return default
        try:
            import json
            data = json.loads(self.context)
            return data.get(key, default)
        except (ValueError, TypeError):
            return default

    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            name = vals.get('name')
            if ('value' not in vals or vals['value'] in (None, '')) and name:
                vals['value'] = name.lower()

        return super(Selection, self).create(vals_list)

    # 13: action methods
    def get_selection(self, type, value=False):
        # Jika ingin mendapatkan selection berdasarkan value juga, maka kirimkan parameter value
        params = [('type', '=', type),]
        if value:
            params.append(('value', '=', value))
        selection_obj = self.suspend_security().search(params)
        return selection_obj
    
    def get_option_list(self, type):
        return [(select.value, select.name) for select in self.search([('type', '=', type)])]

    def get_division(self,trx):
        if not trx:
            raise Warning('Silahkan kirim trx !')
        division = trx.division if 'division' in trx.read()[0] else 'Umum'
        return division

    def get_division_options(self, name=None):
        return self.get_division_options_list([name] if name else False)
    
    def get_division_options_list(self, name=[]):
        domain = [('type','=','Division')]
        if name:
            domain.append(('name', 'in', name))
        
        return [(select.value, select.name) for select in self.search(domain)]
    
    def validate_selection(self, id, type):
        if id:
            questionnaire = self.search([('id', '=', id), ('type', '=', type)])
            if not questionnaire:
                raise Warning(_(f"The ID ({id}, {questionnaire.name}) you provided does not match the selection type {type}"))
            return questionnaire.id