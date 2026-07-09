# 1: imports of python lib
from datetime import datetime, timedelta
import base64
import re

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib


class TwB2BeMeterai(models.Model):
    _name = "tw.b2b.emeterai"
    _description = 'B2B e-Meterai'

    # 7: defaults methods
    def _get_default_date(self): 
        return self.env['res.company'].get_default_date()
    
    def _get_default_datetime(self):
        return datetime.now()

    # 8: fields
    name = fields.Char(string='Name')
    stamped_file_id = fields.Char(string='Stamped File ID')
    stamped_serial_number = fields.Char(string='Stamped Serial Number')
    stamped_status = fields.Char(string='Stamped Status')
    stamped_filename = fields.Char(string='Stamped Filename')
    stamped_note = fields.Char(string='Error Note Stamped')
    transaction_name = fields.Char(string='Transaction Name')
    stamped_response = fields.Text(string='Stamped Response')
    amount = fields.Float(string='Amount')
    date = fields.Date(string='Date', default=_get_default_date)
    state = fields.Selection(string='State', selection=[
        ('draft', 'Draft'),
        ('process', 'Process'),
        ('stamp', 'Stamp'),
        ('error', 'Error')
    ], default='draft')
    file = fields.Binary(string='File', compute='_compute_file')
    download_file = fields.Binary(string='Download File', compute='_compute_file')
    transaction_id = fields.Integer(string='Transaction Id')

    # 9: relation fields
    company_id = fields.Many2one(comodel_name='res.company', string='Branch', domain=[('parent_id','!=',False)])
    model_id = fields.Many2one(comodel_name='ir.model', string='Model')
    report_id = fields.Many2one(comodel_name='ir.actions.report', string='Report')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('stamped_filename')
    def _compute_file(self):
        for data in self:
            if data.stamped_filename:
                image_file = self.env['tw.config.files'].suspend_security().get_file(self.stamped_filename)
                data.file = image_file
                data.download_file = image_file
            else:
                data.file = False
                data.download_file = False

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            branch_obj = self.env['res.company'].suspend_security().browse(vals['company_id'])
            vals['name'] = self.env['ir.sequence'].get_sequence_code('EMET', branch_obj.code)

        emeterai = super(TwB2BeMeterai, self).create(vals_list)

        return emeterai
    
    def write(self, vals):
        return super(TwB2BeMeterai, self).write(vals)
    
    def unlink(self):
        for x in self:
            if x.state != 'draft':
                raise Warning('Perhatian!\nData tidak bisa dihapus.')
        
        return super(TwB2BeMeterai, self).unlink()

    # 13: action methods
    def action_b2b_emeterai_tree(self):
        domain = []
        name = 'B2B e-Meterai'
        path = 'b2b-emeterai'
        list_view_id = self.env.ref('tw_b2b_emeterai.tw_b2b_emeterai_list_view').id
        form_view_id = self.env.ref('tw_b2b_emeterai.tw_b2b_emeterai_form_view').id
        search_view_id = self.env.ref('tw_b2b_emeterai.tw_b2b_emeterai_search_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'path': path,
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.b2b.emeterai',
            'domain': domain,
            'views': [(list_view_id, 'list'), (form_view_id, 'form')],
            'search_view_id': search_view_id,
            'context': {
                'search_default_fieldname': 1,
                'readonly_by_pass': 1
            },
        }
    
    def action_process_stamp_emeterai(self):
        return self.process_stamp_emeterai()

    # 14: private methods
    def _get_trx_obj(self):
        trx_obj = self.env[self.model_id.model].sudo().browse(self.transaction_id)
        if not trx_obj:
            raise Warning("Object of transaction report doesn't exist !")

        return trx_obj

    def _get_peruri_config_api(self):
        config_peruri_obj = self.env['tw.api.configuration'].sudo().get_api_config('peruri_emeterai')
        if not config_peruri_obj:
            raise Warning("API Config Peruri doesn't exist, create first !")
        
        return config_peruri_obj
    
    def _check_amount_limit_and_get_coordinate_file_emeterai(self, trx_obj):
        emeterai_master_coordinate_model = self.env['tw.b2b.emeterai.master.coordinate'].sudo()
        coordinate_file_emeterai_obj = emeterai_master_coordinate_model.search([
            ('company_id','=',self.company_id.id),
            ('model_id','=',self.model_id.id),
            ('report_id','=',self.report_id.id)
        ], limit=1)
        if not coordinate_file_emeterai_obj:
            raise Warning(f"""
                Master Coordinate e-Meterai doesn't exist\n
                    Branch: [{self.company_id.code}] {self.company_id.name}\n
                    Model: [{self.model_id.model}] {self.model_id.name}\n
                    Report: [{self.report_id.report_name}] {self.report_id.name}\n\n
                Please create first !
            """)
        if self.amount < coordinate_file_emeterai_obj.amount_limit:
            raise Warning(f"""
                Amount transaction of {self.model_id.name} [{trx_obj.name}] must be higher than amount limit !\n
                amount transaction: {self.currency_format(self.amount)}\n
                amount limit: {self.currency_format(coordinate_file_emeterai_obj.amount_limit)}
            """)
        
        return coordinate_file_emeterai_obj
    
    def _check_total_usage_stamp_emeterai(self):
        master_quota_stamp_obj = self.env['tw.b2b.emeterai.master.quota'].sudo().search([
            ('company_id','=',self.company_id.id)
        ], limit=1)
        if not master_quota_stamp_obj:
            raise Warning(f"""
                Master Quota stamp e-Meterai doesn't exist\n
                    Branch: [{self.company_id.code}] {self.company_id.name}\n
                Please create first !
            """)
        total_quota = master_quota_stamp_obj.quota
        total_usage = master_quota_stamp_obj.total_usage
        if total_usage >= total_quota:
            raise Warning(f"""
                Total usage of stamp e-Meterai [{total_usage}] is more than equals from limit quota stamp [{total_quota}]\n
                Try to contact the responsible.
            """)
        
        return master_quota_stamp_obj
    
    def _get_pdf_file_and_total_page(self, trx_obj):
        datas = {
            'id': trx_obj.id,
            'model': self.model_id.model,
            'data': trx_obj.read()[0],
            'form': trx_obj.read()[0],
            'user': self._uid
        }
        report_obj = self.env['ir.actions.report']._get_report_from_name(self.report_id.report_name)
        report_action = report_obj.get_external_id().get(report_obj.id)
        report = self.env['ir.actions.report']._render_qweb_pdf(report_action, data=datas)
        b64_pdf = base64.b64encode(report[0]).decode('utf-8')

        # get total page
        total_page = self._get_total_page(b64_pdf)

        return b64_pdf, total_page
    
    def _get_total_page(self, b64_pdf):
        # decode base64
        pdf_bytes = base64.b64decode(b64_pdf)

        # convert to text (PDF is mostly ASCII with binary parts)
        pdf_text = pdf_bytes.decode('latin1') # latin1 preserves all bytes

        # find /Count values
        total_pages = 1
        counts = re.findall(r"/Count\s+(\d+)", pdf_text)
        if counts:
            total_pages = int(counts[0])
            
        return total_pages
    
    def _prepare_body_request_stamp_emeterai_data(self, pdf, filename, total_page, pdf_config_coordinate, trx_obj):
        return {
            'pdf': pdf,
            'filename': filename,
            'page': total_page,
            'visLLX': float(pdf_config_coordinate[0]) if '.' in pdf_config_coordinate[0] else int(pdf_config_coordinate[0]),
            'visLLY': float(pdf_config_coordinate[1]) if '.' in pdf_config_coordinate[1] else int(pdf_config_coordinate[1]),
            'visURX': float(pdf_config_coordinate[2]) if '.' in pdf_config_coordinate[2] else int(pdf_config_coordinate[2]),
            'visURY': float(pdf_config_coordinate[3]) if '.' in pdf_config_coordinate[3] else int(pdf_config_coordinate[3]),
            'object': trx_obj
        }
    
    def create_emeterai_stamp_report(self, vals):
        emet_obj = self.suspend_security().create(vals)
        
        return emet_obj
    
    def process_stamp_emeterai(self):
        # Get Trx Obj
        trx_obj = self._get_trx_obj()

        # * Get Config Peruri API
        config_peruri_obj = self._get_peruri_config_api()
        
        # * Check Amount Limit and Get Coordinate of Report
        coordinate_file_emeterai_obj = self._check_amount_limit_and_get_coordinate_file_emeterai(trx_obj)
        pdf_config_coordinate = coordinate_file_emeterai_obj.list_coordinate.replace(' ', '').split(',')

        # * Check Total Usage from Current Company
        master_quota_obj = self._check_total_usage_stamp_emeterai()

        # Get PDF file and Total Page
        pdf, total_page = self._get_pdf_file_and_total_page(trx_obj)

        # Prepare Body Request Stamp e-Meterai
        filename = f"{self.report_id.name.lower().replace(' ', '_')}_{self.transaction_id}.pdf"
        datas = self._prepare_body_request_stamp_emeterai_data(pdf, filename, total_page, pdf_config_coordinate, trx_obj)

        is_success_stamp = False
        try:
            datas = config_peruri_obj.action_upload_doc_peruri(datas=datas)
            if datas:
                self.stamped_file_id = datas.get('upload_doc_peruri').get('idfile')
                datas = config_peruri_obj.action_generate_sn_peruri(datas=datas)
                if datas:
                    new_datas = datas.copy()
                    new_datas.update({
                        'object': {'model': datas.get('object')._name, 'id': datas.get('object').id}
                    })
                    del new_datas['pdf']
                    self.stamped_serial_number = datas.get('generate_sn_peruri').get('serialNumber')
                    self.stamped_response = str(new_datas)
                    datas = config_peruri_obj.action_stamp_peruri(datas=datas)
                    if datas.get('srcfileStamp'):
                        is_success_stamp = True

                    filename_emeterai = datas.get('filename')
                    stamp_status = config_peruri_obj.action_check_status_sn_peruri(filter_sn=datas.get('generate_sn_peruri').get('serialNumber'))
                    if is_success_stamp:
                        stamp_emeterai_doc_files = config_peruri_obj.action_download_file_stamp_peruri(datas=datas)
                        if stamp_emeterai_doc_files:
                            self.env['tw.config.files'].suspend_security().upload_file(filename_emeterai, stamp_emeterai_doc_files)
                            self.stamped_status = stamp_status
                            self.stamped_filename = filename_emeterai
                            self.state = 'stamp'
                            self.stamped_note = False
                            
                            # * update the total usage of stamp e-Meterai from current company
                            master_quota_obj.suspend_security().write({'total_usage': master_quota_obj.total_usage + 1})
                            
                            return stamp_emeterai_doc_files, filename_emeterai
                        else:
                            return False, False
                    else:
                        self.stamped_status = stamp_status
                        self.state = 'process'
                        if self.stamped_note:
                            self.stamped_note = False
                        return False, False
        except Exception as err:
            raise Warning(str(err.args[0]))

        return True