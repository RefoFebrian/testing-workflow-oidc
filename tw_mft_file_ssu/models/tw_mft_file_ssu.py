# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
import logging
_logger = logging.getLogger(__name__)

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo import models, fields, api, tools, _
from datetime import date, timedelta, datetime
from PIL import Image

# 5: local imports

# 6: Import of unknown third party lib

class TWB2BFileSsu(models.Model):
    _inherit = "tw.config.files"
    _description = "TW MFT File SSU"
    
    # 7: defaults methods
    def _get_default_main_dealer_code(self):
        return self.env['res.company'].get_default_main_dealer_code()
    
    def _get_default_main_dealer_atpm_code(self):
        return self.env['res.company'].get_default_main_dealer_atpm_code()
    
    def _get_default_main_dealer_ahm_code(self):
        return self.env['res.company'].get_default_main_dealer().default_supplier_id.code
    
    def _get_config_file(self, code):
        config_file_obj = self.env['tw.config.files'].search([
            ('active', '=', True),
            ('name', '=', code)
            ])
        if not config_file_obj:
            raise Warning(_("Warning!\nconfig files with Code %s does not exists!" % code))
        
        return config_file_obj

    # 8: fields
    
    # 9: constraints & sql constraints
    
    # 10: compute/depends & on change methods
    
    # 11: override methods
    
    # 12: action methods
    def ssu_received_md(self,limit=10000,date_filter=''):
        sl_to_send_date = date.today()-timedelta(days=1)
        search_filter = [
            '|',
            ('receive_date','!=',False),
            ('ship_list_date','<=',sl_to_send_date),
            ('division','=','Unit'),
            ('filename_ssu_md_receive','=',False),
            ('actual_ssu_md_receive_date','=',False),
            ('company_id.default_supplier_id.code','in',(self._get_default_main_dealer_code(), self._get_default_main_dealer_ahm_code())),
        ]
        if date_filter:
            date_filter = datetime.strptime(date_filter,'%Y-%m-%d').date()
            search_filter.append(('receive_date','=',date_filter))
        else:
            date_filter = date.today()
        lots = self.env['stock.lot'].sudo().search(search_filter,limit=limit)
        if lots:
            atpm_code = self._get_default_main_dealer_atpm_code()
            date_filter = date_filter.strftime('%d%m%Y')
            config_obj = self._get_config_file('MFT-AHM')
            config_path = config_obj.local_path
            today = date.today()
            tgl = today.strftime('%Y%m%d%H%M')
            name = atpm_code+tgl+'IN.SSU'
            local_path = config_path+'/'+name
            f = open(local_path,"w+")
            for lot in lots:
                tgl_receive = lot.receive_date or lot.ship_list_date
                tgl_receive_format = datetime.strptime(str(tgl_receive)[0:10], '%Y-%m-%d').strftime('%d%m%Y')
                value = ""
                value += atpm_code
                value += ";%s" % lot.name
                value += ";%s" % lot.chassis_number
                value += ";RFS"
                value += ";%s" % tgl_receive_format
                value += ";;;;;;;;;;;;;;;\r\n"
                f.write(value)
                lot.write({'actual_ssu_md_receive_date': datetime.now(),'filename_ssu_md_receive':name})
            f.close()
    
    def ssu_send_dealer(self,limit=100000):
        search_filter = [
            ('division','=','Unit'),
            ('receive_date','!=',False),
            ('filename_ssu_md_receive','!=',False),
            ('actual_ssu_md_receive_date','!=',False),
            ('sales_md_date','!=',False),
            ('filename_ssu_md_send','=',False),  #Tanggal MD Kirim ke Dealer
            ('actual_ssu_md_send_date','=',False), #Tanggal Aktual kirim ssu (MD Kirim ke Dealer)
            ('company_id.code','!=',self._get_default_main_dealer_code()),
        ]
        lots = self.env['stock.lot'].sudo().search(search_filter,limit=limit)
        if lots:
            config_obj = self._get_config_file('MFT-AHM')
            config_path = config_obj.local_path
            today = date.today()
            tgl = today.strftime("%d%m%Y%H%M%S")
            atpm_code = self._get_default_main_dealer_atpm_code()
            name = atpm_code+tgl+'.SSU'
            local_path = config_path+'/'+name
            f = open(local_path,"w+")
            for lot in lots:
                value = ""
                value += atpm_code
                value += ";%s" % lot.name
                value += ";%s" % lot.chassis_number
                value += ";RFS"
                value += ";%s" % lot.receive_date.strftime('%d%m%Y')
                value += ";%s" % lot.sales_md_date.strftime('%d%m%Y')
                value += ";%s" % lot.company_id.atpm_code
                value += ";%s" % lot.sales_md_date.strftime('%d%m%Y')
                value += ";%s" % lot.sales_md_date.strftime('%d%m%Y')
                value += ";;;;;;;;;;;\r\n"
                f.write(value)
                lot.write({'actual_ssu_md_send_date': datetime.now(),'filename_ssu_md_send':name})
            f.close()

    # 13: private methods
