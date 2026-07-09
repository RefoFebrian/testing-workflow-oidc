from odoo import models, fields, api
from odoo.exceptions import UserError as Warning
from datetime import datetime

import json
import requests

class TwApiKoprolWizard(models.TransientModel):
    _name = "tw.api.koprol.wizard"
    _description = "Tw Api Koprol Wizard"

    koprol_code = fields.Char('Koprol Code')
    product_code = fields.Char('Product Code')
    category_code = fields.Char('Product Category Code')

    limit = fields.Integer('Limit', default=1)
    offset = fields.Integer('Offset', default=10)
    options = fields.Selection([
        ('goods', 'Goods / Product'),
        ('vendor', 'Vendor'),
        ('proposal', 'Budget Proposal'),
    ], string='Options')

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')

    @api.onchange('end_date')
    def onchange_back_date(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise Warning('Maaf, End Date tidak boleh lebih kecil dari Start Date.')

    def generate_data(self):
        if self.options == 'vendor':
            self.generate_data_vendor()
        elif self.options == 'goods':
            self.generate_data_goods()

    def get_api_config(self):
        """Get Koprol API configuration by api_type_value"""
        config_obj = self.env['tw.api.configuration'].sudo().search([
            ('api_type_value', '=', 'koprol_2')
        ], limit=1)
        if not config_obj:
            raise Warning('Configuration API Koprol Belum di setting. Pastikan API Type = Koprol 2.0')
        
        return config_obj
    
    def get_headers(self):
        """Get Azure token and return authorization headers"""
        config_obj = self.get_api_config()
        
        # Check if token refresh is needed
        need_refresh = False
        if not config_obj.token:
            need_refresh = True
        elif config_obj.expired_on:
            if datetime.now() > config_obj.expired_on:
                need_refresh = True
        else:
            # expired_on is False/None, need to refresh
            need_refresh = True
        
        if need_refresh:
            config_obj.get_azure_access_token()
        
        return {"Authorization": "Bearer {token}".format(token=config_obj.token)}

    def create_log(self, url, body, content):
        self.env['tw.api.log'].sudo().create({
            'name': 'GET All %s From Koprol' % (self.options.capitalize()),
            'url': url,
            'request': str(body),
            'response_code': str(content.get('code')) if content.get('code') else '',
            'response': str(content),
        })

    def generate_data_vendor(self):
        config_obj = self.get_api_config()
        endpoint = config_obj._get_koprol_endpoint('koprol.vendor')
        url = endpoint.full_url
        headers = self.get_headers()

        body = {
            "page": self.limit,
            "page_size": self.offset,
            "company_code": "15", 
            "start_last_modified_koprol": str(self.start_date) if self.start_date else "",
            "end_last_modified_koprol": str(self.end_date) if self.end_date else "",
            "vendor_no_koprol": self.koprol_code if self.koprol_code else "",
        }

        response = requests.post(url, json=body, headers=headers)
        content = json.loads(response.content)

        # Always create log for debugging
        self.create_log(url, body, content)

        # Check for API errors
        if content.get('code') != 200:
            error_msg = content.get('message', 'Unknown Error')
            detail_msg = content.get('detail_message', '')
            raise Warning(f"API Koprol Error ({content.get('code')}): {error_msg}. Detail: {detail_msg}")

        if content.get('data'):
            for item in content['data']:
                vendor_obj = False
                vendor = self.env['res.partner'].sudo()
                term_obj = self.env['account.payment.term'].sudo().search([
                    ('name', '=', item['terms_of_payment']),
                    ('active', '=', True)
                ], limit=1)

                vendor_obj = vendor.process_vendor_data({
                    'supplier': True,
                    'supplier_type': 'perusahaan' if item['company_type'] == 'company' else 'perorangan',
                    'property_supplier_payment_term': term_obj.id if term_obj else False,
                    'street': item['address'],
                    'last_modified_date': item['last_modified_koprol'],
                    'phone': item['phone'],
                    'email': item['email'],
                    'npwp': item['npwp'],
                    'mobile': item['mobile'],
                    'koprol_code': item['vendor_no_koprol'],
                    'website': item['website_link'],
                    'pkp': item['is_pkp'] == 'true',
                    'alamat_pkp': item['address_pkp'],
                    'no_ktp': item['identity_number'],
                    'supplier': item['vendor_type'] == 'trade',
                    'name': item['vendor_name']
                })
                if vendor_obj and item.get('bank_account'):
                    vendor_obj.sudo().create_bank_accounts(item['bank_account'], vendor_obj)
        else:
            raise Warning("API Koprol Success tapi tidak ada data yang ditemukan.")

    def generate_data_goods(self):
        config_obj = self.get_api_config()
        endpoint = config_obj._get_koprol_endpoint('koprol.goods.product')
        url = endpoint.full_url
        headers = self.get_headers()

        body = {
            "page": self.limit,
            "page_size": self.offset,
            "company_code": "", 
            "start_last_modified_koprol": str(self.start_date) if self.start_date else "",
            "end_last_modified_koprol": str(self.end_date) if self.end_date else "",
            "product_no_koprol": self.koprol_code if self.koprol_code else "",
            "category_code": self.category_code if self.category_code else ""
        }
        
        response = requests.post(url, json=body, headers=headers)
        content = json.loads(response.content)
        
        # Always create log for debugging
        self.create_log(url, body, content)

        # Check for API errors
        if content.get('code') != 200:
            error_msg = content.get('message', 'Unknown Error')
            detail_msg = content.get('detail_message', '')
            raise Warning(f"API Koprol Error ({content.get('code')}): {error_msg}. Detail: {detail_msg}")

        if content.get('data'):
            self.process_goods_data(content['data'])
        else:
            raise Warning("API Koprol Success tapi tidak ada data yang ditemukan.")

    def process_goods_data(self, data):
        for item in data:
            product_obj = False
            if item.get('product_no_erp') or item.get('product_no_koprol'):
                product_obj = self.env['product.product'].sudo().search([
                    '|',
                    ('name_template', '=', item['product_no_erp']),
                    ('koprol_code', '=', item['product_no_koprol'])
                ], limit=1)

            if product_obj:
                if product_obj.last_modified_date and datetime.strptime(product_obj.last_modified_date, "%Y-%m-%d %H:%M:%S") > datetime.strptime(item['last_modified_koprol'], "%Y-%m-%d %H:%M:%S"):
                    continue
            
            
            product_type = 'product'
            if item['product_type'] == 'Consumable':
                product_type = 'consu'
            elif item['product_type'] == 'Service':
                product_type = 'service'

            
            category_obj = self.env['product.category'].sudo().search([('name','=',item['category_code'])])
            if not category_obj:
                category_obj = self.env['product.category'].sudo().search([('name','=','Umum')])

            tax_obj = self.env['account.tax'].sudo().search([('name','ilike',item['default_purchase_tax'])],limit=1)

            vals = {
                'name': item['product_name'],
                'default_code': item['product_name'],
                'description': item['alias_name'],
                'koprol_code': item['product_no_koprol'],
                'active': item['active_status'],
                'last_modified_date': item['last_modified_koprol'],
                'type': product_type,
                'is_asset': True,
                'categ_id': category_obj.id,
                'taxes_id': [tax_obj.ids], 
                'supplier_taxes_id': [tax_obj.ids]
            }
            if product_obj:
                product_obj.sudo().write(vals)
            else:
                product_obj = self.env['product.template'].sudo().create(vals)