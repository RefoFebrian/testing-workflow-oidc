# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging

# 2: import of known third party lib
from datetime import datetime, timedelta

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

_logger = logging.getLogger(__name__)


class TwCronLog(models.Model):
    _name = "tw.cron.log"
    _description = "Cron Error Log"

    # 7: defaults methods

    # 8: fields
    name = fields.Char(string='Log Reference', readonly=True, copy=False,default=lambda self: _('New'))
    active = fields.Boolean(string='Active', default=True)
    log_time = fields.Datetime(string='Log Time', default=fields.Datetime.now, readonly=True,index=True)
    method_name = fields.Char(string='Method', readonly=True, help="Method/code yang dijalankan oleh cron")
    error_message = fields.Text(string='Error Message', readonly=True, help="Pesan error singkat")
    error_detail = fields.Text(string='Error Detail (Traceback)', readonly=True, help="Full traceback dari error")

    # 9: relation fields   
    cron_id = fields.Many2one('ir.cron', string='Scheduled Action', required=True, ondelete='cascade',index=True)
    model_id = fields.Many2one('ir.model', string='Model', readonly=True, ondelete='set null', help="Model yang dipanggil oleh cron")

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        """Override create untuk generate sequence name."""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('tw.cron.log') or _('New')
        return super().create(vals_list)

    # 13: action methods

    # 14: private methods
    def _get_duplicate_delay_hours(self):
        """Get delay time (in hours) from system parameter."""
        delay = self.env['ir.config_parameter'].sudo().get_param(
            'tw_cron_log.duplicate_delay_hours', 
            default='1'
        )
        try:
            return int(delay)
        except (ValueError, TypeError):
            return 1

    @api.model
    def _check_duplicate_log(self, cron_id, error_message):
        """
        Check apakah ada log duplikat dalam waktu delay.
        
        :param cron_id: ID dari ir.cron
        :param error_message: Pesan error
        :return: True jika duplikat ditemukan, False jika tidak
        """
        delay_hours = self._get_duplicate_delay_hours()
        if delay_hours <= 0:
            return False
        
        threshold_time = datetime.now() - timedelta(hours=delay_hours)
        
        duplicate = self.sudo().search([
            ('cron_id', '=', cron_id),
            ('error_message', '=', error_message),
            ('log_time', '>=', threshold_time),
        ], limit=1)
        
        return bool(duplicate)

    @api.model
    def create_log(self, cron_id, model_id, method_name, error_message, error_detail):
        """
        Create log entry jika tidak duplikat.
        
        :param cron_id: ID dari ir.cron
        :param model_id: ID dari ir.model
        :param method_name: Nama method/code yang dijalankan
        :param error_message: Pesan error singkat
        :param error_detail: Full traceback
        :return: tw.cron.log record atau False jika duplikat
        """
        if self._check_duplicate_log(cron_id, error_message):
            return False
        
        return self.sudo().create({
            'cron_id': cron_id,
            'model_id': model_id,
            'method_name': method_name,
            'error_message': error_message,
            'error_detail': error_detail,
            'log_time': fields.Datetime.now(),
        })
    
    def _set_archived(self, archived=True):
        """
        Archive atau unarchive log records.
        Dapat dipanggil oleh model lain untuk mengatur status aktif log.
        
        :param archived: True untuk archive (inactive), False untuk unarchive (active)
        :return: Recordset yang diupdate
        
        Contoh pemanggilan dari model lain:
            # Archive semua log dari cron tertentu
            logs = self.env['tw.cron.log'].search([('cron_id', '=', 5)])
            logs._set_archived(archived=True)
            
            # Unarchive
            logs._set_archived(archived=False)
        """
        return self.write({'active': not archived})
    
    @api.model
    def _archive_logs_by_cron(self, cron_id, archived=True):
        """
        Archive atau unarchive semua log dari cron tertentu.
        
        :param cron_id: ID dari ir.cron
        :param archived: True untuk archive, False untuk unarchive
        :return: Recordset yang diupdate
        """
        logs = self.search([('cron_id', '=', cron_id)])
        if logs:
            logs._set_archived(archived=archived)
            _logger.info('Archived %s logs for cron_id %s', len(logs), cron_id)
        return logs
