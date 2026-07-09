# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
import requests
import json
import ssl
import urllib3
from datetime import datetime, timedelta

# 2: import of known third party lib
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

# 3: imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

# Suppress only the single InsecureRequestWarning from urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_logger = logging.getLogger(__name__)

# Define cipher suites that work with legacy servers
CIPHERS = (
    'ECDHE+AESGCM:DHE+AESGCM:ECDHE+CHACHA20:DHE+CHACHA20:'
    'ECDH+AESGCM:DH+AESGCM:ECDH+AES:DH+AES:'
    'RSA+AESGCM:RSA+AES:'
    'ECDHE+3DES:DHE+3DES:RSA+3DES:'
    '!aNULL:!eNULL:!MD5:!DSS'
)


class TLSAdapter(HTTPAdapter):
    """Custom adapter to handle TLS/SSL connections with legacy support."""
    
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context(ssl_version=ssl.PROTOCOL_TLS_CLIENT)
        # Set cipher suites for compatibility
        ctx.set_ciphers(CIPHERS)
        # Allow legacy renegotiation for older servers (Python 3.12+ only)
        if hasattr(ssl, 'OP_LEGACY_SERVER_CONNECT'):
            ctx.options |= ssl.OP_LEGACY_SERVER_CONNECT
        ctx.options |= ssl.OP_NO_SSLv2
        ctx.options |= ssl.OP_NO_SSLv3
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)


class TwMftConfig(models.Model):
    """Configuration model for MFT monitoring per file type."""
    
    _name = "tw.mft.config"
    _description = "MFT Configuration"
    _order = "filetype"

    # 7: defaults methods

    # 8: fields
    name = fields.Char(
        string='Name', 
        compute='_compute_name', 
        store=True,
        help="Nama konfigurasi (auto-generated dari filetype)"
    )
    filetype = fields.Char(
        string='File Type', 
        required=True,
        help="Tipe file yang akan di-monitor (e.g., LDS, SPK)"
    )
    transtype = fields.Selection([
        ('SEND', 'SEND'),
        ('RECEIVE', 'RECEIVE'),
    ], string='Transaction Type', default='SEND', required=True)
    listtype = fields.Char(string='List Type', default='AHM', required=True)
    listtypecode = fields.Char(string='List Type Code', default='H2Z', required=True)
    status = fields.Char(string='Status Filter', default='BERHASIL_DIAMBIL', required=True)
    limit = fields.Integer(string='Limit per Request', default=100)
    date_range_days = fields.Integer(
        string='Date Range (Days)', 
        default=0,
        help="Jumlah hari ke belakang untuk fetch data. 0 = hari ini saja."
    )
    active = fields.Boolean(string='Active', default=True)
    auto_fetch_detail = fields.Boolean(
        string='Auto Fetch Detail', 
        default=True,
        help="Otomatis fetch detail error jika ada record dengan error (irecnok > 0)"
    )
    last_fetch_date = fields.Datetime(string='Last Fetch Date', readonly=True)
    
    # Endpoint paths
    endpoint_get_data = fields.Char(
        string='Get Data Endpoint',
        default='/jx04/ahmsvipmft000-pst/rest/ip/mft007/get-data-mft',
        required=True
    )
    endpoint_get_detail = fields.Char(
        string='Get Detail Endpoint',
        default='/jx04/ahmsvipmft000-pst/rest/ip/mft007/get-data-detail-mft',
        required=True
    )

    # 9: relation fields
    api_config_id = fields.Many2one(
        'tw.api.configuration', 
        string='API Configuration',
        required=True,
        help="Konfigurasi API untuk Portal AHM (berisi jxid token)"
    )
    log_ids = fields.One2many(
        'tw.mft.log',
        'config_id',
        string='MFT Logs'
    )
    log_count = fields.Integer(
        string='Log Count',
        compute='_compute_log_count'
    )

    # 10: constraints & sql constraints
    _sql_constraints = [
        ('filetype_unique', 'UNIQUE(filetype)', 'File type must be unique!')
    ]

    # 11: compute/depends & on change methods
    @api.depends('filetype')
    def _compute_name(self):
        for rec in self:
            rec.name = f"MFT - {rec.filetype}" if rec.filetype else ''
    
    @api.depends('log_ids')
    def _compute_log_count(self):
        for rec in self:
            rec.log_count = len(rec.log_ids)

    # 12: override methods

    # 13: action methods
    def action_fetch_data(self):
        """Manual trigger to fetch MFT data."""
        self.ensure_one()
        
        # Default date range: today to today
        date_to = datetime.now()
        date_from = date_to - timedelta(days=self.date_range_days)
        
        return self._fetch_mft_data(date_from, date_to)
    
    def action_view_logs(self):
        """Open view of all logs for this configuration."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'MFT Logs - {self.filetype}',
            'res_model': 'tw.mft.log',
            'view_mode': 'list,form',
            'domain': [('config_id', '=', self.id)],
            'context': {'default_config_id': self.id},
        }

    # 14: private methods
    def _get_headers(self):
        """Prepare headers for Portal AHM API."""
        self.ensure_one()
        return {
            'Content-Type': 'application/json',
            'jxid': self.api_config_id.token or '',
        }
    
    def _format_date_ahm(self, dt):
        """Format datetime to AHM date format (DD-Mon-YYYY)."""
        return dt.strftime('%d-%b-%Y')
    
    def _parse_ahm_datetime(self, dt_str):
        """Parse AHM datetime string to Odoo datetime."""
        if not dt_str:
            return False
        try:
            # Format: "02-Dec-2025 10:05:25"
            return datetime.strptime(dt_str, '%d-%b-%Y %H:%M:%S')
        except (ValueError, TypeError):
            return False
    
    def _prepare_payload(self, date_from, date_to, offset=0):
        """Prepare payload for get-data-mft endpoint."""
        self.ensure_one()
        return {
            "limit": self.limit,
            "offset": offset,
            "search": {
                "TRANSTYPE": self.transtype,
                "FILENAME": "",
                "FILETYPE": self.filetype,
                "DATEFROM": self._format_date_ahm(date_from),
                "DATETO": self._format_date_ahm(date_to),
                "LISTTYPE": self.listtype,
                "LISTTYPECODE": self.listtypecode,
                "STATUS": self.status,
                "filterFilename": "",
                "filterListtype": "",
                "filterFileext": "",
                "filterFilesize": "",
                "filterDatestart": "",
                "filterDatestart2": "",
                "filterDfinish": "",
                "filterTotal": "",
                "filterSuccess": "",
                "filterFailed": "",
                "filterStatus": ""
            }
        }
    
    def _fetch_mft_data(self, date_from, date_to):
        """
        Fetch MFT data from Portal AHM.
        
        :param date_from: Start date (datetime)
        :param date_to: End date (datetime)
        :return: dict with result summary
        """
        self.ensure_one()
        
        if not self.api_config_id.token:
            raise UserError(_("Token (jxid) belum dikonfigurasi pada API Configuration!"))
        
        url = f"{self.api_config_id.base_url}{self.endpoint_get_data}"
        headers = self._get_headers()
        
        total_created = 0
        total_updated = 0
        total_errors = 0
        offset = 0
        
        MftLog = self.env['tw.mft.log']
        ApiLog = self.env['tw.api.log']
        
        while True:
            payload = self._prepare_payload(date_from, date_to, offset)
            
            try:
                _logger.info(f"Fetching MFT data: {url}, offset: {offset}")
                
                # Use session with custom TLS adapter for SSL compatibility
                session = requests.Session()
                session.mount('https://', TLSAdapter())
                response = session.post(url, json=payload, headers=headers, timeout=60, verify=False)
                response_data = response.json() if response.content else {}
                
                # Log API call
                ApiLog.create_api_log(
                    name=f"MFT - {self.filetype} (get-data)",
                    url=url,
                    description=f"Fetch MFT data for {self.filetype}",
                    ip_address=self.api_config_id.base_url,
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
                
                # Process each record
                for item in data_list:
                    result = MftLog._create_or_update_from_response(item, self)
                    if result.get('created'):
                        total_created += 1
                    elif result.get('updated'):
                        total_updated += 1
                    
                    # Auto fetch detail if has errors
                    if self.auto_fetch_detail and item.get('irecnok', 0) > 0:
                        log_record = result.get('record')
                        if log_record and not log_record.detail_ids:
                            try:
                                log_record.action_fetch_detail()
                            except Exception as e:
                                _logger.warning(f"Failed to fetch detail for {item.get('fileid')}: {e}")
                                total_errors += 1
                
                # Check if more data available
                offset += self.limit
                if offset >= total:
                    break
                    
            except requests.exceptions.RequestException as e:
                _logger.error(f"MFT API connection error: {e}")
                # Log error
                ApiLog.create_api_log(
                    name=f"MFT - {self.filetype} (ERROR)",
                    url=url,
                    description=f"Connection error: {str(e)}",
                    ip_address=self.api_config_id.base_url,
                    response=json.dumps({'error': str(e)}),
                    payload=json.dumps(payload),
                    header=json.dumps(headers),
                    response_code='0',
                    status_code='error'
                )
                raise UserError(_(f"Connection error: {str(e)}"))
        
        # Update last fetch date
        self.write({'last_fetch_date': fields.Datetime.now()})
        
        return {
            'created': total_created,
            'updated': total_updated,
            'errors': total_errors,
        }
    
    @api.model
    def _cron_fetch_mft_data(self):
        """
        Scheduled action to fetch MFT data for all active configurations.
        """
        configs = self.search([('active', '=', True)])
        
        for config in configs:
            try:
                date_to = datetime.now()
                date_from = date_to - timedelta(days=config.date_range_days)
                
                result = config._fetch_mft_data(date_from, date_to)
                _logger.info(
                    f"MFT Cron - {config.filetype}: "
                    f"Created {result['created']}, Updated {result['updated']}, Errors {result['errors']}"
                )
            except Exception as e:
                _logger.error(f"MFT Cron - {config.filetype} failed: {e}")
                # Continue to next config even if one fails
                continue
