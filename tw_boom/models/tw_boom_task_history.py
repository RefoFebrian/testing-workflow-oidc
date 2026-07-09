# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import traceback

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib


class TWBoomTaskHistory(models.Model):
    _name = "tw.boom.task.history"
    _description = "TW Boom Task History"
    _order = "id desc"


    # 7: defaults methods
    def get_default_datetime(self):
        return datetime.now()

    # 8: fields
    name = fields.Char('Name')
    no_transaction = fields.Char('No Transaksi')
    source_transaction = fields.Char('Sumber Transaksi')
    cron_name = fields.Char('Cron Name', help='Name of the scheduled action')
    method_name = fields.Char('Method Name', help='Method that was executed')

    error_message = fields.Text('Error Message')
    error_traceback = fields.Text('Error Traceback')

    state = fields.Selection([
        ('error','Error'),
        ('success','Success'),
    ], string='Status')

    execution_time = fields.Datetime('Execution Time', default=lambda self: fields.Datetime.now())
    
    # 9: relation fields
    category_id = fields.Many2one('tw.boom.category', 'Kategori')


    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        datetime_now = fields.Datetime.now()
        
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].get_sequence_code_with_date('HIST', 'BOOM', datetime_now)

        return super(TWBoomTaskHistory, self).create(vals_list)

    # 13: action methods
    
    # 14: private methods
    @api.model
    def log_error(self, error_data):
        """
        Helper method to create error log
        
        :param error_data: dict with keys:
            - no_transaction (optional)
            - source_transaction (optional)
            - error_message (required)
            - error_traceback (optional)
            - category_id (optional)
            - cron_name (optional)
            - method_name (optional)
        """
        vals = {
            'state': 'error',
            'no_transaction': error_data.get('no_transaction'),
            'source_transaction': error_data.get('source_transaction'),
            'error_message': error_data.get('error_message', 'Unknown error'),
            'error_traceback': error_data.get('error_traceback'),
            'category_id': error_data.get('category_id'),
            'cron_name': error_data.get('cron_name'),
            'method_name': error_data.get('method_name'),
        }
        return self.sudo().create(vals)

    @api.model
    def log_success(self, success_data):
        """
        Helper method to create success log
        
        :param success_data: dict with keys similar to log_error
        """
        vals = {
            'state': 'success',
            'no_transaction': success_data.get('no_transaction'),
            'source_transaction': success_data.get('source_transaction'),
            'category_id': success_data.get('category_id'),
            'cron_name': success_data.get('cron_name'),
            'method_name': success_data.get('method_name'),
        }
        return self.sudo().create(vals)