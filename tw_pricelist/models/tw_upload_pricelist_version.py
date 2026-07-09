# 1: imports of python lib
from datetime import datetime, timedelta
from datetime import date
import base64
import xlrd

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwUploadPricelistVersion(models.TransientModel):
    _name = "tw.upload.pricelist.version"
    _description = 'Upload Pricelist Version'

    # 7: defaults methods
    def _get_default_date(self):
        return self.env['res.company'].get_default_date()

    # 8: fields
    file = fields.Binary('File')

    message = fields.Text(string='Message')

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    
    # 13: action methods   
    def action_download_format_file(self):
        type = self._context.get('type')
        if type == 'bbn_sales':
            name = 'Upload Pricelist Version BBN Sales'
        elif type == 'bbn_purchase':
            name = 'Upload Pricelist Version BBN Purchase'
        elif type == 'expedition':
            name = 'Upload Pricelist Version Expedition'
        else:
            name = 'Upload Pricelist Version'

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
        
    def action_import(self):
        type = self._context.get('type')
        company_id = self._context.get('company_id')
        if type == 'bbn_sales' or type == 'bbn_purchase':
            name = 'Upload Pricelist Version BBN'
        elif type == 'expedition':
            name = 'Upload Pricelist Version Expedition'
        else:
            name = 'Upload Pricelist Version'
        
        if not self.file:
            raise Warning('Silahkan input file terlebih dahulu.')
        
        data = base64.decodebytes(self.file)
        excel = xlrd.open_workbook(file_contents=data)
        sh = excel.sheet_by_index(0)
        warning_note = ''
        vals_pricelist_version = []
        for rx in range(1, sh.nrows):
            warning_note, vals_pricelist_version = self._process_import_data(sh, rx, warning_note, vals_pricelist_version,type)
        
        # Raise Warning if any error or incorrect format
        if warning_note:
            raise Warning(warning_note)
        version_obj = self.env['tw.product.pricelist.version'].suspend_security().with_company(company_id).create(vals_pricelist_version)
        
        message = "Upload berhasil disimpan."

        record = self.env['tw.upload.pricelist.version'].create({'message': message})

        form_view_id = self.env.ref('tw_pricelist.tw_upload_pricelist_version_message_view_wizard').id

        return {
            'name': 'Upload Result',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tw.upload.pricelist.version',
            'type': 'ir.actions.act_window',
            'res_id': record.id,
            'views': [(form_view_id, 'form')],
            'target': 'new',
        }


    # 14: private methods
    def _process_import_data(self, sh, rx, warning_note, vals_pricelist_version,type=False):
        # Cek Madatory and skip the loop if any##
        mandatory_fields = [
            'product_pricelist_version',
            'tanggal_mulai',
            'tanggal_selesai',
            'applied_to',
            'fixed_price'
        ]
        values = [sh.cell(rx, ry).value for ry in range(sh.ncols)]
        product_pricelist_version = values[0]
        tanggal_mulai = values[1]
        tanggal_selesai = values[2]
        if not tanggal_mulai or not tanggal_selesai:
            warning_note += f'Terdapat tanggal mulai atau tanggal selesai yang tidak valid di baris {rx} -> Tanggal Mulai: {tanggal_mulai} & Tanggal Selesai: {tanggal_selesai}'
            return warning_note, vals_pricelist_version
        tanggal_mulai = self.normalize_date(tanggal_mulai)
        tanggal_selesai = self.normalize_date(tanggal_selesai)
        applied_to = values[3]
        product_template_default_code = values[4]
        product_variant_code = values[5]
        category = str(values[6])
        service_category = str(values[7])
        cost_based_on = values[8]
        fixed_price = float(values[9]) if values[9] else 0

        # Check Sensitive Case
        if service_category:
            service_category = service_category.upper()

        # TODO: Aktifkan ketika product code
        # if product_template_default_code:
        #     product_template_default_code = product_template_default_code.upper()

        # Extend mandatory based on type
        if type == 'bbn_purchase':
            mandatory_fields.extend([
                'notice_price',
                'process_price',
                'serv_price',
                'serv_area_price',
                'capital_fee_price',
                'city_code'
            ])
        elif type == 'expedition':
            mandatory_fields.extend([
                'cost_based_on'
            ])
            
        if applied_to == 'Category':
            mandatory_fields.extend([
                'category'
            ])
            if category == 'Service':
                mandatory_fields.extend([
                    'service_category'
                ])
        elif applied_to == 'Product':
            mandatory_fields.extend([
                'product_template_default_code'
            ])
        elif applied_to == 'Product Variant':
            mandatory_fields.extend([
                'product_template_default_code',
                'product_variant_code'
            ])

        if not warning_note:
            found = False

            if applied_to == 'Product Variant':
                applied_to = '0_product_variant'
            elif applied_to == 'Product':
                applied_to = '1_product'
            elif applied_to == 'Category':
                applied_to = '2_product_category'
            else:
                applied_to = '3_global'
            
            # Search Product

            product_tmpl_id = False
            product_tmpl_obj = self.env['product.template'].suspend_security().search([
                ('default_code','=',product_template_default_code),
            ], limit=1)
            if not product_tmpl_obj:
                product_tmpl_obj = self.env['product.template'].suspend_security().search([
                    ('name','=',product_template_default_code)
                ], limit=1)
                warning_note += f'Terdapat product name yang tidak valid di baris {rx} -> {product_template_default_code}!'
            
            # Skip, if product not found on Master
            if not product_tmpl_obj:
                return warning_note, vals_pricelist_version
            product_tmpl_id = product_tmpl_obj.id

            # Sesuaikan pencarian warna product_id
            product_id = False
            if product_variant_code:
                product_variant_obj = self.env['product.product'].suspend_security().search([
                    ('product_tmpl_id', '=', product_tmpl_id),
                    ('product_template_variant_value_ids.product_attribute_value_id.code', '=ilike', str(product_variant_code).strip())
                ], limit=1)
                if product_variant_obj:
                    product_id = product_variant_obj.id
                    applied_to = '0_product_variant'
                else:
                    applied_to = '1_product'
            else:
                if applied_to in ['0_product_variant', '1_product']:
                    applied_to = '1_product'
            # End of Search Product

            # Check BBN
            notice_price = False
            process_price = False
            serv_price = False
            serv_area_price = False
            capital_fee_price = False
            city_code = False
            city_id = False
            if type == 'bbn_purchase':
                text = 'Text'
                notice_price = float(values[10]) if values[10] else 0
                process_price = float(values[11]) if values[11] else 0
                serv_price = float(values[12]) if values[12] else 0
                serv_area_price = float(values[13]) if values[13] else 0
                capital_fee_price = float(values[14]) if values[14] else 0
                if isinstance(values[15], float):
                    city_code = str(int(values[15]))
                else:
                    city_code = values[15]
                # Search City
                city_obj = self.env['res.city'].suspend_security().search([
                    ('code','=',city_code)
                ], limit=1)
                if not city_obj:
                    warning_note += f'Terdapat city code yang tidak valid di baris {rx} -> {city_code}!'
                city_id = city_obj.id
            # End of BBN

            # Check Expedition
            cost_based_on_id = False
            if type == 'expedition':
                # Search Cost Based On
                cost_based_on_obj = self.env['tw.selection'].suspend_security().search([
                    ('name','=',cost_based_on)
                ], limit=1)
                if not cost_based_on_obj:
                    warning_note += f'Terdapat cost based on yang tidak valid di baris {rx} -> {cost_based_on}!'
                cost_based_on_id = cost_based_on_obj.id
            # End of Expedition

            # Check Service
            categ_id = False
            service_category_id = False
            if category == 'Service':
                category_obj = self.env['product.category'].get_child_ids('Service')
                if not category_obj:
                    warning_note += f'Terdapat category yang tidak valid di baris {rx} -> {category}!'
                categ_id = category_obj[0]
                
                service_category_obj = self.env['tw.selection'].suspend_security().search([
                    ('name','=',service_category),
                    ('type','=','PricelistServiceCategory')
                ])
                if not service_category_obj:
                    warning_note += f'Terdapat service category yang tidak valid di baris {rx} -> {service_category}!'        
                service_category_id = service_category_obj.id
            elif category == 'Unit':
                category_obj = self.env['product.category'].get_child_ids('Unit')
                if not category_obj:
                    warning_note += f'Terdapat category yang tidak valid di baris {rx} -> {category}!'
                categ_id = category_obj[0]

            pricelist_id = self._context.get('active_id')
            company_obj  = self.env['product.pricelist'].sudo().browse(pricelist_id).company_id

            for header in vals_pricelist_version:
                if header['name'] == product_pricelist_version:
                    header['item_ids'].append([0, 0, {
                        'pricelist_id': pricelist_id,
                        'product_tmpl_id': product_tmpl_id,
                        'product_id': product_id,
                        'company_id': company_obj.id,
                        'applied_on': applied_to,
                        'fixed_price': fixed_price,
                        # Service
                        'categ_id': categ_id,
                        'service_category_id':service_category_id,
                        # BBN
                        'notice_price': notice_price,
                        'process_price': process_price,
                        'serv_price': serv_price,
                        'serv_area_price': serv_area_price,
                        'capital_fee_price': capital_fee_price,
                        'city_id': city_id,
                        # Expedition
                        'cost_based_on_id': cost_based_on_id
                    }])
                    found = True
                    break

            if not found:
                vals_pricelist_version.append({
                    'name': product_pricelist_version,
                    'date_start': tanggal_mulai,
                    'date_end': tanggal_selesai,
                    'pricelist_id': pricelist_id,
                    'active': True,
                    'item_ids': [[0, 0, {
                        'pricelist_id': pricelist_id,
                        'product_tmpl_id': product_tmpl_id,
                        'product_id': product_id,
                        'company_id': company_obj.id,
                        'applied_on': applied_to,
                        'fixed_price': fixed_price,
                        # Service
                        'categ_id': categ_id,
                        'service_category_id':service_category_id,
                        # BBN
                        'notice_price': notice_price,
                        'process_price': process_price,
                        'serv_price': serv_price,
                        'serv_area_price': serv_area_price,
                        'capital_fee_price': capital_fee_price,
                        'city_id': city_id,
                        # Expedition
                        'cost_based_on_id': cost_based_on_id
                    }]]
                })

        return warning_note, vals_pricelist_version

    def normalize_date(self,value):
        # Jika sudah string format YYYY-MM-DD
        if isinstance(value, str):
            try:
                return datetime.strptime(value, '%Y-%m-%d').strftime('%Y-%m-%d')
            except ValueError:
                raise ValueError(f'Format tanggal tidak valid: {value}')

        # Jika angka Excel (float/int)
        elif isinstance(value, (int, float)):
            excel_epoch = datetime(1899, 12, 30)
            return (excel_epoch + timedelta(days=float(value))).strftime('%Y-%m-%d')

        raise ValueError(f'Tipe data tidak didukung: {type(value)}')