# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
import requests
import json
from datetime import datetime

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError

# 4: imports from odoo modules

# 5: local imports
from .tw_mft_config import TLSAdapter

# 6: Import of unknown third party lib

_logger = logging.getLogger(__name__)


class TwMftLog(models.Model):
    """Model to store MFT data from Portal AHM get-data-mft endpoint."""
    
    _name = "tw.mft.log"
    _description = "MFT Log"
    _order = "fetch_date desc, id desc"

    # 7: defaults methods

    # 8: fields
    name = fields.Char(
        string='Reference', 
        readonly=True, 
        copy=False,
        default=lambda self: _('New')
    )
    fileid = fields.Char(
        string='File ID', 
        required=True, 
        index=True,
        help="Unique file identifier from AHM"
    )
    filename = fields.Char(string='File Name')
    sendername = fields.Char(string='Sender Name')
    receivername = fields.Char(string='Receiver Name')
    fileext = fields.Char(string='File Extension')
    filesize = fields.Integer(string='File Size (bytes)')
    filesize_display = fields.Char(
        string='File Size',
        compute='_compute_filesize_display'
    )
    
    # Date fields
    dstart = fields.Datetime(string='Start Date')
    dstart2 = fields.Datetime(string='Start Date 2')
    dfinish = fields.Datetime(string='Finish Date')
    fetch_date = fields.Datetime(
        string='Fetch Date', 
        default=fields.Datetime.now,
        readonly=True
    )
    
    # Record counts
    irec = fields.Integer(string='Total Records')
    irecok = fields.Integer(string='Success Records')
    irecnok = fields.Integer(string='Failed Records')
    
    # Status
    status = fields.Float(string='Success Rate (%)', digits=(5, 3))
    status_code = fields.Char(string='Status Code')
    color_status = fields.Char(string='Color Status')
    
    # State for UI coloring
    state = fields.Selection([
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ], string='State', compute='_compute_state', store=True)
    
    # Success rate category for grouping
    success_rate_category = fields.Selection([
        ('complete', '100% Success'),
        ('incomplete', 'Belum 100%'),
    ], string='Success Category', compute='_compute_success_rate_category', store=True)
    
    active = fields.Boolean(string='Active', default=True)

    # 9: relation fields
    config_id = fields.Many2one(
        'tw.mft.config',
        string='Configuration',
        required=True,
        ondelete='cascade',
        index=True
    )
    detail_ids = fields.One2many(
        'tw.mft.log.detail',
        'log_id',
        string='Error Details'
    )
    detail_count = fields.Integer(
        string='Error Count',
        compute='_compute_detail_count'
    )

    # 10: constraints & sql constraints
    _sql_constraints = [
        ('fileid_unique', 'UNIQUE(fileid)', 'File ID must be unique!')
    ]

    # 11: compute/depends & on change methods
    @api.depends('filesize')
    def _compute_filesize_display(self):
        """Convert bytes to human readable format."""
        for rec in self:
            size = rec.filesize or 0
            if size < 1024:
                rec.filesize_display = f"{size} B"
            elif size < 1024 * 1024:
                rec.filesize_display = f"{size / 1024:.2f} KB"
            else:
                rec.filesize_display = f"{size / (1024 * 1024):.2f} MB"
    
    @api.depends('detail_ids')
    def _compute_detail_count(self):
        for rec in self:
            rec.detail_count = len(rec.detail_ids)
    
    @api.depends('status', 'irecnok')
    def _compute_state(self):
        for rec in self:
            # Use irecnok == 0 as source of truth for 100% success
            if rec.irecnok == 0:
                rec.state = 'success'
            elif rec.status >= 80:
                rec.state = 'warning'
            else:
                rec.state = 'error'
    
    @api.depends('irecnok')
    def _compute_success_rate_category(self):
        for rec in self:
            # Use irecnok == 0 as source of truth for 100% success
            if rec.irecnok == 0:
                rec.success_rate_category = 'complete'
            else:
                rec.success_rate_category = 'incomplete'
    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate sequence reference."""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('tw.mft.log') or _('New')
        return super().create(vals_list)

    # 13: action methods
    def action_fetch_detail(self):
        """Fetch error details for this log record."""
        self.ensure_one()
        
        if self.irecnok == 0:
            raise UserError(_("Tidak ada error records untuk di-fetch!"))
        
        config = self.config_id
        if not config.api_config_id.token:
            raise UserError(_("Token (jxid) belum dikonfigurasi!"))
        
        url = f"{config.api_config_id.base_url}{config.endpoint_get_detail}"
        headers = config._get_headers()
        
        MftLogDetail = self.env['tw.mft.log.detail']
        ApiLog = self.env['tw.api.log']
        
        offset = 0
        limit = 100
        
        # Clear existing details before fetching
        self.detail_ids.unlink()
        
        while True:
            payload = {
                "limit": limit,
                "offset": offset,
                "search": {
                    "FILEID": self.fileid,
                    "filterFilename": "",
                    "filterErrorrow": "",
                    "filterErrormsg": ""
                }
            }
            
            try:
                _logger.info(f"Fetching MFT detail: {url}, fileid: {self.fileid}, offset: {offset}")
                
                # Use session with custom TLS adapter for SSL compatibility
                session = requests.Session()
                session.mount('https://', TLSAdapter())
                response = session.post(url, json=payload, headers=headers, timeout=60, verify=False)
                response_data = response.json() if response.content else {}
                
                # Log API call
                ApiLog.create_api_log(
                    name=f"MFT - {self.fileid} (get-detail)",
                    url=url,
                    description=f"Fetch MFT detail for {self.fileid}",
                    ip_address=config.api_config_id.base_url,
                    response=json.dumps(response_data),
                    payload=json.dumps(payload),
                    header=json.dumps({k: v[:20] + '...' if k == 'jxid' and len(v) > 20 else v for k, v in headers.items()}),
                    response_code=str(response.status_code),
                    status_code='success' if response.status_code == 200 else 'error'
                )
                
                if response.status_code != 200:
                    raise UserError(_(
                        f"API Error {response.status_code}: {response_data.get('message', {}).get('message', 'Unknown error')}"
                    ))
                
                if response_data.get('status') != '1':
                    raise UserError(_(
                        f"API returned error: {response_data.get('message', {}).get('message', 'Unknown error')}"
                    ))
                
                data_list = response_data.get('data', [])
                total = response_data.get('total', 0)
                
                # Create detail records
                for item in data_list:
                    MftLogDetail.create({
                        'log_id': self.id,
                        'filename': item.get('filename', ''),
                        'errorrow': item.get('errorrow', 0),
                        'errormsg': item.get('errormsg', ''),
                    })
                
                # Check if more data
                offset += limit
                if offset >= total:
                    break
                    
            except requests.exceptions.RequestException as e:
                _logger.error(f"MFT Detail API connection error: {e}")
                raise UserError(_(f"Connection error: {str(e)}"))
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('%d error details fetched.') % len(self.detail_ids),
                'sticky': False,
                'type': 'success',
            }
        }
    
    def action_view_details(self):
        """Open view of error details for this log."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Error Details - {self.filename}',
            'res_model': 'tw.mft.log.detail',
            'view_mode': 'list,form',
            'domain': [('log_id', '=', self.id)],
            'context': {'default_log_id': self.id},
        }
    
    def action_update_success_rate(self):
        """
        Update success rate by checking detail endpoint.
        If total = 0, it means no more errors (100% success).
        """
        self.ensure_one()
        
        config = self.config_id
        if not config.api_config_id.token:
            raise UserError(_("Token (jxid) belum dikonfigurasi!"))
        
        url = f"{config.api_config_id.base_url}{config.endpoint_get_detail}"
        headers = config._get_headers()
        
        ApiLog = self.env['tw.api.log']
        MftLogDetail = self.env['tw.mft.log.detail']
        
        payload = {
            "limit": 10,
            "offset": 0,
            "search": {
                "FILEID": self.fileid,
                "filterFilename": "",
                "filterErrorrow": "",
                "filterErrormsg": ""
            }
        }
        
        try:
            _logger.info(f"Checking success rate for: {self.fileid}")
            
            # Use session with custom TLS adapter for SSL compatibility
            session = requests.Session()
            session.mount('https://', TLSAdapter())
            response = session.post(url, json=payload, headers=headers, timeout=60, verify=False)
            response_data = response.json() if response.content else {}
            
            # Log API call
            ApiLog.create_api_log(
                name=f"MFT - {self.fileid} (check-success)",
                url=url,
                description=f"Check success rate for {self.fileid}",
                ip_address=config.api_config_id.base_url,
                response=json.dumps(response_data),
                payload=json.dumps(payload),
                header=json.dumps({k: v[:20] + '...' if k == 'jxid' and len(v) > 20 else v for k, v in headers.items()}),
                response_code=str(response.status_code),
                status_code='success' if response.status_code == 200 else 'error'
            )
            
            if response.status_code != 200:
                raise UserError(_(
                    f"API Error {response.status_code}: {response_data.get('message', {}).get('message', 'Unknown error')}"
                ))
            
            if response_data.get('status') != '1':
                raise UserError(_(
                    f"API returned error: {response_data.get('message', {}).get('message', 'Unknown error')}"
                ))
            
            total_errors = response_data.get('total', 0)
            data_list = response_data.get('data', [])
            
            # Clear existing details
            self.detail_ids.unlink()
            
            if total_errors == 0:
                # No more errors - update to 100% success
                self.write({
                    'irecnok': 0,
                    'irecok': self.irec,
                    'status': 100.0,
                    'fetch_date': fields.Datetime.now(),
                })
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('File sudah 100%% Success! Status updated.'),
                        'sticky': False,
                        'type': 'success',
                    }
                }
            else:
                # Still has errors - update error count and create detail records
                new_irecnok = total_errors
                new_irecok = self.irec - new_irecnok
                new_status = (new_irecok / self.irec * 100) if self.irec > 0 else 0
                
                self.write({
                    'irecnok': new_irecnok,
                    'irecok': new_irecok,
                    'status': new_status,
                    'fetch_date': fields.Datetime.now(),
                })
                
                # Create detail records from response
                for item in data_list:
                    MftLogDetail.create({
                        'log_id': self.id,
                        'filename': item.get('filename', ''),
                        'errorrow': item.get('errorrow', 0),
                        'errormsg': item.get('errormsg', ''),
                    })
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Updated'),
                        'message': _('Masih ada %d error. Success rate: %.2f%%') % (total_errors, new_status),
                        'sticky': False,
                        'type': 'warning',
                    }
                }
                
        except requests.exceptions.RequestException as e:
            _logger.error(f"MFT Check Success Rate API error: {e}")
            raise UserError(_(f"Connection error: {str(e)}"))

    # 14: private methods
    @api.model
    def _parse_ahm_datetime(self, dt_str):
        """Parse AHM datetime string to Odoo datetime."""
        if not dt_str:
            return False
        try:
            # Format: "02-Dec-2025 10:05:25"
            return datetime.strptime(dt_str, '%d-%b-%Y %H:%M:%S')
        except (ValueError, TypeError):
            return False
    
    @api.model
    def _create_or_update_from_response(self, data, config):
        """
        Create or update MFT log record from API response.
        
        :param data: dict from API response
        :param config: tw.mft.config record
        :return: dict with 'record', 'created', 'updated' keys
        """
        fileid = data.get('fileid')
        if not fileid:
            return {'record': False, 'created': False, 'updated': False}
        
        existing = self.search([('fileid', '=', fileid)], limit=1)
        
        vals = {
            'fileid': fileid,
            'filename': data.get('filename', ''),
            'sendername': data.get('sendername', ''),
            'receivername': data.get('receivername', ''),
            'fileext': data.get('fileext', ''),
            'filesize': data.get('filesize', 0),
            'dstart': self._parse_ahm_datetime(data.get('dstart')),
            'dstart2': self._parse_ahm_datetime(data.get('dstart2')),
            'dfinish': self._parse_ahm_datetime(data.get('dfinish')),
            'irec': data.get('irec', 0),
            'irecok': data.get('irecok', 0),
            'irecnok': data.get('irecnok', 0),
            'status': data.get('status', 0),
            'status_code': data.get('statusCode', ''),
            'color_status': data.get('colorStatus', ''),
            'config_id': config.id,
            'fetch_date': fields.Datetime.now(),
        }
        
        if existing:
            existing.write(vals)
            return {'record': existing, 'created': False, 'updated': True}
        else:
            record = self.create(vals)
            return {'record': record, 'created': True, 'updated': False}
