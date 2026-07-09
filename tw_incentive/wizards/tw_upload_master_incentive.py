# -*- coding: utf-8 -*-

# 1: imports of python lib
import base64
from io import BytesIO
import openpyxl

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class UploadMasterIncentive(models.TransientModel):
    _name = "tw.upload.master.incentive"
    _description = "Upload Master Incentive"

    # 7: defaults methods
    def _get_default_date(self):
        return self.env['res.company'].get_default_date()

    # 8: fields
    file = fields.Binary('File')
    date = fields.Date('Tanggal',readonly=True,default=_get_default_date)
    state_x = fields.Selection([('choose','choose'),('get','get')],default=lambda self:self._context.get('default_state_x','choose'))
    sales_category = fields.Selection(selection=lambda self: self.env['tw.selection'].get_option_list('IncentiveCategory'))
    branch_class = fields.Selection(selection=lambda self: self.env['tw.selection'].get_option_list('BranchClass'), default='-')
    
    # 9: relation fields
    
    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    
    # 12: override methods
    
    # 13: action methods
    def action_download_format_file(self):
        format = self.env['tw.format.upload'].suspend_security().search([('name', '=', 'master incentive'), ('active', '=', True)], limit=1)
        if format:
            return {
                'type': 'ir.actions.act_url',
                'name': 'contract',
                'url': f'/web/content/tw.format.upload/{format.id}/file_format_show/{format.filename_upload_format}'
            }
        else:
            raise Warning(_("Sorry, the format is not available yet. Please contact the Helpdesk."))

    
    def action_import(self):
        
        if not self.sales_category:
            raise Warning('Silahkan pilih kategori jabatan untuk master terlebih dahulu')
        if not self.file:
            raise Warning('Silahkan input file terlebih dahulu.')
        
        data = base64.b64decode(self.file)
        try:
            wb = openpyxl.load_workbook(BytesIO(data), data_only=True)
            sh = wb.active
        except Exception as e:
            raise Warning(f"Error reading excel file: {str(e)}")
        
        warning_note = ''
        
        line_ids = []
        rows = list(sh.iter_rows(min_row=2, values_only=True))
        
        for idx, values in enumerate(rows, start=2):
            if not values or not any(v is not None for v in values):
                continue
            
            quantity = int(values[0]) if values[0] is not None else 0
            cash = int(values[1]) if values[1] is not None else 0
            credit = int(values[2]) if values[2] is not None else 0
            reward = int(values[3]) if values[3] is not None else 0
            accumulate_cash = int(values[4]) if len(values) > 4 and values[4] is not None else 0
            accumulate_credit = int(values[5]) if len(values) > 5 and values[5] is not None else 0

            line_ids.append([0,0,{
                'quantity': quantity,
                'cash': cash,
                'credit': credit,
                'reward': reward,
                'accumulate_cash': accumulate_cash,
                'accumulate_credit': accumulate_credit,
            }])
            
        vals = {
            'sales_category': self.sales_category,
            'branch_class': self.branch_class.upper(),
            'incentive_line_ids': line_ids
            }
        
        self.env['tw.master.incentive'].suspend_security().create(vals)
        if warning_note:
            raise Warning(warning_note)
        
        submenu_name = 'Master incentive'
        res_model = 'tw.master.incentive'
        result = {
            'type': 'ir.actions.act_window',
            'name': (submenu_name),
            'res_model': res_model,
            'view_mode': 'list,form',
            'target': 'current',
        }
        
        return result
    
    # 14: private methods
