from odoo import models, fields, api, Command
from odoo.exceptions import UserError as Warning, ValidationError
from datetime import date, datetime
import base64
import xlrd
import logging

_logger = logging.getLogger(__name__)

class TwUploadPaymentRequest(models.TransientModel):
    _name = "tw.payment.request.upload"
    _description = "Upload Payment Request"

    @api.model
    def _get_default_date(self):
        return self.env['res.company'].get_default_datetime()

    # General fields
    file = fields.Binary('File')
    filename = fields.Char('File Name')

    payment_id = fields.Many2one('tw.payment.request', string='Payment Request')
    
    def action_download_format_file(self):
        name = 'upload ' + self.payment_id.type.replace('_',' ').lower() #This will result ex : 'upload payment request'
        format_upload_obj = self.env['tw.format.upload'].suspend_security().search([
            ('name','=',name),
            ('active','=',True)
        ], limit=1)
        if format_upload_obj:
            return {
                'type': 'ir.actions.act_url',
                'name': 'contract',
                'url': f'/web/content/tw.format.upload/{format_upload_obj.id}/file_format_show/{format_upload_obj.filename_upload_format}?download=true'
            }
        else:
            raise Warning(f'Maaf, format template file "{name}" belum tersedia.')

    def action_import_file(self):
        self.ensure_one()
        if not self.file:
            raise Warning("Please upload a file to import")
        
        data = base64.decodebytes(self.file)
        workbook = xlrd.open_workbook(file_contents=data)
        worksheet = workbook.sheet_by_index(0)
        lines = []
        
        MANDATORY_COLS = {}
        if self.payment_id.type == 'payment_request':
            MANDATORY_COLS = {
                'branch': 0,
                'ktp': 1,
                'account': 3,
                'description': 4,
                'amount': 5,
            }
        
        for rx in range(1, worksheet.nrows):
            values = [worksheet.cell(rx, ry).value for ry in range(worksheet.ncols)]

            # * Check for missing / invalid mandatory values
            for item in MANDATORY_COLS:
                if not values[MANDATORY_COLS[item]] or values[MANDATORY_COLS[item]] == '0':
                    col = self._get_excel_column(COLS[item]+1)
                    cell = col+str(rx+1)
                    err = "{} di cell {} TIDAK boleh kosong!".format(MANDATORY_COLS[item],cell)
                    _logger.error(err)
                    raise Warning(err)

            branch = values[0]
            ktp = str(values[1]).replace('.0','')
            nip = str(values[2]).replace('.0','')
            account = str(values[3]).replace('.0','')
            name = str(values[4])
            amount = float(values[5])
            taxes_names = values[6].split(';')

            if branch:
                branch_obj = self.env['res.company'].search([('code', '=', branch)], limit=1)
                if not branch_obj:
                    raise Warning(f"Branch {branch} in row {rx+1} not found ")

            account_obj = self.env['account.account'].search([('code', '=', account)], limit=1)
            if not account_obj:
                raise Warning(f"Account {account} in row {rx+1} not found ")
            
            employee_obj = self.env['hr.employee'].search([('identification_id', '=', ktp)], limit=1)
            if not employee_obj:
                employee_obj = self.env['hr.employee'].search([('registry_number', '=', nip)], limit=1)
                if not employee_obj:
                    raise Warning(f"Employee ktp: {ktp} nip: {nip} in row {rx+1} not found ")
                
            taxes = []
            for tax_name in taxes_names:
                tax_name = tax_name.strip()
                if tax_name:
                    tax_obj = self.env['account.tax'].search([('name', '=', tax_name)], limit=1)
                    if not tax_obj:
                        raise Warning(f"Tax {tax_name} in row {rx+1} not found ")
                    taxes.append(tax_obj.id)

            lines.append({
                'type': 'dr',
                'beneficiary_company_id': branch_obj.id,
                'account_id': account_obj.id,
                'employee_id': employee_obj.id,
                'name': name,
                'amount': amount,
                'tax_ids': [Command.set(taxes)],
            })

        workbook.release_resources()
        self.payment_id.write({
            'user_id': self.env.user.id,
            'line_dr_ids': [Command.create(line) for line in lines]
        })
    