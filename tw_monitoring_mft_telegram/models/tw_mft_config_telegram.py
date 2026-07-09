# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
from datetime import datetime

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _

# 4: imports from odoo modules
from odoo.exceptions import UserError

# 5: local imports

# 6: Import of unknown third party lib

_logger = logging.getLogger(__name__)


class TwMftConfigTelegram(models.Model):
    """Extend tw.mft.config with Telegram notification capabilities."""
    
    _inherit = "tw.mft.config"

    # 8: fields
    telegram_enabled = fields.Boolean(
        string='Enable Telegram Notification',
        default=False,
        help="Aktifkan notifikasi Telegram untuk konfigurasi ini"
    )
    telegram_notify_on_error = fields.Boolean(
        string='Notify on Error',
        default=True,
        help="Kirim notifikasi jika ada file dengan error (belum 100%)"
    )
    telegram_notify_on_success = fields.Boolean(
        string='Notify on All Success',
        default=False,
        help="Kirim notifikasi jika semua file sudah 100% success"
    )
    telegram_last_notification_date = fields.Datetime(
        string='Last Notification Date',
        readonly=True
    )

    # 9: relation fields
    telegram_user_ids = fields.Many2many(
        'res.users',
        'tw_mft_config_telegram_user_rel',
        'config_id',
        'user_id',
        string='Telegram Recipients',
        domain=[('telegram_chat_id', '!=', False)],
        help="User yang akan menerima notifikasi Telegram"
    )

    # 13: action methods
    def action_send_telegram_notification(self):
        """Manual trigger to send Telegram notification."""
        self.ensure_one()
        
        if not self.telegram_enabled:
            raise UserError(_("Telegram notification tidak diaktifkan untuk konfigurasi ini!"))
        
        if not self.telegram_user_ids:
            raise UserError(_("Tidak ada penerima Telegram yang dikonfigurasi!"))
        
        return self._send_mft_telegram_notification()
    
    def _send_mft_telegram_notification(self):
        """
        Send Telegram notification for this MFT config.
        Returns notification result.
        """
        self.ensure_one()
        
        # Get today's logs for this config
        today = datetime.now().date()
        logs = self.env['tw.mft.log'].search([
            ('config_id', '=', self.id),
            ('fetch_date', '>=', today.strftime('%Y-%m-%d')),
        ])
        
        if not logs:
            _logger.info(f"No logs found for {self.name} today, skipping notification")
            return False
        
        # Calculate statistics
        total_logs = len(logs)
        success_logs = logs.filtered(lambda l: l.status == 100)
        pending_logs = logs.filtered(lambda l: l.status < 100)
        
        count_success = len(success_logs)
        count_pending = len(pending_logs)
        
        # Check if notification should be sent
        should_notify = False
        notification_type = ''
        
        if self.telegram_notify_on_error and count_pending > 0:
            should_notify = True
            notification_type = 'error'
        elif self.telegram_notify_on_success and count_pending == 0:
            should_notify = True
            notification_type = 'success'
        
        if not should_notify:
            _logger.info(f"No notification needed for {self.name}")
            return False
        
        # Build message
        message = self._build_telegram_message(
            total_logs, count_success, count_pending, pending_logs
        )
        
        # Build URL button - filter by pending files for this config
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        # URL with search_default to show only pending files
        url = (
            f"{base_url}/web#model=tw.mft.log&view_type=list"
            f"&action=tw_monitoring_mft.tw_mft_log_action"
            f"&search_default_filter_incomplete=1"
            f"&search_default_config_id={self.id}"
        )
        
        button = [[{
            "text": "📋 Lihat Detail Pending",
            "url": url
        }]]
        
        # Send to all recipients
        sent_count = 0
        for user in self.telegram_user_ids:
            if user.telegram_chat_id:
                try:
                    user.send_telegram_message(message, button_params=button)
                    sent_count += 1
                except Exception as e:
                    _logger.error(f"Failed to send Telegram to {user.name}: {e}")
        
        # Update last notification date
        self.write({'telegram_last_notification_date': fields.Datetime.now()})
        
        _logger.info(f"Telegram notification sent to {sent_count} users for {self.name}")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Telegram Sent'),
                'message': _('Notifikasi dikirim ke %d user.') % sent_count,
                'sticky': False,
                'type': 'success',
            }
        }
    
    def _build_telegram_message(self, total_logs, count_success, count_pending, pending_logs):
        """Build formatted Telegram message."""
        from datetime import timedelta
        
        # Date range based on config
        today = datetime.now().date()
        date_from = today - timedelta(days=self.date_range_days)
        
        if self.date_range_days == 0:
            date_str = today.strftime('%d-%b-%Y')
        else:
            date_str = f"{date_from.strftime('%d-%b-%Y')} - {today.strftime('%d-%b-%Y')}"
        
        # Header
        message = f"📊 MFT Monitoring Report\n"
        message += f"━━━━━━━━━━━━━━━\n"
        message += f"📁 File Type: {self.filetype}\n"
        message += f"📅 Date: {date_str}\n\n"
        
        # Summary
        message += f"✅ Success (100%): {count_success}\n"
        message += f"⚠️ Pending: {count_pending}\n"
        message += f"📈 Total: {total_logs}\n"
        
        # Detail pending (max 10)
        if pending_logs:
            message += f"\n*Detail Pending:*\n"
            for log in pending_logs[:10]:
                message += f"• {log.filename} - {log.status:.0f}%\n"
            
            if len(pending_logs) > 10:
                message += f"... dan {len(pending_logs) - 10} file lainnya\n"
        
        # Closing text
        message += f"\nSilahkan lihat lebih detail dengan klik button berikut"
        
        return message
    
    # 14: private methods
    @api.model
    def _cron_send_mft_telegram_notification(self):
        """
        Scheduled action to send Telegram notifications for all active configs.
        """
        configs = self.search([
            ('active', '=', True),
            ('telegram_enabled', '=', True),
        ])
        
        for config in configs:
            if config.telegram_user_ids:
                try:
                    config._send_mft_telegram_notification()
                except Exception as e:
                    _logger.error(f"Telegram notification failed for {config.name}: {e}")
                    continue
