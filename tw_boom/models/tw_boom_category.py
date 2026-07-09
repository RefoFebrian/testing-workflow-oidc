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

class TWBoomCategory(models.Model):
      _name = "tw.boom.category"
      _description = "TW Boom Kategori"
      _order = "id desc"

      # 7: defaults methods
      def _get_default_date(self):
         return date.today().strftime("%Y-%m-%d")

      # 8: fields
      name = fields.Char('Name')

      active = fields.Boolean('Active', default=True)

      due_date_day = fields.Integer('Due Date Day')
      due_date_hour = fields.Integer('Due Date Hour')

      periode = fields.Selection([
         ('daily', 'Daily'),
         ('weekly', 'Weekly'),
         ('monthly', 'Monthly'),
      ], string='Periode')

      escalation_periode = fields.Selection([
         ('hour', 'Hour'),
         ('day', 'Day'),
         ('week', 'Week'),
         ('month', 'Month'),
      ], string='Periode Eskalasi')

      classification = fields.Selection([
         ('resiko', 'Resiko'),
         ('report', 'Report'),
         ('support', 'Support'),
      ], string='Klasifikasi')

      dealer_category = fields.Selection([
         ('H123', 'H123'),
         ('H23', 'H23'),
         ('H1','H1'),
      ], string='Kategori Dealer')

      # Field Notification Dashboard BOOM
      # TODO: 11/20/2025 Dashboard boom is still TBD (to be discussed)
      # notif_date = fields.Selection(selection=[('h+','H+'),('h-','H-')],  string='Notification Date',  help='')
      # notif_date_day= fields.Integer(string='Notification Day',  help='')
      # notif_date_hour = fields.Integer(string='Notification Hour',  help='')
      # is_manual_confirm = fields.Boolean(string='Manual Confirm', default=False, help="This field is used to determine if the confirmation is done manually or automatically for confirmation box of dashboard")


      # 9: relation fields
      main_category_id = fields.Many2one('tw.boom.main.category', 'Main Kategori')
      sub_category_id = fields.Many2one('tw.boom.sub.category', 'Sub Kategori')
      job_id = fields.Many2one('hr.job', 'Job PIC')
      job_delegation_id = fields.Many2one('hr.job', 'Job Delegasi PIC')

      # 10: constraints & sql constraints

      # 11: compute/depends & on change methods

      # 12: override methods

      # 13: action methods

      # 14: private methods