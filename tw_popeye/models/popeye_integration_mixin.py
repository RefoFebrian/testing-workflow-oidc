# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning
import requests
import json
import logging

_logger = logging.getLogger(__name__)

class PopeyeIntegrationMixin(models.AbstractModel):
    _name = "popeye.integration.mixin"
    _description = 'Mixin for Popeye Payment Gateway Integration'

    bulky_type = fields.Selection([
        ('transfer','Transfer'),
        ('cheque','Cheque'),
        ('auto_debit','Auto Debit'),
    ], string='Bulky Type', default='transfer')

    payment_reference_number = fields.Char('Popeye Doc Number', help='Reference Code from Popeye Payment System', readonly=True, copy=False)
    payment_payment_number = fields.Char('Popeye Payment Number', help='Payment Code from Popeye Payment System', readonly=True, copy=False)
    last_status_check = fields.Datetime('Last Status Check', readonly=True, copy=False)
    reason_reject = fields.Text(string='Reason for Rejection', readonly=True, copy=False)

    status_api_payment = fields.Selection([
        ('draft','Draft'),
        ('error','Error'),
        ('send','Sent'),
        ('waiting_request_approval','Waiting Request Approval'),
        ('verifying','Verifying'),
        ('on_approval','On Approval'),
        ('reject','Rejected'),
        ('queuing','Queuing'),
        ('paid','Paid'),
    ], string='Popeye Status', readonly=True, copy=False, default='draft')

    reject_uid = fields.Many2one('res.users', string='Rejected By', readonly=True, copy=False)
    reject_date = fields.Datetime(string='Rejected On', readonly=True, copy=False)
    
    send_uid = fields.Many2one('res.users', string='Sent By', readonly=True, copy=False)
    send_date = fields.Datetime(string='Sent On', readonly=True, copy=False)
    wfp_uid = fields.Many2one('res.users', string='WFP By', readonly=True, copy=False) 
    wfp_date = fields.Datetime(string='WFP On', readonly=True, copy=False)
    verifying_uid = fields.Many2one('res.users', string='Verifying By', readonly=True, copy=False)
    verifying_date = fields.Datetime(string='Verifying On', readonly=True, copy=False)
    on_approval_uid = fields.Many2one('res.users', string='On Approval By', readonly=True, copy=False)
    on_approval_date = fields.Datetime(string='On Approval On', readonly=True, copy=False)
    queuing_uid = fields.Many2one('res.users', string='Queuing By', readonly=True, copy=False)
    queuing_date = fields.Datetime(string='Queuing On', readonly=True, copy=False)
    paid_uid = fields.Many2one('res.users', string='Paid By', readonly=True, copy=False)
    paid_date = fields.Datetime(string='Paid On', readonly=True, copy=False)
    reject_api_uid = fields.Many2one('res.users', string='API Rejected By', readonly=True, copy=False)
    reject_api_date = fields.Datetime(string='API Rejected On', readonly=True, copy=False)

    # Cancel Popeye Fields
    cancel_popeye_uid = fields.Many2one('res.users', string='Cancelled Popeye By', readonly=True, copy=False)
    cancel_popeye_date = fields.Datetime(string='Cancelled Popeye On', readonly=True, copy=False)
    cancel_popeye_reason = fields.Text(string='Cancel Popeye Reason', readonly=True, copy=False)

    
    def _create_api_log(self, name, url, request_data, response, response_code=None, description=None):
        """
        Helper method untuk membuat log API dengan detail (payload, header, response).
        Log akan selalu tersimpan (di-commit) meskipun ada exception/warning setelahnya.
        
        :param name: Nama log (deskripsi operasi)
        :param url: URL endpoint yang dipanggil
        :param request_data: Data request (dict with 'headers' and 'body' keys)
        :param response: Response object atau content
        :param response_code: HTTP status code (optional)
        :param description: Deskripsi tambahan (optional)
        """
        try:
            # Extract response content
            if hasattr(response, 'content'):
                try:
                    import json
                    response_content = json.loads(response.content)
                except (json.JSONDecodeError, ValueError):
                    response_content = {'raw': str(response.content)}
            else:
                response_content = {'raw': str(response)}
            
            status_code = response_code or (response.status_code if hasattr(response, 'status_code') else 'N/A')
            
            # Extract headers and payload from request_data
            headers = request_data.get('headers', {}) if isinstance(request_data, dict) else {}
            payload = request_data.get('body', request_data) if isinstance(request_data, dict) else request_data
            
            _logger.info(f"Creating API log: {name} - URL: {url} - Status: {status_code}")
            
            # Use create_api_log method which creates log_detail_ids automatically
            log_record = self.env['tw.api.log'].sudo().create_api_log(
                name=name,
                url=url,
                description=description or name,
                ip_address='',
                response=response_content,
                payload=payload,
                header=headers,
                response_code=str(status_code),
                status_code=str(status_code),
            )
            
            _logger.info(f"API log created with ID: {log_record.id}")
            # Commit log agar tetap tersimpan meskipun ada Warning/exception setelahnya
            self.env.cr.commit()
            _logger.info(f"API log committed successfully")
        except Exception as e:
            _logger.error(f"Failed to create API log: {e}")

    def action_send_to_popeye(self):
        self.ensure_one()
        
        # Check allocation before sending to Popeye
        self._check_allocation()
        
        config = self._popeye_get_config()
        payload = self._popeye_prepare_payload()

        url = f"{config['url']}/api/v1/post_ap_payment"
        log_name = f"B2B Popeye Send Payment - {self.name}"
        response = None
        
        try:
            response = requests.post(
                url,
                headers=config['headers'],
                json=payload,
            )
            
            # Create API Log
            self._create_api_log(
                name=log_name,
                url=url,
                request_data={'headers': config['headers'], 'body': payload},
                response=response,
            )
            
            content = response.content
            if not content:
                 raise Warning('Empty response from Popeye API. Status Code: %s' % response.status_code)
            
            try:
                check_response = json.loads(content)
            except json.JSONDecodeError:
                 raise Warning('Invalid JSON response from Popeye API. Status Code: %s, Content: %s' % (response.status_code, content))

            # Validasi response dari Popeye API
            # Status = 0 menandakan error, atau code diawali 'ERR'
            if check_response.get('status') == 0:
                error_message = check_response.get('message') or check_response.get('error') or 'Unknown error'
                error_code = check_response.get('code') or 'N/A'
                raise Warning('Popeye API Error [%s]: %s' % (error_code, error_message))
            
            if str(check_response.get('code', '')).upper().startswith('ERR'):
                error_message = check_response.get('message') or check_response.get('error') or 'Unknown error'
                raise Warning('Popeye API Error [%s]: %s' % (check_response.get('code'), error_message))
            
            if 'error' in check_response and check_response.get('error'):
                raise Warning('Popeye API Error: %s' % check_response.get('error'))

            if 'data' in check_response:
                check_response = check_response['data']
            
            response.raise_for_status() 

        except requests.exceptions.RequestException as e:
            # Log error jika request gagal
            self._create_api_log(
                name=log_name,
                url=url,
                request_data={'headers': config['headers'], 'body': payload},
                response=str(e),
                response_code='Error',
            )
            raise Warning(_('Failed to connect to Popeye API: %s') % e)
        
        self.write({
            'status_api_payment': 'send',
            'send_uid': self.env.user.id,
            'send_date': fields.Datetime.now(),
            'state': 'wfp',
            'wfp_uid': self.env.user.id,
            'wfp_date': fields.Datetime.now(),
        })

    def action_check_status_popeye(self):
        self.ensure_one()

        payload = {"transactions": [{"transaction_no": self.name}]}
        
        config = self._popeye_get_config()
        url = f"{config['url']}/api/v1/ap_payment/check_status"
        log_name = f"B2B Popeye Check Status - {self.name}"
        response = None
        
        try:
            response = requests.post(
                url,
                headers=config['headers'],
                json=payload,
                timeout=10
            )
            
            # Create API Log
            self._create_api_log(
                name=log_name,
                url=url,
                request_data={'headers': config['headers'], 'body': payload},
                response=response,
            )
            
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            # Log error jika request gagal
            self._create_api_log(
                name=log_name,
                url=url,
                request_data={'headers': config['headers'], 'body': payload},
                response=str(e),
                response_code='Error',
            )
            raise Warning(_('Failed to connect to Popeye API: %s') % e)

        content = response.content
        if not content:
             raise Warning('Empty response from Popeye API. Status Code: %s' % response.status_code)
        
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
             raise Warning('Invalid JSON response from Popeye API. Status Code: %s, Content: %s' % (response.status_code, content))

        if 'data' in data:
            data = data['data']

        if not data:
             raise Warning('Invalid response data from Popeye API: Data is empty.')
        
        if 'transactions' in data and isinstance(data['transactions'], list) and len(data['transactions']) > 0:
            transaction_data = data['transactions'][0]
            self._update_status_from_popeye(transaction_data.get('transaction_status'), transaction_data.get('message'))
        else:
            self._update_status_from_popeye(data.get('transaction_status'), data.get('message'))


    def _popeye_get_config(self):
        config = self.env['tw.api.configuration'].search([('api_type_id.value', '=', 'popeye')], limit=1)
        if not config:
            raise Warning(_('There is no active Popeye API configuration in TW API Configuration. Please configure one first.'))

        return {
            'url': config.base_url,
            'headers': {
                "authorization":"Bearer %s" %config.token,
                "content-type": "application/json"
                }
        }

    def _popeye_prepare_payload(self):
        raise NotImplementedError()
    
    def _get_payment_lines_for_allocation_check(self):
        """
        Abstract method: Must be implemented by child class.
        Returns: dict of {move_line_id: amount}
        """
        raise NotImplementedError(_(
            "Method _get_payment_lines_for_allocation_check must be implemented by %s" % self._name
        ))
    
    def _get_outstanding_popeye_amount(self, move_line_ids):
        """
        Menghitung jumlah (amount) untuk move_line_ids tertentu yang saat ini 
        terkunci di transaksi lain yang telah dikirim ke Popeye 
        (tetapi belum 'Paid' atau 'Reject').

        :param move_line_ids: list dari ID account.move.line
        :return: dict {move_line_id: outstanding_amount}
        """
        if not move_line_ids:
            return {}

        # Status Popeye yang dianggap "pending" / masih mengunci amount
        popeye_pending_states = (
            'send', 
            'waiting_request_approval', 
            'verifying', 
            'on_approval', 
            'queuing'
        )

        # Query untuk mencari alokasi yang terkunci di Popeye
        query = """
            SELECT
                payment_line.move_line_id,
                SUM(payment_line.amount) as outstanding_amount
            FROM
                %s payment_line
            JOIN
                %s payment ON payment_line.payment_id = payment.id
            WHERE
                payment_line.move_line_id IN %%s
                AND payment_line.type IN ('dr', 'cr')
                AND payment.status_api_payment IN %%s
                AND payment.id != %%s
            GROUP BY
                payment_line.move_line_id
        """ % (
            self._get_payment_line_table_name(),
            self._get_payment_table_name()
        )
        
        self.env.cr.execute(query, (tuple(move_line_ids), popeye_pending_states, self.id or 0))
        result = self.env.cr.fetchall()
        
        return {row[0]: row[1] for row in result}
    
    def _get_payment_line_table_name(self):
        """Returns the table name for payment lines. Must be overridden by child class."""
        raise NotImplementedError(_(
            "Method _get_payment_line_table_name must be implemented by %s" % self._name
        ))
    
    def _get_payment_table_name(self):
        """Returns the table name for payment header. Must be overridden by child class."""
        raise NotImplementedError(_(
            "Method _get_payment_table_name must be implemented by %s" % self._name
        ))
    
    def _check_allocation(self):
        """
        Validasi alokasi payment untuk memastikan tidak over-allocate.
        Mengecek apakah total alokasi (current + outstanding di Popeye) 
        tidak melebihi open balance sebenarnya.
        """
        self.ensure_one()
        
        # Get payment lines dari child class
        lines_to_check = self._get_payment_lines_for_allocation_check()
        
        if not lines_to_check:
            return True
        
        # Precision untuk pembulatan
        precision = self.env['decimal.precision'].precision_get('Account')
        
        # Ambil move line IDs
        move_line_ids = list(lines_to_check.keys())
        
        # Ambil data move lines (amount_residual, name, ref)
        move_lines = self.env['account.move.line'].browse(move_line_ids)
        residual_map = {ml.id: ml.amount_residual for ml in move_lines}
        name_map = {ml.id: (ml.name or '', ml.ref or '') for ml in move_lines}
        
        # Ambil outstanding amount di Popeye
        outstanding_map = self._get_outstanding_popeye_amount(move_line_ids)
        
        # Validasi setiap line
        for move_line_id, current_allocation in lines_to_check.items():
            true_open_balance = residual_map.get(move_line_id, 0.0) * -1
            outstanding_amount = outstanding_map.get(move_line_id, 0.0)
            
            if outstanding_amount:
                total_allocation = current_allocation + outstanding_amount
                
                # Gunakan round dengan precision untuk perbandingan
                if round(total_allocation, precision) > round(true_open_balance, precision):
                    line_name, line_ref = name_map.get(move_line_id, ('N/A', 'N/A'))
                    
                    raise Warning(_(
                        'Alokasi Gagal untuk Detail %s (Ref: %s)!\n\n'
                        'Sisa Open Balance (%s) tidak mencukupi.\n\n'
                        'Alokasi saat ini: %s\n'
                        'Outstanding di Popeye: %s\n'
                        'Total Alokasi (Saat ini + Popeye): %s'
                    ) % (
                        line_name, line_ref, self.currency_format(true_open_balance),
                        self.currency_format(current_allocation),
                        self.currency_format(outstanding_amount),
                        self.currency_format(total_allocation)
                    ))
        
        return True

    def _update_status_from_popeye(self, status, message=''):
        self.ensure_one()
        status_api_payment = status.lower().replace(' ', '_') if status else False
        if not status_api_payment or status_api_payment not in dict(self.fields_get(['status_api_payment'])['status_api_payment']['selection']).keys():
             return

        vals = {'status_api_payment': status_api_payment, 'last_status_check': fields.Datetime.now()}
        user_id = self.env.user.id
        now = fields.Datetime.now()

        if status_api_payment == 'waiting_request_approval':
            vals.update({'wra_uid': user_id, 'wra_date': now})
        elif status_api_payment == 'verifying':
            vals.update({'verifying_uid': user_id, 'verifying_date': now})
        elif status_api_payment == 'on_approval':
            vals.update({'on_approval_uid': user_id, 'on_approval_date': now})
        elif status_api_payment == 'reject':
            vals.update({'reject_api_uid': user_id, 'reject_api_date': now, 'reason_reject': message})
        elif status_api_payment == 'queuing':
            vals.update({'queuing_uid': user_id, 'queuing_date': now})
        elif status_api_payment == 'paid':
            vals.update({'paid_uid': user_id, 'paid_date': now})
            if hasattr(self, '_popeye_post_payment'):
                self._popeye_post_payment()

        self.write(vals)

    def action_open_cancel_popeye_wizard(self):
        """
        Membuka wizard untuk input alasan cancel Popeye.
        """
        self.ensure_one()
        return {
            'name': 'Cancel Popeye',
            'type': 'ir.actions.act_window',
            'res_model': 'tw.popeye.cancel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_model': self._name,
                'active_id': self.id,
            }
        }

    def action_cancel_popeye(self, reason):
        """
        Action untuk cancel transaksi Popeye.
        Dipanggil dari wizard setelah user mengisi alasan cancel.
        
        :param reason: Alasan pembatalan dari wizard
        """
        self.ensure_one()
        
        # Determine correct cancel state based on model
        # tw.account.payment uses 'canceled' (from account.payment)
        # tw.bank.transfer uses 'cancel'
        cancel_state = 'canceled' if self._name == 'tw.account.payment' else 'cancel'
        
        self.write({
            'status_api_payment': 'draft',
            'state': cancel_state,
            'cancel_popeye_uid': self.env.user.id,
            'cancel_popeye_date': fields.Datetime.now(),
            'cancel_popeye_reason': reason,
        })
