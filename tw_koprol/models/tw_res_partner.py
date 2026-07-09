from odoo import models, fields, api
from datetime import datetime, timedelta

import requests

class Vendor(models.Model):
    _inherit = "res.partner"
    _description = "Vendor"

    koprol_code = fields.Char('Koprol Code')
    last_modified_date = fields.Datetime('Last Modified Date Koprol')

    
    def assign_vendor_categories(self, item, vals):
        category_mapping = {
            'Biro Jasa': 'biro_jasa',
            'Dispenda': 'dispenda',
            'Forwarder': 'forwarder',
            'Showroom': 'showroom',
            'Finance Company': 'finance_company',
            'Insurance': 'insurance',
            'Customer': 'customer',
            'Direct Customer': 'direct_customer',
            'Samsat': 'is_samsat'
        }
        for categ in item['vendor_categories']:
            if categ:
                category_name = categ['category_name']
                if category_name in category_mapping:
                    vals[category_mapping[category_name]] = True
                else:
                    vals['supplier'] = True

    
    def create_bank_accounts(self, bank_account, vendor_obj):
        for bank in bank_account:
            if len(bank['account_number']) < 10:
                return {'error': 'digit', 'message': 'Account Number tidak boleh kurang dari 10 digit.'}
            
            bank_obj = self.env['res.bank'].sudo().search([('code', '=', bank['bank_code'])], limit=1)
            if bank_obj:
                bank_obj.write({'bic': bank['swift_code']})
            else:
                return {'error': 'bank_obj', 'message': 'Bank Code %s tidak ditemukan' % (bank['bank_code'])}

            bank_name = '[{bank}] {number} - {name}'.format(bank=bank_obj.name, number=bank['account_number'] , name=bank['account_holder'])
            self.env['res.partner.bank'].sudo().create({
                'name': bank['bank_alias'] if bank.get('bank_alias') else bank_name,
                'account_number': bank['account_number'],
                'account_holder': bank['account_holder'],
                'active': bank['is_active'],
                'bank_id': bank_obj.id if bank_obj else False,
                'partner_id': vendor_obj.id,
                'flag_check_account': True
            })

    def checking_modified_vendor_data(self, last_modified_date_erp, last_modified_date_koprol):
        last_modified_date = datetime.strptime(last_modified_date_erp, '%Y-%m-%d %H:%M:%S') 
        last_modified_date_koprol = datetime.strptime(last_modified_date_koprol, '%Y-%m-%d %H:%M:%S') 

        if last_modified_date < datetime.strptime(last_modified_date_koprol, '%Y-%m-%d %H:%M:%S'):
            return True
        return False

    def checking_duplicate_vendor_data(self, vals):
        vendor_no_erp = vals.get('default_code')
        vendor_no_koprol = vals.get('koprol_code')
        last_modified_koprol = vals.get('last_modified_date')

        duplicate_vendor = False
        if vendor_no_erp:
            duplicate_vendor = self.sudo().search([('code', '=', vendor_no_erp)], limit=1)
        if not duplicate_vendor and vendor_no_koprol:
            duplicate_vendor = self.sudo().search([('koprol_code', '=', vendor_no_koprol)], limit=1)
        
        if duplicate_vendor:
            if duplicate_vendor.last_modified_date:
                if self.checking_modified_vendor_data(duplicate_vendor.last_modified_date, last_modified_koprol):
                    return duplicate_vendor
            return False
                
        return duplicate_vendor

    def process_vendor_data(self, data, type=None):
        for item in data:
            vendor_obj = self.checking_duplicate_vendor_data({
                'default_code': item['default_code'],
                'koprol_code': item['koprol_code'],
                'name': item['name'],
                'last_modified_date': item['last_modified_date']
            })

            if vendor_obj:
                vendor_obj.sudo().write(item)
            else:
                item.update({
                    'supplier': True,
                    'customer': False,
                })
                vendor_obj = self.sudo().create(item)

            if type == 'api' and len(data) == 1:
                return vendor_obj