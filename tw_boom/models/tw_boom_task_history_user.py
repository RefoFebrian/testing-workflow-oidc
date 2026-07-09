# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TWBoomTaskHistory(models.Model):
    _name = "tw.boom.task.history.user"
    _description = "TW Boom Task History User"


    #7: defaults methods
    def _get_default_date(self):
        return self.env['res.company'].get_default_date()
    def _get_state_value(self):
        # Mengambil value yang sesuai dengan key di state
        selection = self._fields.get('state') and self._fields['state'].selection
        return dict(selection).get(self.state, self.state) if selection else self.state

    # 8: fields
    assign_date = fields.Datetime(string='Tgl Assign', help='')

    # 9: relation fields
    task_id = fields.Many2one('tw.boom.task', 'Task')
    employee_id = fields.Many2one('hr.employee', 'PIC')
    job_id = fields.Many2one('hr.job', 'PIC Job')
    company_id = fields.Many2one('res.company', 'Branch')
    reason = fields.Char(string='Alasan', help='')
    
    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    
    # 12: override methods
    
    # 13: action methods
    
    # 14: private methods