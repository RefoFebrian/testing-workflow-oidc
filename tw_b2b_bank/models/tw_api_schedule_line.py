# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class ApiScheduleLine(models.Model):
    _name = "tw.api.schedule.line"
    _description = 'API Schedule Lines'
    _order = "hour ASC, minute ASC"

    # 7: defaults methods

    # 8: fields
    hour = fields.Char(string='Jam')
    minute = fields.Char(string='Menit')

    # 9: relation fields
    schedule_id = fields.Many2one(comodel_name='tw.api.schedule', string='Schedule ID', ondelete='cascade')

    # 10: constraints & sql constraints
    _sql_constraints = [('hour_minute_unique', 'unique(hour, minute, schedule_id)', 'Jam Menit tidak boleh duplikat !')]

    @api.constrains('hour')
    def _constrains_hour(self):
        for line in self:
            if not line.hour.isdigit():
                raise Warning('Jam tidak boleh mengandung karakter !')
            if not line.minute.isdigit():
                raise Warning('Menit tidak boleh mengandung karakter !')

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods