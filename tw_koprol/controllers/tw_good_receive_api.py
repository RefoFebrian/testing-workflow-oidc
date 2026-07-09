#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib
import functools
import werkzeug.wrappers
try:
    import simplejson as json
except ImportError:
    import json
import logging
_logger = logging.getLogger(__name__)
from datetime import timedelta,datetime,date
from dateutil.relativedelta import relativedelta
# 2: import of known third party lib
try:
    from packaging import version as parse_version
except ImportError:
    from odoo.tools import parse_version as parse_version

# 3:  imports of odoo
import odoo
from odoo import models, fields, api, _
from odoo import http

# 4:  imports from odoo modules
from odoo.http import request
from odoo.http import Response
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
from odoo.addons.tw_koprol.controllers.main import check_mandatory_fields, create_api_log, invalid_response, valid_response
from odoo.addons.rest_api.controllers.main import check_valid_token
    
class ControllerREST(http.Controller):
    @http.route('/api/v1/integration/goodReceipt/create', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_good_receive_create(self,**post):
        post = json.loads(request.httprequest.get_data(as_text=True))
        po_header = post.get('header')
        po_details = post.get('details')
        vals = {}

        message = 'mandatory_field'
        MANDATORY_FIELDS = [
            'header',
            'details'
        ]
        MANDATORY_HEADER_FIELDS = [
            'company_code',
            'branch_code',
            'vendor_code',
            'purchase_order_no_erp',
            'purchase_order_no_koprol',
            'nomor_surat_jalan_vendor',
            'good_receipt_no_erp',
            'transaction_date',
            'document_date',
            'transaction_type',
            'type'
        ]

        MANDATORY_DETAILS_FIELDS = [
            'po_line_no_erp',
            'product_no',
            'order_qty',
            'receipt_qty',
            'remaining_qty',
            'qty',
            'site',
            'description'
        ]

        ip_address = ''
        detail_message = check_mandatory_fields(post,MANDATORY_FIELDS)

        detail_message += check_mandatory_fields(po_header,MANDATORY_HEADER_FIELDS)
        for data in po_details:
            detail_message += check_mandatory_fields(data,MANDATORY_DETAILS_FIELDS)

        if detail_message:
            request.env['tw.api.log'].sudo().create_api_log(
                name = 'Failed Good Receive Create, %s' %(detail_message),
                url = '/v1/integration/goodReceipt/create',
                description = str(detail_message),
                ip_address = ip_address,
                response = post,
                payload = post,
                header = str(vals),
            )
            return invalid_response(400,message,detail_message)
        
        no_surat_jalan_vendor = po_header.get('nomor_surat_jalan_vendor',False)
        good_receipt_no_erp = po_header.get('good_receipt_no_erp',False)
        po_koprol_number = po_header.get('purchase_order_no_koprol',False)
        po_number = po_header.get('purchase_order_no_erp',False)
        check_good_receive = request.env['stock.picking'].sudo().search([('vendor_picking_number','=',no_surat_jalan_vendor)],limit=1)
        if check_good_receive:
            detail_message = 'Nomor Surat Jalan sudah digunakan, dengan status %s' %(check_good_receive.state)
            
            if check_good_receive.state == 'cancel':
                detail_message = 'Nomor Surat Jalan sudah dibatalkan'
            
            request.env['tw.api.log'].sudo().create_api_log(
                name = 'Failed Good Receive Create, %s' %(detail_message),
                url = '/v1/integration/goodReceipt/create',
                description = str(detail_message),
                ip_address = ip_address,
                response = post,
                payload = post,
                header = str(vals),
            )
            return invalid_response(400, message="Posting GR dengan No SJ %s gagal" %(no_surat_jalan_vendor), detail_message="%s" %(detail_message))

        if po_number:
            po_erp_obj = request.env['purchase.order.asset'].sudo().search([('name','=',po_number)],limit=1)
            if not po_erp_obj:
                request.env['tw.api.log'].sudo().create_api_log(
                name = 'Failed Good Receive Create, PO ERP dengan po_number %s tidak ditemukan !' %(po_number),
                url = '/v1/integration/goodReceipt/create',
                description = str(detail_message),
                ip_address = ip_address,
                response = post,
                payload = post,
                header = str(vals),
            )
                return invalid_response(400, message="Posting GR dengan No SJ %s gagal" %(no_surat_jalan_vendor), detail_message="PO ERP dengan po_number %s tidak ditemukan !" %(po_number))

        supplier_id = po_header.get('vendor_code')
        supplier_obj = request.env['res.partner'].sudo().search([('code','=',supplier_id)],limit=1)
        if not supplier_obj:
            request.env['tw.api.log'].sudo().create_api_log(
                name = 'Failed Good Receive Create,Pemasok dengan ID %s tidak valid untuk penerimaan barang %s' %(supplier_id,po_details[0].get('product_no','')),
                url = '/v1/integration/goodReceipt/create',
                description = str(detail_message),
                ip_address = ip_address,
                response = post,
                payload = post,
                header = str(vals),
            )
            return invalid_response(400, message="Posting GR dengan No SJ %s gagal" %(no_surat_jalan_vendor), detail_message="Supplier dengan vendor_code %s tidak ditemukan !" %(supplier_id))

        branch_code = po_header.get('branch_code',False)
        if branch_code:
            branch_obj = request.env['res.company'].sudo().search([('code','=',branch_code)],limit=1)
            if not branch_obj:
                request.env['tw.api.log'].sudo().create_api_log(
                name = 'Failed Good Receive Create, Branch dengan branch_code %s tidak ditemukan !' %(branch_code),
                url = '/v1/integration/goodReceipt/create',
                description = str(detail_message),
                ip_address = ip_address,
                response = post,
                payload = post,
                header = str(vals),
            )
                return invalid_response(400, message="Posting GR dengan No SJ %s gagal" %(no_surat_jalan_vendor), detail_message='Branch dengan branch_code %s tidak ditemukan !' %(branch_code))
            if branch_obj.id != po_erp_obj.company_id.id:
                request.env['tw.api.log'].sudo().create_api_log(
                name = 'Failed Good Receive Create, Branch dengan branch_code %s tidak sama dengan Branch pada PO ERP !' %(branch_code),
                url = '/v1/integration/goodReceipt/create',
                description = str(detail_message),
                ip_address = ip_address,
                response = post,
                payload = post,
                header = str(vals),
            )
                return invalid_response(400, message="Posting GR dengan No SJ %s gagal" %(no_surat_jalan_vendor), detail_message='Branch dengan branch_code %s tidak sama dengan Branch pada PO ERP' %(branch_code))


        transaction_date = po_header.get('transaction_date',False)
        document_date = po_header.get('document_date',False)
        if document_date == '':
            document_date = False
        transaction_type = po_header.get('transaction_type',False)
        if transaction_type == '':
            transaction_type = False
        type = po_header.get('type')
        message_error = ''
        
        good_receive_obj = request.env['stock.picking']
        
        gr_line = []
        is_cip = False
        for data in po_details:
            qty = 0
            po_line_no_erp_obj = False
            po_line_no_erp = data.get('po_line_no_erp',False)
            product_no = data.get('product_no',False)
            if product_no:
                product_obj = request.env['product.product'].sudo().search(['|',('default_code','=',product_no),('koprol_code','=',product_no)],limit=1)
                if not product_obj:
                    message_error += 'Product dengan product code %s tidak ditemukan ! \n' %(product_no)
            if product_obj:
                po_line_no_erp_obj = request.env['purchase.order.asset.line'].sudo().search([('id','=',int(po_line_no_erp))],limit=1) 
            
            is_cip = product_obj.asset_category_id.is_cip
            
            if not po_line_no_erp_obj:
                message_error += 'PO Line dengan product code %s tidak ditemukan ! \n' %(product_no)
            else: 
                qty_order = data.get('order_qty',0)
                qty_receipt = data.get('receipt_qty',0)
                qty_available = data.get('available_qty',0)
                qty_remaining = data.get('remaining_qty',0)
                qty = data.get('qty',0)

                if qty > po_line_no_erp_obj.product_qty:
                    message_error += 'Tidak dapat menerima lebih dari jumlah yang dipesan untuk produk %s \n' %(product_no)
                
                if qty_order > po_line_no_erp_obj.product_qty:
                    message_error += 'Qty Order melebihi dengan Qty yang ada di PO untuk produk %s \n' %(product_no)

                if qty > qty_order:
                    message_error += 'Persediaan barang yang tersedia tidak mencukupi untuk produk %s \n' %(product_no)

                if qty < 0:
                    message_error += 'Qty pada GR untuk produk %s \n' %(product_no)


            site = data.get('site',False)
            description = data.get('description',False)
            is_asset = po_line_no_erp_obj.is_asset
            if not po_line_no_erp_obj.product_id.asset_category_id and is_asset:
                message_error += 'PO Line dengan product code %s tidak memiliki Asset Category ! \n' %(product_no)
            
            if message_error:
                continue
            
                 
            gr_line.append([0,0,{
                    'purchase_order_id': po_erp_obj.id,
                    'purchase_order_line_id': po_line_no_erp_obj.id,
                    'product_id': product_obj.id,
                    'name':description,
                    'qty':qty,
                    'qty_remaining':qty_remaining,
                    'qty_receipt':qty_receipt,
                    'qty_order':qty_order,
                    'qty_available':qty_available,
                    'is_asset': is_asset,
                    'price': po_line_no_erp_obj.price_unit,
                    'tax_ids' : [(6,0,po_line_no_erp_obj.taxes_id.ids)],
                    'asset_category_id' : po_line_no_erp_obj.product_id.asset_category_id.id,
                    'description' : po_line_no_erp_obj.product_id.name,
                    'is_cip': po_line_no_erp_obj.product_id.asset_category_id.is_cip
                }])

        if message_error:
            request.env['tw.api.log'].sudo().create_api_log(
                name = 'Failed Good Receive Create, %s !' %(message_error),
                url = '/v1/integration/goodReceipt/create',
                description = str(detail_message),
                ip_address = ip_address,
                response = post,
                payload = post,
                header = str(vals),
            )
            return invalid_response(400, message="Posting GR dengan No SJ %s gagal" %(no_surat_jalan_vendor), detail_message=message_error)

        picking_type_obj = request.env['stock.picking.type'].with_context({'is_asset':True}).get_picking_type('incoming', branch_obj.id, 'Umum')
        vals = {
                'company_id' : branch_obj.id,
                'partner_id' : supplier_obj.id,
                'origin': po_number,
                'vendor_picking_number': no_surat_jalan_vendor,
                'division' : 'Umum',
                'move_asset_ids' : gr_line,
                'transaction_type': transaction_type,
                'date': transaction_date,
                'date_document': document_date,
                'is_asset': True,
                'type': type,
                'note': 'GR KOPROL %s' %(no_surat_jalan_vendor),
                'picking_type_id': picking_type_obj.id,
                'location_id':picking_type_obj.default_location_src_id.id,
                'location_dest_id':picking_type_obj.default_location_dest_id.id,
            }
        try:
            good_receive_obj = good_receive_obj.sudo().create(vals)
            good_receive_obj.sudo().action_request_approval()
            good_receive_obj.sudo().approva_all_approval(reason='Auto Approve (Koprol)')
            # good_receive_obj.sudo().action_open()

            data = {
                'nomor_surat_jalan_vendor': no_surat_jalan_vendor,
                'good_receipt_no_erp': good_receive_obj.name
                
            }
            return valid_response("success", "GR dengan Surat Jalan %s berhasil diposting dengan nomor %s" %(no_surat_jalan_vendor,good_receive_obj.name), data)
        
        except Exception as err:
            _logger.error(err)
            request._cr.rollback()
            request.env['tw.api.log'].sudo().create_api_log(
                name = 'Failed Good Receive Create, %s !' %(str(err)),
                url = '/v1/integration/goodReceipt/create',
                description = str(detail_message),
                ip_address = ip_address,
                response = post,
                payload = post,
                header = str(vals),
                response_code = 400,
            )
            return invalid_response(400, message="Posting GR dengan No SJ %s gagal" %(no_surat_jalan_vendor), detail_message=str(err))

    @http.route('/api/v1/integration/goodReceipt/getAll', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def get_good_receive_alldata(self,**params):
        params = json.loads(request.httprequest.get_data(as_text=True))
        message = 'mandatory_field'
        results = {}
            
        MANDATORY_FIELDS = [
            'company_code',
            'vendor_code',
            'purchase_order_no_erp',
            'purchase_order_no_koprol',
            'start_transaction_date',
            'end_transaction_date'
        ]

        detail_message = check_mandatory_fields(params,MANDATORY_FIELDS)
        if detail_message:
            create_api_log(
                name = 'Failed Good Receive Get All, %s !' %(detail_message),
                type_hit = 'incoming',
                url = '/v1/integration/goodReceipt/getAll',
                request_type = 'get',
                request_data = params,
                response_code = 400,
                response_data = str(results),
            )
            return invalid_response(400,message,detail_message)

        # limit = int(params['page']) if params.get('page') else 1
        # if params.get('page_size'):
        #     offset = (int(params['page']) - 1) * int(params['page_size']) 
        #     if offset == 0:
        #         offset = 1
        # else:
        #     offset = 10
        query_where = " WHERE 1=1 "
        supplier_id = params.get('vendor_code',False)
        if supplier_id:
            supplier_obj = request.env['res.partner'].sudo().search([('default_code','=',supplier_id)],limit=1)
            if not supplier_obj:
                create_api_log(
                    name = 'Failed Good Receive Get,Pemasok dengan ID %s tidak valid' %(supplier_id),
                    type_hit = 'incoming',
                    url = '/v1/integration/goodReceipt/getAll',
                    request_type = 'get',
                    request_data = params,
                    response_code = 400,
                    response_data = str(results),
                )
                return invalid_response(400, message='Failed Good Receive Get,Pemasok dengan ID %s tidak valid' %(supplier_id), detail_message="Supplier dengan vendor_code %s tidak ditemukan !" %(supplier_id))
            query_where += " AND rp.id = %s" %(supplier_obj.id)
        
        po_koprol_number = params.get('purchase_order_no_koprol',False)
        po_number = params.get('purchase_order_no_erp',False)
        
        if po_koprol_number and po_number:
            query_where += " AND (tpo.name = '%s' OR tpo.reference = '%s')" %(po_number,po_koprol_number)
        
        start_transaction_date = params.get('start_transaction_date',False)
        end_transaction_date = params.get('end_transaction_date',False)
        if start_transaction_date and end_transaction_date:
            query_where += " AND tgr.date >= '%s' AND tgr.date <= '%s'" %(start_transaction_date,end_transaction_date)        

        query = """
        SELECT 
            '14' as company_code,
            wb.code as branch_code,
            rp.default_code as vendor_code,
            tpo.name as purchase_order_no_erp ,
            tpo.reference as purchase_order_no_koprol ,
            tgr.no_surat_jalan_vendor as nomor_surat_jalan_vendor,
            tgr.name as good_receipt_no_erp,
            TO_CHAR(tgr.date + INTERVAL '7 Hours', 'YYYY-MM-DD HH24:MI:SS') AS transaction_date,
            tgr.document_date as document_date,
            tgr.transaction_type as transaction_type,
            tgr.type as type,
            tgr.state as good_receipt_status,
            TO_CHAR(tgr.write_date + INTERVAL '7 Hours', 'YYYY-MM-DD HH24:MI:SS') AS last_modified_erp
            FROM teds_good_receive tgr
            LEFT JOIN teds_good_receive_line tgrl ON tgrl.gr_id = tgr.id
            LEFT JOIN teds_purchase_order tpo on tgrl.purchase_order_id = tpo.id
            LEFT JOIN res_company wb ON tgr.company_id = wb.id
            LEFT JOIN res_partner rp ON tgr.partner_id = rp.id
            LEFT JOIN product_product pp ON pp.id = tgrl.product_id
            {query_where}
            AND tgr.state in ('approved','open','invoiced')
            GROUP BY wb.code,tgr.name,tpo.name,tpo.reference,rp.default_code,tgr.state,tgr.no_surat_jalan_vendor,tgr.date,tgr.write_date,tgr.date,tgr.document_date,tgr.transaction_type
            ,tgr.type
            
            
        """.format(query_where=query_where)
        try:
            request._cr.execute(query)
            results = request._cr.dictfetchall()
        except Exception as err:
            _logger.error(err)
            request._cr.rollback()
            create_api_log(
                name = 'Failed Good Receive Get All, %s !' %(str(err)),
                type_hit = 'incoming',
                url = '/v1/integration/goodReceipt/getAll',
                request_type = 'get',
                request_data = params,
                response_code = 400,
                response_data = str(results),
            )
            return invalid_response(400, message="Data GR Kosong", detail_message=str(err))

        if not results:
            create_api_log(
                name = 'Failed Good Receive Get All, Data GR Kosong !',
                type_hit = 'incoming',
                url = '/v1/integration/goodReceipt/getAll',
                request_type = 'get',
                request_data = params,
                response_code = 400,
                response_data = str(results),
            )
            return invalid_response(400, message="Data GR Kosong", detail_message="")
        
        limit = int(params['page'])
        offset = int(params['page_size'])

        return valid_response("success", "Successfully", data=results, total_data=len(results), total_page=offset , page=limit)

    @http.route('/api/v1/integration/goodReceipt/getData', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def get_good_receive_data(self,**params):
        params = json.loads(request.httprequest.get_data(as_text=True))
        message = 'mandatory_field'
        results= {}

        MANDATORY_FIELDS = [
            'nomor_surat_jalan_vendor',
            'good_receipt_no'
        ]

        detail_message = check_mandatory_fields(params,MANDATORY_FIELDS)
        if detail_message:
            create_api_log(
                name = 'Failed Good Receive Get Data, %s !' %(detail_message),
                type_hit = 'incoming',
                url = '/v1/integration/goodReceipt/getData',
                request_type = 'get',
                request_data = params,
                response_code = 400,
                response_data = str(results),
            )
            return invalid_response(400,message,detail_message)

        query_where = " WHERE 1=1 "
        nomor_surat_jalan_vendor = post.get('nomor_surat_jalan_vendor',False)
        if not nomor_surat_jalan_vendor:
            detail_message = "Nomor Surat Jalan Vendor Kosong !"
            create_api_log(
                name = 'Failed Good Receive Get Data, %s !' %(detail_message),
                type_hit = 'incoming',
                url = '/v1/integration/goodReceipt/getData',
                request_type = 'get',
                request_data = params,
                response_code = 400,
                response_data = str(results),
            )
            return invalid_response(400, message="Data GR Kosong", detail_message=detail_message)
        if nomor_surat_jalan_vendor:
            query_where += " AND tgr.no_surat_jalan_vendor = '%s'" %(nomor_surat_jalan_vendor)
        
        good_receipt_no_erp = post.get('good_receipt_no',False)
        if not good_receipt_no_erp:
            detail_message = "Nomor Good Receipt No ERP Kosong !"
            create_api_log(
                name = 'Failed Good Receive Get Data, %s !' %(detail_message),
                type_hit = 'incoming',
                url = '/v1/integration/goodReceipt/getData',
                request_type = 'get',
                request_data = params,
                response_code = 400,
                response_data = str(results),
            )
            return invalid_response(400, message="Data GR Kosong", detail_message=detail_message)
        if good_receipt_no_erp:
            query_where += " AND tgr.name = '%s'" %(good_receipt_no_erp)
        
        """
        kita ada di level details
        'purchase_order_no_erp', tpo.name,
        'purchase_order_no_koprol', tpo.reference,
        'purchase_order_status', tpo.state

        """

        query = """
            SELECT 
                json_build_object(
                    'company_code', '14',
                    'branch_code', wb.code,
                    'vendor_code', rp.default_code,
                    'nomor_surat_jalan_vendor', tgr.no_surat_jalan_vendor,
                    'good_receipt_no_erp', tgr.name,
                    'transaction_date', TO_CHAR(tgr.date, 'YYYY-MM-DD HH24:MI:SS'),
                    'document_date', TO_CHAR(tgr.document_date, 'YYYY-MM-DD HH24:MI:SS'),
                    'transaction_type', tgr.transaction_type,
                    'type',tgr.type,
                    'good_receipt_status', tgr.state,
                    'purchase_order_no_erp', tpo.name,
                    'purchase_order_no_koprol', tpo.reference,
                    'last_modified_erp', TO_CHAR(tgr.write_date + INTERVAL '7 Hours', 'YYYY-MM-DD HH24:MI:SS')
                ) AS header,
                (
                SELECT json_agg(
                    json_build_object(
                        'po_line_no_erp', tpol.id,
                        'product_no', pp.default_code,
                        'qty', tgrl.qty,
                        'receipt_qty', tpol.qty_receipt,
                        'remaining_qty', tgrl.qty_remaining,
                        'order_qty', tgrl.qty_order,
                        'site', wb.code,
                        'description', pp.name_template
                    )
                ) 
                FROM teds_good_receive_line tgrl 
                LEFT JOIN teds_purchase_order_line tpol ON tgrl.purchase_order_line_id = tpol.id
                LEFT JOIN product_product pp ON pp.id = tpol.product_id
                WHERE tgrl.gr_id = tgr.id
            ) AS details
                FROM teds_good_receive tgr
                LEFT JOIN teds_good_receive_line tgrl ON tgrl.gr_id = tgr.id
                LEFT JOIN res_company wb ON tgr.company_id = wb.id
                LEFT JOIN res_partner rp ON tgr.partner_id = rp.id
                LEFT JOIN product_product pp ON pp.id = tgrl.product_id
                LEFT JOIN LATERAL (select name, reference from teds_purchase_order tpo where tpo.id = tgrl.purchase_order_id order by tgrl.id asc limit 1  ) tpo on true
                {query_where}
                AND tgr.state in ('approved','open')
                AND tgrl.state = 'draft'
                GROUP BY wb.code, rp.default_code, tgr.no_surat_jalan_vendor, 
                tgr.name, tgr.document_date,tgr.transaction_type,tgr.write_date,
                tgr.date,tpo.name,tgr.type, tgr.state, tpo.reference
            """.format(query_where=query_where)
        try:
            request._cr.execute(query)
            results = request._cr.dictfetchone()
        except Exception as err:
            _logger.error(err)
            create_api_log(
                name = 'Failed Good Receive Get Data, %s !' %(str(err)),
                type_hit = 'incoming',
                url = '/v1/integration/goodReceipt/getData',
                request_type = 'get',
                request_data = params,
                response_code = 400,
                response_data = str(results),
            )
            return invalid_response(400, message="Data GR Kosong", detail_message=str(err))

        if not results:
            create_api_log(
                name = 'Failed Good Receive Get Data, Data GR Kosong !',
                type_hit = 'incoming',
                url = '/v1/integration/goodReceipt/getData',
                request_type = 'get',
                request_data = params,
                response_code = 400,
                response_data = str(results),
            )
            return invalid_response(400, message="Data GR Kosong", detail_message="")

        return valid_response("success", "Successfully", results)