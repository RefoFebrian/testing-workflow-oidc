from odoo import http
from odoo.http import request
from odoo.addons.rest_api.controllers.main import *
from odoo.exceptions import UserError as Warning, UserError, ValidationError
from datetime import date,timedelta,datetime,date
import logging
_logger = logging.getLogger(__name__)

try:
    import phonenumbers
    from phonenumbers import PhoneNumberFormat
except ImportError:
    phonenumbers = None
    PhoneNumberFormat = None

class ControllerREST(http.Controller):
    @http.route('/api/workshop/<version>/create_part_sales', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def create_part_sales(self, version, **post):
        try:
            cek_group = request.env.user.has_group('tw_part_sales_api.group_button_api_part_sales_single')
            if not cek_group:
                return invalid_response(401,'not_authorized','User tidak memiliki hak akses.')
                
            mandatory_fields = [
                'branch_code',
                'customer_id',
                'line_ids',
            ]

            mandatory_line_fields = [
                'product_code',
                'product_qty',
            ]

            is_valid, error_msg = validate_payload(post, mandatory_fields)
            if not is_valid:
                return invalid_response(400, 'Missing mandatory fields', error_msg)

            # Get Data
            branch_code = post.get('branch_code')
            engine_code = post.get('engine_code')
            plate_number = post.get('plate_number')
            chassis_no = post.get('chassis_no')
            customer_id = post.get('customer_id')
            prod_code = post.get('prod_code')
            ps_number = post.get('ps_number')

            line_ids = post.get('line_ids')

            branch = request.env['res.company'].sudo().search([('code','=',branch_code)],limit=1)
            if not branch:
                return invalid_response(400, 'Branch not found', f"Branch not found: {branch_code}")

            if engine_code:
                lot = request.env['stock.lot'].sudo().search([('name','=',engine_code)],limit=1)
                if not lot:
                    query = """
                            SELECT pp.id as prod_id
                            FROM product_product pp
                            INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id
                            LEFT JOIN product_variant_combination pvc ON pvc.product_product_id = pp.id
                            LEFT JOIN product_template_attribute_value ptav ON ptav.id = pvc.product_template_attribute_value_id
                            LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
                            WHERE pt.default_code = '%s';
                        """ %(prod_code)
                    request._cr.execute(query)
                    ress = request._cr.dictfetchall()
                    if not ress:
                        return invalid_response(400, 'Product not found', f"Product {prod_code} not found")
                    
                    product = ress[0].get('prod_id')
                    product_id = request.env['product.product'].sudo().browse(product)
                    if not product_id:
                        return invalid_response(400, 'Product not found', f"Product {product} not found")
                    
                    create_lot = request.env['stock.lot'].create({
                        'company_id':branch.id,
                        'name':engine_code,
                        'chassis_number':chassis_no,
                        'plate_number':plate_number,
                        'state':'workshop',
                        'product_id':product_id.id,
                    })          
                    if create_lot:
                        lot = create_lot

            product_unit_id = lot.product_id
            # TODO: Mapping dari master Type WO
            payment_term = branch.default_supplier_id.property_payment_term_id.id
            order_line = []

            for line in line_ids:
                is_valid, error_msg = validate_payload(line, mandatory_line_fields)
                if not is_valid:
                    return invalid_response(400, 'Missing mandatory fields', error_msg)
                
                # Get Data Line
                serial_number = line.get('serial_number') # EV
                product_code = line.get('product_code')
                categ_id = line.get('categ_id')
                product_qty = line.get('product_qty')
                diskon = line.get('diskon')
                
                # lot_id = request.env['stock.lot'].sudo().search([('name','=',serial_number)],limit=1) # EV
                product = request.env['product.product'].sudo().search([('default_code','=',product_code)],limit=1)
                if not product:
                    return invalid_response(400, 'Product not found', f"Product {product_code} not found")

                branch_setting_obj = request.env['tw.branch.setting'].search([('company_id','=',branch.id)],limit=1)
                
                pricelist = branch_setting_obj.pricelist_sale_sparepart_id
                price_get = pricelist.sudo()._price_get(product, 1)
                price = price_get[pricelist.id]
                order_line.append([0,False,{
                    'categ_id':product.categ_id.id,
                    'product_id':product.id,
                    # 'lot_id':lot_id.id, #EV
                    'name':product.description,
                    'product_uom_qty':product_qty, 
                    'discount':diskon,
                    'price_unit':price,
                    'product_uom':1,
                }])

            if lot.partner_id:
                customer = lot.partner_id.id

            # CRM
            mobile = customer_id.get('mobile')
            if mobile:
                if mobile[0] in ['0','6']:
                    mobile = self._normalize_with_lib(mobile)
            identification_number = customer_id.get('no_ktp')
            provinsi_code = customer_id.get('provinsi')
            kota_code = customer_id.get('kota')
            kec_code = customer_id.get('kecamatan')
            kel_code = customer_id.get('kelurahan')

            ktp = request.env['res.partner'].sudo().search([
                ('identification_number','=',identification_number),
                ('active','=',True)
            ],limit=1)
            provinsi_obj = request.env['res.country.state'].sudo().search([('code','=',provinsi_code)],limit=1)
            kota_obj = request.env['res.city'].sudo().search([
                ('code','=',kota_code),
                ('active','=',True)
            ],limit=1)
            kecamatan_obj = request.env['res.district'].sudo().search([
                ('code','=',kec_code),
                ('active','=',True)
            ],limit=1)
            kelurahan_obj = request.env['res.sub.district'].sudo().search([
                ('code','=',kel_code),
                ('active','=',True)
            ],limit=1)
            
            if ktp:
                customer = ktp.id # pake data stnk res partner
            else: # create baru
                new_customer = request.env['res.partner'].sudo().create({
                    'name': customer_id.get('customer_name'),
                    'mobile': mobile,
                    'street': customer_id.get('alamat'),
                    'street2': customer_id.get('alamat'),
                    'rt': customer_id.get('rt'),
                    'rw': customer_id.get('rw'),
                    'state_id': provinsi_obj.id if provinsi_obj else False,
                    'city_id': kota_obj.id if kota_obj else False,
                    'district_id': kecamatan_obj.id if kecamatan_obj else False,
                    'sub_district_id': kelurahan_obj.id if kelurahan_obj else False,
                    'is_pkp':False
                })
                customer = new_customer.id
            vals = {
                'company_id': branch.id,
                'date_order':datetime.now(),
                'lot_id':lot.id,
                'chassis_number':lot.chassis_number,
                'ps_number':ps_number,
                'division':'Sparepart',
                'payment_term_id':payment_term,
                'product_id':lot.product_id.id,
                'partner_id':customer,
                'partner_stnk_id':lot.partner_id.id,
                'partner_mobile':mobile,
                'order_line':order_line,
            }
            result = request.env['tw.part.sales'].sudo().create(vals)
        except Exception as e:
            return invalid_response(401,'Failed API POST Work Order',str(e))
    
        return valid_response(200,result.name)

    def _normalize_with_lib(self, s: str, default_region='ID') -> str:
        try:
            num = phonenumbers.parse(s, default_region)
            if not phonenumbers.is_valid_number(num):
                raise ValidationError("Nomor tidak valid. Contoh Nomor yang Valid (+62 812-3456-7890 / 081234567890)")
            return phonenumbers.format_number(num, PhoneNumberFormat.E164).lstrip('+')
        except phonenumbers.NumberParseException:
            raise ValidationError("Gagal parse nomor")
