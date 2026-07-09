from odoo import http
from odoo.http import request
from odoo.addons.tw_api.controllers.main import valid_response, invalid_response, check_sensitive_value
from odoo.addons.rest_api.controllers.main import check_valid_token, validate_payload
from datetime import date,timedelta,datetime,date
import logging
_logger = logging.getLogger(__name__)

class ControllerREST(http.Controller):
    @http.route('/api/workshop/<version>/create_work_order', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def create_work_order(self, version, **post):
        try:
            cek_group = request.env.user.has_group('tw_work_order_api.group_button_api_work_order_single')
            if not cek_group:
                return invalid_response(401,'not_authorized','User tidak memiliki hak akses.')

            mandatory_fields = [
                'branch_code',
                'type',
                'engine_code',
                'chassis_no',
                'plate_number',
                'km',
                'prod_code',
                'prod_warna',
                'reason_to_ahass',
                'fuel',
                'sa_number',
                'customer_id',
                'production_year',
                'purchase_date',
                'relationship_with_the_owner',
                'mechanic_id',
                'line_ids',
            ]

            mandatory_line_fields = [
                'division',
                'product_code',
                'product_uom_qty',
            ]

            is_valid, error_msg = validate_payload(post, mandatory_fields)
            if not is_valid:
                return invalid_response(400, 'Missing mandatory fields', error_msg)

            # Get Data
            branch_code = post.get('branch_code')
            type = post.get('type')
            type_id = request.env['tw.selection'].sudo().search([
                ('value','=',type),
                ('type','=','WorkOrderType'),
                ('active','=',True)
            ],limit=1)
            claim_type_id = False
            if type in ['Claim','KPB','Claim Program','Other']:
                claim_type_id = request.env['tw.selection'].sudo().search([
                    ('value','=',type),
                    ('type','=','WorkOrderClaimType'),
                    ('active','=',True)
                ],limit=1)
            engine_code = post.get('engine_code')
            chassis_no = post.get('chassis_no')
            plate_number = post.get('plate_number')
            customer_id = post.get('customer_id')
            km = post.get('km')
            reason_to_ahass = post.get('reason_to_ahass')
            reason_to_ahass_id = request.env['tw.selection'].sudo().search([
                ('value','=',reason_to_ahass),
                ('type', '=', 'AlasanKeAHASS'),
                ('active', '=', True)
            ],limit=1)
            keluhan_konsumen = post.get('keluhan_konsumen', False)
            fuel = post.get('fuel')
            sa_number = post.get('sa_number')
            prod_code = post.get('prod_code')
            prod_warna = post.get('prod_warna')
            is_event_kpb = post.get('is_event_kpb')
            purchase_date = post.get('purchase_date')
            production_year = post.get('production_year')
            relationship_with_the_owner = post.get('relationship_with_the_owner')
            relationship_with_the_owner_id = request.env['tw.selection'].sudo().search([
                ('value','=',relationship_with_the_owner),
                ('type', '=', 'HubunganDenganPemilik')
            ],limit=1)
            state_pud = post.get('state_pud', False)
            notification = post.get('notification', False)
            consumer_willingness = post.get('consumer_willingness', False)
            check_results = post.get('check_results', False)
            claim_number = post.get('claim_number',False)
            kpb_ke = post.get('kpb_ke',False)

            line_ids = post.get('line_ids')
            branch = request.env['res.company'].sudo().search([('code','=',branch_code)],limit=1)
            if not branch:
                return invalid_response(400, 'Branch not found', f"Branch not found: {branch_code}")

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
                    # WHERE pt.name = '%s' AND pav.code = '%s';
                    # """ %(prod_code,prod_warna)
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

            if fuel == '25%':
                fuel = '25'
            elif fuel == '50%':
                fuel = '50'
            elif fuel == '75%':
                fuel = '75'
            elif fuel == '100%':
                fuel = '100'

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
                division = line.get('division')
                product_uom_qty = line.get('product_uom_qty')
                diskon = line.get('diskon')
                
                lot_id = request.env['stock.lot'].sudo().search([('name','=',serial_number)],limit=1) # EV
                # TODO: Pada existing menggunakan name, di teto menggunakan default_code
                product = request.env['product.product'].sudo().search([('default_code','=',product_code)],limit=1)
                if not product:
                    return invalid_response(400, 'Product not found', f"Product {product_code} not found")

                branch_setting_obj = request.env['tw.branch.setting'].search([('company_id','=',branch.id)],limit=1)
                
                if division == 'Service':
                    pricelist = branch_setting_obj.pricelist_service_id
                    price = request.env['tw.work.order.line']._get_harga_jasa(product,product_uom_qty,product_unit_id,pricelist)
                else:
                    pricelist = branch_setting_obj.pricelist_sale_sparepart_id
                    if type == 'KPB' and kpb_ke == '1' :
                        price = 0
                        obj_categ_service1 = request.env['tw.work.order.line']._get_harga_jasa(product,product_uom_qty,product_unit_id,pricelist)
                        if obj_categ_service1:
                            price = obj_categ_service1.price
                    else :
                        price_get = pricelist.sudo()._price_get(product, 1)
                        price = price_get[pricelist.id]
                order_line.append([0,False,{
                    'division':division,
                    'product_id':product.id,
                    # 'lot_id':lot_id.id if lot_id else False, #TODO: Uncomment jika sudah ada EV
                    'name':self._get_line_name(product),
                    'product_uom_qty':product_uom_qty, 
                    'discount':diskon,
                    'price_unit':price,
                    'product_uom':1,
                    'warranty':0.0,
                }])

            if lot.partner_id:
                customer = lot.partner_id.id

            default_relationship_with_the_owner_obj = request.env['tw.selection'].sudo().search([
                ('type','=','HubunganDenganPemilik'),
                ('name','=','Sendiri')
            ],limit=1)
            if not relationship_with_the_owner_id:
                relationship_with_the_owner_id = default_relationship_with_the_owner_obj
            else:
                relationship_with_the_owner_id = relationship_with_the_owner_id

            # CRM
            pekerjaan = post.get('pekerjaan')
            nip = post.get('mechanic_id')
            mobile = customer_id.get('mobile')
            if mobile:
                if mobile[0] in ['0','6']:
                    mobile = request.env['tw.work.order'].sudo()._normalize_with_lib(mobile)
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
            pekerjaan_obj = request.env['tw.selection'].sudo().search([
                ('name','=',pekerjaan),
                ('type','=','Pekerjaan')
            ],limit=1)
            user_obj = request.env['res.users'].sudo().search([
                ('login','=',nip),
                ('active','=',True)
            ],order='create_date DESC',limit=1)
            
            if lot.company_id.id == branch.id:
                is_own_dealer = 'ya'
            else:
                is_own_dealer = 'tidak'
                
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
                'type_id':type_id.id if type_id else False,
                'claim_type_id':claim_type_id.id if claim_type_id else False,
                'date_order':datetime.now(),
                'kpb_ke':kpb_ke,
                'is_event_kpb':is_event_kpb,
                'lot_id':lot.id,
                'chassis_number':lot.chassis_number,
                'plate_number':lot.plate_number,
                'km':km,
                'relationship_with_the_owner_id':relationship_with_the_owner_id.id if relationship_with_the_owner_id else False,
                'reason_to_ahass_id':reason_to_ahass_id.id if reason_to_ahass_id else False,
                'note': keluhan_konsumen,
                'sa_number':sa_number,
                'division':'Sparepart',
                'fuel':fuel,
                'payment_term_id':payment_term,
                'purchase_date':purchase_date,
                'product_id':lot.product_id.id,
                'partner_id':customer,
                'customer_stnk_id':lot.partner_id.id if lot.partner_id else customer,
                'mobile':mobile,
                'production_year':production_year,
                'job_id':pekerjaan_obj.id if pekerjaan_obj else False,
                'is_own_dealer':is_own_dealer,
                'mechanic_id':user_obj.id if user_obj else False,
                'order_line':order_line,
                'state_lcr':state_pud,
                'notification':notification,
                'consumer_willingness':consumer_willingness,
                'check_results':check_results,
                'claim_number':claim_number
            }
            result = request.env['tw.work.order'].sudo().create(vals)
            _logger.error('Work Order Created: %s >>>> Vals: %s' % (result.name, vals))
        except Exception as e:
            return invalid_response(401,'Failed API POST Work Order',str(e))
    
        return valid_response(200,result.name)

    def _get_line_name(self,product_obj):        
        # Get product name and description
        name = product_obj.display_name
        if product_obj.description_sale:
            name += '\n' + product_obj.description_sale
        return name

    @http.route('/api/workshop/<version>/get_detail_wo/', methods=['GET'], type='http', auth='public', csrf=False)
    def get_detail_work_order(self, version, **params):
        tw_api_log = request.env['tw.api.log']
        url = '/api/workshop/%s/get_detail_wo/' % version
        name = 'Get Detail WO'
        request_time = datetime.now()

        get_no_wo = params.get('md_reference_pkb')
        if not get_no_wo:
            return invalid_response(400, 'Bad Request', "Parameter 'md_reference_pkb' tidak boleh kosong!")
        
        work_order_obj = request.env['tw.work.order'].sudo().search([('md_reference_pkb', '=', get_no_wo)])
        data_work_order = []
        for work_order in work_order_obj:
            list_work_order_line = []
            for work_line in work_order.order_line:
                list_work_order_line.append({
                    'id': work_line.id, 
                    'product_code': work_line.product_id.default_code,
                    'division': work_line.division, 
                    'price_unit': work_line.price_unit, 
                    'product_name': work_line.product_id.name,
                })
            data_work_order.append({
                'id': work_order.id, 
                'name': work_order.name,
                'customer_name': work_order.customer_stnk_id.name if work_order.customer_stnk_id else '', 
                'customer_no_stnk': work_order.customer_stnk_id.identification_number if work_order.customer_stnk_id else '', 
                'confirm_date': work_order.confirm_date.strftime('%Y-%m-%d %H:%M:%S') if work_order.confirm_date else '', 
                'amount_untaxed': work_order.amount_untaxed, 
                'amount_total': work_order.amount_total,
                'amount_tax': work_order.amount_tax,
                'work_order_line_ids' : list_work_order_line,
            })
        data = {
            'status': 200,
            'message': 'success',
            'response': data_work_order
        }

        response_time = datetime.now()
        tw_api_log.sudo().create_api_log(name, url, 'Sukses', url, None, None, None, reference='tw_work_order')
            
        if data:
            return valid_response(status=200, data=data)
        else:
            return invalid_response(400, 'Bad Request', "Data not found!")
        
    @http.route('/api/account_invoice/<version>/get_detail_invoice/', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_detail_account_invoice(self, version, **params):
        get_no_wo = params.get('no_wo')
        get_no_hp = params.get('no_hp')
        get_tgl_invoice = params.get('tgl_invoice')
        if not get_no_wo and not get_no_hp:
            return invalid_response(400, 'Bad Request', "Parameter 'no_wo' atau 'no_hp' tidak boleh kosong!")
        
        list_of_pilot_branch_code = ()
        pilot_obj = request.env['tw.pilot.project'].sudo().search([
            ('name','=','TW Payment Machine WO'),
            ('active','=',True)
        ])
        if pilot_obj:
            list_of_pilot_branch_code = tuple([str(branch.code) for branch in pilot_obj.company_ids])
        
        # Build parameterized query
        query_conditions = []
        query_params = []

        if list_of_pilot_branch_code:
            placeholders = ','.join(['%s'] * len(list_of_pilot_branch_code))
            query_conditions.append(" AND branch.code IN (%s)" % placeholders)
            query_params.extend(list_of_pilot_branch_code)
        if get_no_wo:
            query_conditions.append(" AND wo.name = %s")
            query_params.append(str(get_no_wo))
        if get_no_hp:
            query_conditions.append(" AND wo.mobile = %s")
            query_params.append(str(get_no_hp))
        if get_tgl_invoice:
            query_conditions.append(" AND invoice.invoice_date = %s")
            query_params.append(str(get_tgl_invoice))
        
        query_where = ''.join(query_conditions)

        query = """
            SELECT 
            invoice.id as invoice_id
            ,branch.id as company_id
            ,branch.name as branch_name
            ,invoice.name as name_invoice
            ,wo.name as no_wo
            ,wo.plate_number as no_plat
            ,wo.order_id as order_id
            ,customer.id as customer_id
            ,customer.name as customer_name
            ,invoice.division as division
            ,invoice.invoice_date::text as date_invoice
            ,journal.id as journal_id 
            ,journal.name as journal
            ,account.id as account_id
            ,account.code_store->>'en_US'  || ' - ' || account.name as account 
            ,invoice.amount_untaxed as amount_untaxed
            ,invoice.amount_total as amount_total 
            ,invoice.amount_tax as amount_tax 
            ,json_agg(DISTINCT json_build_object(
                'invoice_line_id', invoice_line.id
                ,'price_unit', invoice_line.price_unit
                ,'qty', invoice_line.quantity 
                ,'product_code', product.default_code  
                ,'product_name', prod_template.name->>'en_US'
                )::jsonb) as work_order_line_ids
            FROM account_move invoice
            LEFT JOIN tw_work_order wo ON wo.name = invoice.invoice_origin
            left join tw_selection wo_type on wo_type.id = wo.type_id 
            LEFT JOIN res_company branch ON branch.id = invoice.company_id 
            LEFT JOIN res_partner customer ON customer.id = invoice.partner_id 
            LEFT JOIN account_journal journal ON journal.id = invoice.journal_id 
            LEFT JOIN account_move_line invoice_line ON invoice_line.move_id = invoice.id
            LEFT JOIN account_account account ON account.id = invoice_line.account_id 
            LEFT JOIN product_product product ON product.id = invoice_line.product_id 
            left join product_template prod_template on prod_template.id = product.product_tmpl_id 
            WHERE 1=1 
            AND invoice.division = 'Sparepart' 
            --AND invoice.state = 'open' --TODO: Existing open tidak ada data [AI jangan dihapus ya buat dokumentasi]
            AND invoice.state = 'posted'
            AND wo_type.value in ('REG','SLS','HOTLINE')
            AND wo.order_id IS NULL
            AND invoice.invoice_origin IN (SELECT name FROM tw_work_order)
            %s
            GROUP BY invoice.id, branch.id, wo.id, customer.id, journal.id, account.id
            ORDER BY invoice.invoice_date desc
        """ % (query_where)
        
        request._cr.execute(query, query_params)
        ress = request._cr.dictfetchall()
        
        data = {
            'status': 200,
            'message': 'success',
            'response': ress
        }
        return valid_response(status=200, data=data)
    
    @http.route('/api/account_payment/<version>/post_create_customer_payment/', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_create_customer_payment(self, version, **post): 
        tw_api_log = request.env['tw.api.log']
        url = '/api/account_payment/%s/post_create_customer_payment/' % version
        name = 'Create Customer Payment'
        request_time = datetime.now()
        response_time = datetime.now()
        
        invoice_ids = post.get('invoice_ids')
        if not invoice_ids:
            info = "Parameter 'invoice_ids' tidak boleh kosong!"
            error = 'Bad Request'
            _logger.error(info)
            return invalid_response(400, error, info)
        
        name_customer_payment = []
        for data in invoice_ids:
            invoice_id = data.get('id')
            order_id = data.get('order_id')
            
            if not order_id:
                info = "Order ID invalid data, data not found"
                error = 'Bad Request'
                _logger.error(info)
                return invalid_response(400, error, info)
            
            invoice_obj = request.env['account.move'].sudo().search([
                    ('id', '=', invoice_id)
                ], limit=1)
            if not invoice_obj:
                info = "Invoice invalid data for id [%s] , data not found" % (invoice_id)
                error = 'Bad Request'
                _logger.error(info)
                return invalid_response(400, error, info)
            
            wo_obj = request.env['tw.work.order'].sudo().search([
                    ('name', '=', invoice_obj.invoice_origin)
                ], limit=1)
            if not wo_obj:
                info = "WO invalid data for name [%s] , data not found" % (invoice_obj.invoice_origin)
                error = 'Bad Request'
                _logger.error(info)
                return invalid_response(400, error, info)
            
            # Cari receivable move line (debit) untuk reconcile
            move_line_obj = request.env['account.move.line'].sudo().search([
                    ('move_id', '=', invoice_obj.id),
                    ('debit', '>', 0),
                    ('reconciled', '=', False),
                ], limit=1)
            if not move_line_obj:
                info = "Move line receivable tidak ditemukan untuk invoice [%s]" % (invoice_id)
                error = 'Bad Request'
                _logger.error(info)
                return invalid_response(400, error, info)
            
            branch_config = request.env['tw.branch.setting'].sudo().search([('company_id','=',invoice_obj.company_id.id)], limit=1)
            if not branch_config:
                info = "Branch setting tidak ditemukan untuk company [%s]" % (invoice_obj.company_id.name)
                error = 'Bad Request'
                _logger.error(info)
                return invalid_response(400, error, info)
            
            account_setting = branch_config.account_setting_id
            if not account_setting:
                info = "Account setting tidak ditemukan untuk branch [%s]" % (branch_config.name)
                error = 'Bad Request'
                _logger.error(info)
                return invalid_response(400, error, info)
            
            journal_obj = account_setting.wo_customer_payment_journal_id
            if not journal_obj:
                info = "Journal WO Customer Payment belum disetting pada account setting [%s]" % (account_setting.name)
                error = 'Bad Request'
                _logger.error(info)
                return invalid_response(400, error, info)

            # Cari payment method manual payment
            payment_method_obj = request.env['account.payment.method'].sudo().search([
                ('payment_type','=','inbound'),
                ('name','=ilike','%manual payment%')
            ], limit=1)
            if not payment_method_obj:
                info = "Payment Method 'Manual Payment' untuk inbound tidak ditemukan!"
                error = 'Bad Request'
                _logger.error(info)
                return invalid_response(400, error, info)
            
            vals = {
                'company_id':invoice_obj.company_id.id,
                'division':'Sparepart',
                'partner_type':'customer',
                'payment_type':'inbound',
                'type':'customer_payment',
                'partner_id':invoice_obj.partner_id.id,
                'amount':invoice_obj.amount_total,
                'journal_id':journal_obj.id,
                'memo':'Telah DiBayar Melalui Mesin',
                'currency_id':invoice_obj.currency_id.id,
                'account_id':move_line_obj.account_id.id,
                'payment_method_id':payment_method_obj.id,
                'account_number':journal_obj.name,
                'account_holder':invoice_obj.partner_id.name,
                # 'approval_code':order_id, # TODO: Approval code tidak ada di model account.payment
                'line_cr_ids':[[0,False,{
                    'move_line_id': move_line_obj.id,
                    'account_id':move_line_obj.account_id.id,
                    'name':'Telah DiBayar Melalui Mesin',
                    'type':'cr',
                    'is_reconciled':True,
                    'amount':invoice_obj.amount_total,
                }]]
            }
            
            try:
                create_customer_payment = request.env['tw.account.payment'].sudo().create(vals)
                create_customer_payment.action_post()
                wo_obj.sudo().write({'order_id': order_id})
            except Exception as err:
                _logger.error(err)
                request._cr.rollback()
                error = "Gagal Create Customer Payment: %s"%(err)
                tw_api_log.sudo().create_api_log(name, url, str(error), url, None, None, None, reference='tw_api_payment_gateway')
                return {
                    'message' : '%s' %error,
                    'status' : 0,
                }
            name_customer_payment.append(str(create_customer_payment.name))
        
        # * return success response
        result = "Success Create Customer Payment : %s" % name_customer_payment
        response_time = datetime.now()
        tw_api_log.sudo().create_api_log(name, url, result, url, None, None, None, reference='tw_api_payment_gateway')
        return result
