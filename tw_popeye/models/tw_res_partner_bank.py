# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning

# 4:  imports from odoo modules

# 5: local imports
import requests
import json
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib


class ResPartnerBankPopeyeInherit(models.Model):
    _inherit = "res.partner.bank"

    is_match_check_account = fields.Boolean('Is Match Check Account', default=False)
    flag_check_account = fields.Boolean('Cek Nama ke Popeye', default=False)
    is_use_account_name_popeye = fields.Boolean('Gunakan Nama Pemilik Rekening Popeye', default=False)
    remark = fields.Text('Remark')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._check_configuration_popeye(vals)
            vals['is_use_account_name_popeye'] = False
            vals['flag_check_account'] = False
            vals['is_match_check_account'] = True

        create = super(ResPartnerBankPopeyeInherit, self).create(vals_list)
        return create

    def write(self, vals):
        self._check_configuration_popeye(vals)
        vals['is_use_account_name_popeye'] = False
        vals['flag_check_account'] = False
        vals['is_match_check_account'] = True

        write = super(ResPartnerBankPopeyeInherit, self).write(vals)
        return write

    @api.onchange('bank_id')
    def _onchange_bank_id(self):
        self.acc_number = False
        self.acc_holder_name = False
        self.flag_check_account = False
    
    @api.onchange('flag_check_account')
    def _onchange_flag_check_account(self):
        if self.bank_id and self.acc_number and self.flag_check_account:
            datas = {'account_number': str(self.acc_number), 'account_bank': str(self.bank_id.bic)}
            try:
                data = self.action_get_account_holder(datas)
                if data:
                    account_holder = str(data.get('account_name'))
                    if account_holder.lower() != str(self.acc_holder_name).lower():
                        remark = 'NOTE:\nTerdapat perbedaan Nama Pemilik Rekening saat ini dengan data pada Popeye\nNama Pemilik Rekening saat ini\t\t: {nama_pemilik_sekarang}\nNama Pemilik Rekening pada Popeye\t: {nama_pemilik_popeye}'.format(
                            nama_pemilik_sekarang=self.acc_holder_name or '',
                            nama_pemilik_popeye=account_holder
                        )
                        remark += '\n\nJika Nama Pemilik Rekening saat ini dirasa benar, bisa lanjut proses selanjutnya.'
                        remark += '\nJika terdapat kesalahan, ceklis kolom Gunakan Nama Pemilik Rekening Popeye untuk otomatis mengganti Nama Pemilik Rekening saat ini dengan Nama Pemilik Rekening dari Popeye.'
                        self.remark = remark
            except Exception as err:
                self.flag_check_account = False
                self.remark = str(err)
        else:
            self.is_use_account_name_popeye = False
            self.acc_holder_name = False
            self.remark = False
    
    @api.onchange('is_use_account_name_popeye')
    def _onchange_is_use_account_name_popeye(self):
        if self.remark and self.is_use_account_name_popeye and self.flag_check_account:
            if 'Nama Pemilik Rekening pada Popeye' in self.remark:
                account_holder = str(self.remark.split('Nama Pemilik Rekening pada Popeye\t:')[-1].strip().split('\n\n')[0])
                self.acc_holder_name = account_holder
        else:
            self.flag_check_account = False
    
    def action_get_account_holder(self, datas={}, context=None):
        data = self.check_status_account_holder({
            'account_number': datas.get('account_number') if datas.get('account_number') else str(self.acc_number),
            'account_bank': datas.get('account_bank') if datas.get('account_bank') else str(self.bank_id.bic)
        })
        if data:
            if datas and datas.get('account_number') and datas.get('account_bank'):
                return data
    
    def check_status_account_holder(self, data):
        config = self.env['popeye.integration.mixin']._popeye_get_config()
        url = "%s/api/v1/bank/account/check_status" % config['url']
        header = config['headers']
        try:
            log_name = "B2B Popeye Check Status Account Holder"
            log_type = "outgoing"
            log_request_type = "post"
            log_request = {'headers': header, 'body': data}
            response = requests.post(url=url, json=data, headers=header, verify=True)
            # Create Log
            log = {
                'name': log_name,
                'type': log_type,
                'url': url,
                'request_type': log_request_type,
                'request': log_request,
                'response_code': response.status_code,
                'response': str(response.content),
            }
            self.env['tw.api.log'].sudo().create(log)
            self._cr.commit()

            # Process Response
            if response.status_code == 200:
                content = json.loads(response.content)
                code = content.get('code', False) or str(content)
                msg = content.get('message', False) or str(content)
                message_err = 'Message: ' + msg + '\n' + 'Code: ' + code
                info_account = '\nuntuk Nama Bank: %s dan No Rekening: %s\n' % (data.get('account_bank', ''), data.get('account_number', ''))
                if str(content.get('status')) == '1' and content.get('data'):
                    data = content.get('data')
                    if data:
                        account_number = data.get('account_number')
                        account_name = data.get('account_name')
                        if account_number and account_name:
                            datas = {'account_number': account_number, 'account_name': account_name}
                            return datas
                        else:
                            raise Warning('Gagal mengambil status ke Popeye!%s data tidak ada. \n' % (info_account) + message_err)
                    else:
                        raise Warning('Gagal mengambil status ke Popeye!%s data tidak ada. \n' % (info_account) + message_err)
                else:
                    raise Warning('Nomor rekening ini tidak valid, nomor rekening tidak terdaftar!%s \n' % (info_account) + message_err)
            else:
                try:
                    content = json.loads(response.content)
                    msg = content.get('message', False) or str(content)
                except:
                    msg = str(response.content)
                raise Warning('Failed sending data with error :'+msg)
        except Exception as e:
            status_code = response.status_code if 'response' in locals() else 'Unknown'
            raise Warning('There is an error when sending API '+str(status_code)+' : \n'+str(e))

    def _check_configuration_popeye(self,vals):
        is_check_account_popeye = self.env['ir.config_parameter'].sudo().get_param('tw_popeye.is_check_account_popeye') or False
        if is_check_account_popeye:
            if 'flag_check_account' in vals and vals.get('flag_check_account') == False:
                bank_obj = self.env['res.bank'].sudo().browse(vals.get('bank_id'))
                name = "[%s] %s a/n %s" % (bank_obj.name, vals.get('account_number'), vals.get('account_holder'))
                raise Warning('Harap melakukan check account ke Popeye dahulu, dengan ceklis kolom "Check Account to Popeye?" untuk Bank Account {bank_account} !'.format(bank_account=name))
    