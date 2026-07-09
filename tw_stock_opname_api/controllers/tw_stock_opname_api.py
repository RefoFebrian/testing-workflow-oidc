import base64
from datetime import datetime
from odoo import http
from odoo.http import request, Response
from odoo.addons.rest_api.controllers.main import check_valid_token, invalid_response, valid_response

try:
    import simplejson as json
except ImportError:
    import json

import logging
_logger = logging.getLogger(__name__)


class ControllerREST(http.Controller):
    def _get_default_main_dealer_code(self):
        return self.env['res.company'].get_default_main_dealer_code()

    @http.route('/api/stock_opname/<version>/post_create_stock_opname', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_create_stock_opname(self, version, **post):
        post = json.loads(request.httprequest.get_data(as_text=True))
        uid = request.session.uid
        employee_obj = request.env['hr.employee'].sudo().search([('user_id', '=', uid)], limit=1)

        mandatory_fields = [ 'start_date', 'end_date', 'date' ]
        fields = [mandatory for mandatory in mandatory_fields if mandatory not in post]
        if len(fields):
            info = f"Parameter {fields} is not supplied!"
            message = 'Parameter is missing or invalid',
            return invalid_response(400, message, info)
            
        if post.get('end_date') < post.get('start_date'):
            info = 'Parameter is missing or invalid'
            message = 'End Date tidak boleh kurang dari Start Date'
            return invalid_response(400, message, info)
        
        branch_obj = request.env['res.company'].sudo().search([('code', '=', self._get_default_main_dealer_code())], limit=1)
        create_stock_opname = request.env['tw.stock.opname'].sudo().create({
            'name': request.env['ir.sequence'].suspend_security().get_sequence_code('SO',branch_obj.code),
            'company_id': branch_obj.id,
            'date': post.get('date'),
            'periode_awal': post.get('start_date'),
            'periode_akhir': post.get('end_date'),
            'employee_id': employee_obj.id,
        })

        if not create_stock_opname:
            info = 'Failed'
            message = 'Failed creating Stock Opname!'
            return invalid_response(400, message, info)

        return valid_response(200,{'no_so': create_stock_opname.name})

    @http.route('/api/stock_opname/<version>/post_update_stock_opname', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_update_stock_opname(self, version, **post):
        post = json.loads(request.httprequest.get_data(as_text=True))
        uid = request.session.uid
        employee_obj = request.env['hr.employee'].sudo().search([('user_id', '=', uid)], limit=1)

        mandatory_fields = [ 'opname_id', 'product_list', 'lokasi' ]
        fields = [mandatory for mandatory in mandatory_fields if mandatory not in post]
        if len(fields):
            info = f"Parameter {fields} is not supplied!"
            message = 'Parameter is missing or invalid',
            return invalid_response(400, message, info)

        product_list = post.get('product_list')
        lokasi = post.get('lokasi')
        opname_id = post.get('opname_id')

        opname_obj = request.env['tw.stock.opname'].sudo().browse(int(opname_id))
        if not opname_obj.exists():
            info = "Opname record not found."
            message = "Data Not Found"
            return invalid_response(400, message, info)

        location_obj = request.env['stock.location'].sudo().search([
            ('complete_name', '=', str(lokasi)),
            ('company_id', '=', opname_obj.company_id.id)
        ])
        
        opname_detail_obj = request.env['tw.stock.opname.detail'].sudo().search([
            ('opname_id', '=', int(opname_id)),
            ('employee_id', '=', employee_obj.id),
            ('location_id', '=', int(location_obj.id))
        ])
        if not opname_detail_obj:
            info = "Lokasi Tidak Sesuai."
            message = "Lokasi Binbox tidak sesuai dengan PIC"
            return invalid_response(400, message, info)
        
        product_list_create = []
        for opname in product_list:
            product_code = opname.get('product_code').strip()
            qty = opname.get('qty')
            if not qty:
                request._cr.rollback()
                info = "Parameter qty is not supplied!"
                message = "Parameter is missing or invalid"
                return invalid_response(400, message, info)

            product_obj= request.env['product.product'].sudo().search([('default_code', '=', str(product_code))], limit=1)
            if not product_obj:
                product_code = str(product_code).replace('-','').replace('‒', '')
                product_obj = request.env['product.product'].sudo().search([
                    ('default_code', '=', str(product_code))
                ], limit=1)

            if not product_obj:
                request._cr.rollback()
                info = f"Product {product_code} Tidak Ditemukan di Master Part."
                message = "Data Not Found"
                return invalid_response(400, message, info)

            product_list_create.append(str(product_code))
            detail_obj = request.env['tw.stock.opname.detail'].sudo().search([
                ('opname_id', '=', int(opname_id)),
                ('location_id', '=', int(location_obj.id)),
                ('product_code', '=', str(product_code)),
            ], limit=1)
            
            qty_system = detail_obj.qty_system or 0
            selisih =  qty - qty_system
            perhitungan_ke = (detail_obj.perhitungan_ke or 0) + 1

            state = 'done' if selisih == 0 else 'selisih'
            if qty_system == 0 or not qty_system:
                state = 'anomali'
                
            vals = {
                'count_date':datetime.now(),
                'qty_count': int(qty),
                'selisih': int(selisih), 
                'state': state, 
                'is_recount': False, 
                'perhitungan_ke' : perhitungan_ke,
            }

            if detail_obj.state == 'anomali':
                vals.update({ 'employee_id': employee_obj.id })
                    
            if not detail_obj:
                state = 'anomali'
                vals.update({
                    'location_id': int(location_obj.id),
                    'product_code': product_code,
                    'product_id': product_obj.id,
                    'employee_id': employee_obj.id,
                    'qty_system' : 0,
                    'opname_id': int(opname_id),
                    'state': state
                })
                detail_obj = request.env['tw.stock.opname.detail'].sudo().create(vals)
            else:
                if detail_obj.state not in ('open', 'anomali'):
                    request._cr.rollback()
                    info = "Qty Stock sudah terinput untuk Transaksi Opname tsb ."
                    message = "Failed"
                    return invalid_response(400, message, info)
                detail_obj.sudo().write(vals)

            request.env['tw.stock.opname.history'].sudo().create({
                'opname_detail_id' : detail_obj.id,
                'employee_id' : employee_obj.id,
                'count_date' : datetime.now(),
                'perhitungan_ke' : perhitungan_ke,
                'state' : state,
                'qty_count': qty
            })

        for not_count in opname_detail_obj:
            if not_count.state != 'anomali' and not_count.product_code not in product_list_create:
                perhitungan = (not_count.perhitungan_ke or 0) + 1

                not_count.sudo().write({
                    'count_date':datetime.now(),
                    'qty_count': 0,
                    'selisih': 0 - not_count.qty_system, 
                    'state': 'selisih', 
                    'is_recount': False, 
                    'perhitungan_ke' : perhitungan,
                })

                request.env['tw.stock.opname.history'].sudo().create({
                    'opname_detail_id' : not_count.id,
                    'employee_id' : employee_obj.id,
                    'count_date' : datetime.now(),
                    'perhitungan_ke' : perhitungan,
                    'state' : 'selisih',
                    'qty_count': 0
                })

        return valid_response(200,'')

    @http.route('/api/stock_opname/<version>/get_location_detail', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token 
    def get_location_detail(self, version, **params):
        uid = request.session.uid
        employee_obj = request.env['hr.employee'].sudo().search([('user_id', '=', uid)], limit=1)
        lokasi = params.get('lokasi', None)
        # branch_code = params.get('branch_code', self._get_default_main_dealer_code())
        
        if not lokasi :
            info = 'Parameter lokasi is empty!'
            message = 'Parameter is missing or invalid'
            return invalid_response(400, message, info)
            
        # branch_obj = request.env['res.company'].sudo().search([('code','=',branch_code)], limit=1)
        # if not branch_obj :
        #     info = f'Branch Code {branch_code} Not Found!'
        #     message = 'Parameter is missing or invalid!'
        #     return invalid_response(400, message, info)

        query = f"""
            SELECT sl.complete_name lokasi
                , opname.id as opname_id
            FROM tw_stock_opname_detail detail
            LEFT JOIN tw_stock_opname opname ON opname.id = detail.opname_id
            LEFT JOIN stock_location sl ON sl.id = detail.location_id
            WHERE date_part('month', opname.date) = date_part('month', now())
            AND date_part('year', opname.date) = date_part('year', now())
            AND opname.division = 'Sparepart'
            AND detail.employee_id = {employee_obj.id}
            AND sl.name = '{lokasi}'
            GROUP BY sl.complete_name, opname.id
        """
        request._cr.execute (query)
        data = request._cr.dictfetchall()
        if not data:
            info = 'PIC ditugaskan pada lokasi tersebut tidak sesuai.'
            message = 'Data Not Found'
            return invalid_response(400, message, info)
        return valid_response(200,data)

    @http.route('/api/stock_opname/<version>/get_summary_opname', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token 
    def get_summary_opname(self, version, **params):
        uid = request.session.uid
        query = f"""
            SELECT opname.id as opname_id
                , opname.name
                , count(detail) binding
                , count(detail) FILTER (WHERE detail.state != 'open') as done
                , count(detail) FILTER (WHERE detail.state != 'done' and opname.state = 'recount') as recount
                , count(detail) FILTER (WHERE detail.state in ('selisih','anomali') and opname.state = 'recount') as recount_done
                , count(detail) FILTER (WHERE detail.state = 'open'and opname.state = 'recount') as recount_draft
            FROM tw_stock_opname opname
            LEFT JOIN tw_stock_opname_detail detail ON opname.id = detail.opname_id
            LEFT JOIN hr_employee emp ON emp.id = detail.employee_id
            WHERE opname.state in ('in_progress','recount')
            AND emp.user_id = {uid}
            AND opname.division = 'Sparepart'
            GROUP BY opname.name, opname.id
            ORDER BY opname.id DESC LIMIT 1
        """
        request._cr.execute(query)
        data = request._cr.dictfetchone()
        if not data:
            info = 'Data summary untuk user tersebut kosong/tidak ditemukan.'
            return invalid_response(400, 'Data Not Found', info,version)
        return valid_response(200,data)
    
    @http.route('/api/stock_opname/<version>/get_binbox_list', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token 
    def get_binbox_list(self, version, **params):
        uid = request.session.uid

        lokasi = params.get('lokasi', None)
        if not lokasi :
            info = 'Parameter lokasi is empty!'
            message = 'Parameter is missing or invalid'
            return invalid_response(400, message, info)

        query = f"""
            SELECT CASE WHEN string_agg(DISTINCT detail.state,'') = 'open' THEN 'draft' else 'done' end as state
                , json_agg(detail.*) as product_list
            FROM (
                SELECT detail.product_code
                    , sl.complete_name lokasi
                    , detail.state
                    , COALESCE(detail.qty_count,0) qty
                FROM tw_stock_opname opname
                LEFT JOIN tw_stock_opname_detail detail ON opname.id = detail.opname_id
                LEFT JOIN stock_location sl ON sl.id = detail.location_id
                LEFT JOIN hr_employee emp ON emp.id = detail.employee_id
                WHERE opname.state in ('in_progress','recount')
                AND opname.division = 'Sparepart'
                AND sl.complete_name = '{lokasi}'
                AND emp.user_id = {uid}
                AND detail.state != 'open'
            ) detail
        """
        request._cr.execute (query)
        data =  request._cr.dictfetchall()
        if not data:
            info = 'Data Tidak Ditemukan'
            message = 'Not Found'
            return invalid_response(400, message, info)
        return valid_response(200,data)
    
    @http.route('/api/stock_opname/<version>/get_binbox_detail', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_binbox_detail(self, version, **params):
        uid = request.session.uid
        employee_obj = request.env['hr.employee'].sudo().search([('user_id', '=', uid)], limit=1)

        lokasi = params.get('lokasi', None)
        if not lokasi:
            info = 'Parameter lokasi is empty!'
            message = 'Parameter is missing or invalid'
            return invalid_response(400, message, info)
        
        opname_id = params.get('opname_id')
        if not opname_id:
            request._cr.rollback()
            error = 'Parameter is missing or invalid'
            info = "Parameter opname_id is not supplied!"
            return invalid_response(400, error,info)
        
        query = f""" 
            SELECT binbox.complete_name lokasi
                , opname.id as opname_id
            FROM tw_stock_opname_detail detail
            LEFT JOIN tw_stock_opname opname ON opname.id = detail.opname_id
            LEFT JOIN stock_location binbox ON binbox.id = detail.location_id
            LEFT JOIN hr_employee emp ON emp.id = detail.employee_id
            WHERE date_part('month', opname.date) = date_part('month', now())
            AND date_part('year', opname.date) = date_part('year', now())
            AND opname.division = 'Sparepart'
            AND opname.id = {opname_id}
            AND binbox.complete_name = '{lokasi}'
            AND emp.user_id = {uid}
            GROUP BY binbox.complete_name,  opname.id
        """
        request._cr.execute (query)
        data =  request._cr.dictfetchall()
        if not data:
            info = 'Data Tidak Ditemukan'
            message = 'Not Found'
            return invalid_response(400, message, info)
        return valid_response(200,data)

    @http.route('/api/stock_opname/<version>/get_pic_list', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token 
    def get_pic_list(self, version, **params):
        opname_id = params.get('opname_id', None)
        if not opname_id :
            info = 'Parameter opname_id is empty!'
            message = 'Parameter is missing or invalid'
            return invalid_response(400, message, info)

        
        where = ''
        if opname_id:
            where += f" AND opname.id = {opname_id}"

        query = f"""
            SELECT pic.name pic
                , json_agg(sl.name) lokasi
                , opname.name no_so
                , opname.id id_so
            FROM tw_stock_opname_detail detail
            LEFT JOIN tw_stock_opname opname ON detail.opname_id = opname.id
            LEFT JOIN stock_location sl ON sl.id = detail.location_id
            LEFT JOIN hr_employee pic ON pic.id = detail.employee_id
            WHERE 1=1
            {where}
            GROUP BY pic.name, opname.name, opname.id
        """
        request._cr.execute (query)
        data =  request._cr.dictfetchall()
        if not data:
            message = json.dumps({ 'status':0, 'message':'Not OK', 'info':'Data Tidak Ditemukan' })
            info = 'Data List Team Tidak Ditemukan'
            message = 'Data Not Found'
            return invalid_response(400, message, info)
        return valid_response(200,data)
    
    @http.route('/api/stock_opname/<version>/get_binbox', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token 
    def get_binbox(self, version, **params):
        uid = request.session.uid

        opname_id = params.get('opname_id')
        if not opname_id :
            info = 'Parameter opname_id is empty!'
            message = 'Parameter is missing or invalid'
            return invalid_response(400, message, info)

        query = f"""
            SELECT sl.complete_name lokasi
                , CASE WHEN string_agg(DISTINCT detail.state,'') = 'open' THEN 'draft' else 'done' end as state
                , opname.id as opname_id
                , detail.is_recount
            FROM tw_stock_opname_detail detail
            LEFT JOIN tw_stock_opname opname ON opname.id = detail.opname_id
            LEFT JOIN stock_location sl ON sl.id = detail.location_id
            LEFT JOIN hr_employee emp ON emp.id = detail.employee_id
            WHERE detail.state != 'anomali'
            AND emp.user_id = {uid}
            AND opname.id =  {opname_id}
            GROUP BY sl.complete_name, opname.id, detail.is_recount
        """
        request._cr.execute (query)
        data =  request._cr.dictfetchall()
        if not data:
            info = 'Tidak Ada daftar lokasi Binbox untuk No. SO tsb.'
            return invalid_response(400, 'Data Not Found', info,version)
        return valid_response(200,data)
    
    @http.route('/api/stock_opname/<version>/get_so_retail', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token 
    def get_list_accessories(self, version, **params):
        uid = request.session.uid
        status = params.get('status')
        query_where = "AND opname.state = 'in_progress'"
        if status:
            query_where = f"AND opname.state = '{str(status)}'"
            
        query = f"""
            SELECT opname.id opname_id
                , loc.id as lokasi_id
                , loc.complete_name as lokasi
                , opname.name as name
                , opname.state as status
                , TO_CHAR(opname.date, 'YYYY-MM-DD HH24:MI:SS') as date
                , CASE
                    WHEN (COUNT(detail.id) filter(where detail.state = 'open')) > 0 THEN 'open'
                    ELSE 'done'
                    END state_so_unit
                , opname.total_data as total_data
            FROM tw_stock_opname opname
            LEFT JOIN tw_stock_opname_detail detail ON opname.id = detail.opname_id
            LEFT JOIN tw_stock_opname_location tsol ON tsol.opname_id= opname.id
            LEFT JOIN tw_stock_opname_accessories sum ON sum.location_id = tsol.id
            LEFT JOIN stock_location loc ON loc.id = detail.location_id
            LEFT JOIN hr_employee emp ON emp.id = detail.employee_id
            WHERE emp.user_id = {uid}
            AND opname.division = 'Unit'
            {query_where}
            GROUP BY opname.id, loc.id
            ORDER BY opname.id
        """
        request._cr.execute (query)
        data =  request._cr.dictfetchall()
        if not data:
            request._cr.rollback()
            error =  'Data Not Found'
            info =  'Tidak Ada daftar list SO untuk dikerjakan.'
            return invalid_response(400, error,info)
        
        return valid_response(200,data)

    @http.route('/api/stock_opname/<version>/get_so_retail_accessories', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token 
    def get_so_accessories(self, version, **params):
        uid = request.session.uid
        employee_obj = request.env['hr.employee'].sudo().search([('user_id', '=', uid)], limit=1)
        status = params.get('status')
        query_where = "AND opname.state = 'in_progress'"
        if status:
            query_where = f"AND opname.state = '{str(status)}'"
            
        query = f"""
            SELECT opname.id opname_id
                , loc.id as lokasi_id
                , loc.complete_name as lokasi
                , opname.name as name
                , opname.state as status
                , TO_CHAR(opname.date, 'YYYY-MM-DD HH24:MI:SS') as date
                , CASE
                    WHEN (COUNT(acc.id) filter(where acc.state = 'open')) > 0 THEN 'open'
                    ELSE 'done'
                    END state_so_accessories
                , COUNT(acc.id) as total_data
            FROM tw_stock_opname opname
            LEFT JOIN tw_stock_opname_accessories acc ON opname.id = acc.opname_id
            LEFT JOIN stock_location loc ON loc.id = acc.location_id
            LEFT JOIN hr_employee emp ON emp.id = acc.employee_id
            WHERE opname.division = 'Unit'
            AND emp.user_id = {uid}
            {query_where}
            GROUP BY opname.id, loc.id
            ORDER BY opname.id
        """
        request._cr.execute (query)
        data =  request._cr.dictfetchall()
        if not data:
            request._cr.rollback()
            error =  'Data Not Found'
            info =  'Tidak Ada daftar list SO Aksesoris untuk dikerjakan.'
            return invalid_response(400, error,info)
        
        return valid_response(200,data)

    @http.route('/api/stock_opname/<version>/post_stockopname', methods=['POST'], type='json', auth='none', csrf=False, json_rpc=False)
    @check_valid_token
    def post_items_so(self, version, **post):
        post = json.loads(request.httprequest.get_data(as_text=True))
        mandatory_fields = [ 'opname_id', 'location_id' ]
        fields = [mandatory for mandatory in mandatory_fields if mandatory not in post]
        if len(fields):
            request._cr.rollback()
            error = 'Parameter is missing or invalid'
            info = f"Parameter {fields} is not supplied!"
            return invalid_response(400, error,info)

        list_kondisi = []
        
        opname_id = post.get('opname_id')
        location_id = post.get('location_id')
        jumlah_unit = post.get('jumlah_unit')
        foto_selfie = post.get('foto_selfie')
        foto_all_stock = post.get('foto_all_stock')
        filename_foto_all_stock=''
        filename_foto_selfie=''

        location_obj = request.env['tw.stock.opname.location'].sudo().search([
            ('location_id', '=', int(location_id)),
            ('opname_id', '=', int(opname_id))
        ])
        if not location_obj:
            request._cr.rollback()
            error =  'Data not found'
            info =  'Lokasi tidak Ditemukan!'
            return invalid_response(400, error,info)
        
        if foto_all_stock:
            filename_foto_all_stock = str('foto_all_stock')+'_'+str(location_obj.id)
            request.env['tw.config.files'].suspend_security().upload_file(filename_foto_all_stock, foto_all_stock)
            
        if foto_selfie:
            filename_foto_selfie = str('foto_selfie')+'_'+str(location_obj.id)
            request.env['tw.config.files'].suspend_security().upload_file(filename_foto_selfie, foto_selfie)
            
        
        rumah_gembok = post.get('rumah_gembok')
        if rumah_gembok:
            opname_detail_obj = request.env['tw.stock.opname.condition'].sudo().search([
                ('location_id', '=', location_obj.id),
                ('code', '=', 'rumah_gembok')
            ], limit=1)
            if opname_detail_obj:
                list_kondisi.append([1,opname_detail_obj.id,{
                    'status_kondisi' : rumah_gembok
                }])

        kunci_gembok = post.get('kunci_gembok')
        if kunci_gembok:
            opname_detail_obj = request.env['tw.stock.opname.condition'].sudo().search([
                ('location_id', '=', location_obj.id),
                ('code', '=', 'kunci_gembok')
            ], limit=1)
            if opname_detail_obj:
                list_kondisi.append([1,opname_detail_obj.id,{
                    'status_kondisi' : kunci_gembok
                }])

        pengaman_unit = post.get('pengaman_unit')
        if pengaman_unit:
            opname_detail_obj = request.env['tw.stock.opname.condition'].sudo().search([
                ('location_id', '=', location_obj.id),
                ('code', '=', 'pengaman_unit')
            ], limit=1)
            if opname_detail_obj:
                list_kondisi.append([1,opname_detail_obj.id,{
                    'status_kondisi' : pengaman_unit
                }])

        kondisi_lain = post.get('kondisi_lain')
        if kondisi_lain:
            opname_detail_obj = request.env['tw.stock.opname.condition'].sudo().search([
                ('location_id', '=', location_obj.id),
                ('code', '=', 'kondisi_lain')
            ], limit=1)
            if opname_detail_obj:
                list_kondisi.append([1,opname_detail_obj.id,{
                    'other_information' : kondisi_lain
                }])
        
        has_accessories = post.get('has_accessories')
        if has_accessories is not None:
            opname_detail_obj = request.env['tw.stock.opname.detail'].sudo().search([
                ('location_id', '=', int(location_id)),
                ('opname_id', '=', int(opname_id))
            ])
            opname_detail_obj.sudo().write({'has_accessories': bool(has_accessories)})

        location_obj.sudo().write({
            'file_foto_selfie' : foto_selfie,
            'filename_upload_foto_selfie' : filename_foto_selfie,
            'file_foto_all_stock' : foto_all_stock,
            'filename_upload_foto_all_stock' : filename_foto_all_stock,
            'jumlah_unit' : jumlah_unit,
            'condition_opname_ids': list_kondisi
        })
        return valid_response(200,'')

    @http.route('/api/stock_opname/<version>/post_accessories', methods=['POST'], type='json', auth='none', csrf=False, json_rpc=False)
    @check_valid_token
    def post_items_accessories(self, version, **post):
        post = json.loads(request.httprequest.get_data(as_text=True))
        mandatory_fields = ['opname_id', 'location_id']
        fields = [mandatory for mandatory in mandatory_fields if mandatory not in post]
        if len(fields):
            request._cr.rollback()
            error = 'Parameter is missing or invalid'
            info = f"Parameter {fields} is not supplied!"
            return invalid_response(400, error, info)

        list_kondisi = []

        opname_id = post.get('opname_id')
        location_id = post.get('location_id')
        jumlah_unit = post.get('jumlah_unit')
        foto_selfie = post.get('foto_selfie')
        foto_all_stock = post.get('foto_all_stock')
        filename_foto_all_stock = ''
        filename_foto_selfie = ''

        location_obj = request.env['tw.stock.opname.accessories.location'].sudo().search([
            ('location_id', '=', int(location_id)),
            ('opname_id', '=', int(opname_id))
        ])
        if not location_obj:
            request._cr.rollback()
            error = 'Data not found'
            info = 'Lokasi tidak Ditemukan!'
            return invalid_response(400, error, info)

        if foto_all_stock:
            filename_foto_all_stock = str('foto_all_stock') + '_' + str(location_obj.id)
            request.env['tw.config.files'].suspend_security().upload_file(filename_foto_all_stock, foto_all_stock)

        if foto_selfie:
            filename_foto_selfie = str('foto_selfie') + '_' + str(location_obj.id)
            request.env['tw.config.files'].suspend_security().upload_file(filename_foto_selfie, foto_selfie)

        rumah_gembok = post.get('rumah_gembok')
        if rumah_gembok:
            opname_detail_obj = request.env['tw.stock.opname.condition'].sudo().search([
                ('accessories_location_id', '=', location_obj.id),
                ('code', '=', 'rumah_gembok')
            ], limit=1)
            if opname_detail_obj:
                list_kondisi.append([1, opname_detail_obj.id, {
                    'status_kondisi': rumah_gembok
                }])

        kunci_gembok = post.get('kunci_gembok')
        if kunci_gembok:
            opname_detail_obj = request.env['tw.stock.opname.condition'].sudo().search([
                ('accessories_location_id', '=', location_obj.id),
                ('code', '=', 'kunci_gembok')
            ], limit=1)
            if opname_detail_obj:
                list_kondisi.append([1, opname_detail_obj.id, {
                    'status_kondisi': kunci_gembok
                }])

        pengaman_unit = post.get('pengaman_unit')
        if pengaman_unit:
            opname_detail_obj = request.env['tw.stock.opname.condition'].sudo().search([
                ('accessories_location_id', '=', location_obj.id),
                ('code', '=', 'pengaman_unit')
            ], limit=1)
            if opname_detail_obj:
                list_kondisi.append([1, opname_detail_obj.id, {
                    'status_kondisi': pengaman_unit
                }])

        kondisi_lain = post.get('kondisi_lain')
        if kondisi_lain:
            opname_detail_obj = request.env['tw.stock.opname.condition'].sudo().search([
                ('accessories_location_id', '=', location_obj.id),
                ('code', '=', 'kondisi_lain')
            ], limit=1)
            if opname_detail_obj:
                list_kondisi.append([1, opname_detail_obj.id, {
                    'other_information': kondisi_lain
                }])

        has_accessories = post.get('has_accessories')
        if has_accessories is not None:
            opname_detail_obj = request.env['tw.stock.opname.detail'].sudo().search([
                ('location_id', '=', int(location_id)),
                ('opname_id', '=', int(opname_id))
            ])
            opname_detail_obj.sudo().write({'has_accessories': bool(has_accessories)})

        location_obj.sudo().write({
            'file_foto_selfie': foto_selfie,
            'filename_upload_foto_selfie': filename_foto_selfie,
            'file_foto_all_stock': foto_all_stock,
            'filename_upload_foto_all_stock': filename_foto_all_stock,
            'jumlah_unit': jumlah_unit,
            'condition_opname_ids': list_kondisi
        })
        return valid_response(200, '')

    @http.route('/api/stock_opname/<version>/post_stockopname_unit', methods=['POST'], type='json', auth='none', csrf=False, json_rpc=False)
    @check_valid_token
    def post_unit_so(self, version, **post):
        post = json.loads(request.httprequest.get_data(as_text=True))
        uid = request.session.uid
        employee_obj = request.env['hr.employee'].sudo().search([('user_id', '=', uid)], limit=1)
        opname_id = post.get('opname_id')
        if not post.get('opname_id'): 
            error = 'Parameter is missing or invalid'
            info = "Parameter opname_id is not supplied!"
            return invalid_response(400, error,info)
        
        opname_obj = request.env['tw.stock.opname'].sudo().search([('id', '=', int(opname_id))],limit=1)
        if not opname_obj: 
            error = 'Data Not Found'
            info = "Stock Opname Tidak Ditemukan"
            return invalid_response(400, error,info)

        detail_opname = []
        for detail in post.get('detail'): 
            mandatory_fields = [
                'location_id',
                'chassis_no',
                'product_id',
                'rfs',
                'lat',
                'long',
            ]        

            fields = [mandatory for mandatory in mandatory_fields if mandatory not in detail]
            if len(fields):
                request._cr.rollback()
                error = 'Parameter is missing or invalid',
                info = f"Parameter {fields} is not supplied!"
                return invalid_response(400, error,info)
                
            location_id = detail.get('location_id')

            opname_detail_obj = request.env['tw.stock.opname.detail'].sudo().search([
                ('opname_id', '=', int(opname_id)),
                ('employee_id', '=', employee_obj.id),
                ('location_id', '=', int(location_id))
            ])
            if not opname_detail_obj:
                request._cr.rollback()
                error =  'Lokasi Tidak Sesuai.'
                info =  'Lokasi tidak sesuai dengan PIC'
                return invalid_response(400, error,info)

            rfs = detail.get('rfs')
            penjelasan_nrfs = detail.get('penjelasan_nrfs')
            chassis_no = detail.get('chassis_no')
            if len(chassis_no.strip()) != 14 :
                request._cr.rollback()
                error =  'Validation Error'
                info = f"Nomor Chassis {chassis_no} harus berjumlah 14 digit"
                return invalid_response(400, error,info)
                
            opname_detail_obj = request.env['tw.stock.opname.detail'].sudo().search([
                ('opname_id', '=', int(opname_id)),
                ('employee_id', '=', employee_obj.id),
                ('location_id', '=', int(location_id)),
                ('chassis_no', '=', chassis_no),
            ])
            
            qty = 1
            qty_system = opname_detail_obj.qty_system or 0
            selisih =  qty - qty_system
            perhitungan_ke = (opname_detail_obj.perhitungan_ke or 0) + 1
            
            state = 'done' if selisih == 0 else 'selisih'

            if qty_system == 0 or not qty_system:
                state = 'anomali'

            vals_history = [[0,0,{
                'employee_id' : employee_obj.id,
                'count_date' : datetime.now(),
                'perhitungan_ke' : perhitungan_ke,
                'state' : state,
                'qty_count': qty
            }]]
            
            lat = detail.get('lat')
            lon = detail.get('long')
            link_maps = "https://www.google.com/maps/?q=%s,%s"%(str(lat).replace(',','.'),str(lon).replace(',','.'))
            
            vals_detail = {
                'count_date':datetime.now(),
                'qty_count': int(qty),
                'selisih': int(selisih),
                'is_recount': False, 
                'perhitungan_ke' : perhitungan_ke,
                'latitude' : lat,
                'longtitude' : lon,
                'maps' : link_maps,
                'rfs' : rfs,
                'penjelasan_nrfs' : penjelasan_nrfs,
                'history_opname_ids': vals_history
            }
            if not opname_detail_obj:
                lot_obj = request.env['stock.lot'].sudo().search([('name','=',detail.get('engine_no'))],limit=1)
                if lot_obj:
                    vals_detail.update({'lot_id' : lot_obj.id})
                
                vals_detail.update({
                    'employee_id' : employee_obj.id,
                    'state' : state,
                    'qty_system' : 0,
                    'location_id' : location_id,
                    'chassis_no' : chassis_no,
                    'product_id' :int(detail.get('product_id')),
                })
                detail_opname.append([0,0,vals_detail])
            else:
                vals_detail.update({
                    'state' : state,
                })
                detail_opname.append([1,opname_detail_obj.id,vals_detail])
        opname_obj.sudo().write({'detail_opname_ids': detail_opname})
        return valid_response(200,'')
    
    @http.route('/api/stock_opname/<version>/upload_image_stockopname', methods=['POST'], type='http', auth='none', csrf=False, json_rpc=False)
    @check_valid_token
    def upload_image_items_so(self, **post):
        uid = request.session.uid
        employee_obj = request.env['hr.employee'].sudo().search([('user_id', '=', uid)], limit=1)
        mandatory_fields = [
                'opname_id',
                'location_id',
                'foto_selfie',
                'foto_all_stock'
            ]  
        
        fields = [mandatory for mandatory in mandatory_fields if mandatory not in post]
        if len(fields):
            request._cr.rollback()
            error = 'Parameter is missing or invalid'
            info = "Parameter %s is not supplied!" %(fields)
            return invalid_response(400, error,info)
        
        opname_id = post.get('opname_id')
        location_id = post.get('location_id')
        foto_selfie = post.get('foto_selfie')
        foto_all_stock = post.get('foto_all_stock')
        filename_foto_all_stock=''
        filename_foto_selfie=''

        location_obj = request.env['tw.stock.opname.location'].sudo().search([
            ('location_id', '=', int(location_id)),
            ('opname_id', '=', int(opname_id))])
        foto_all_stock_base64 = ''
        foto_selfie_base64 = ''

        if foto_all_stock:
            filename_foto_all_stock = foto_all_stock.filename
            foto_all_stock_base64 = base64.b64encode(foto_all_stock.read()).decode('utf-8')
            
        if foto_selfie:
            filename_foto_selfie = foto_selfie.filename
            foto_selfie_base64 = base64.b64encode(foto_selfie.read()).decode('utf-8')
        
        vals_image = {
            'file_foto_selfie' : foto_selfie_base64,
            'filename_upload_foto_selfie' : filename_foto_selfie,
            'file_foto_all_stock' : foto_all_stock_base64,
            'filename_upload_foto_all_stock' : filename_foto_all_stock
        }

        location_obj.sudo().write(vals_image)
        
        return valid_response(200,'')
    
    @http.route('/api/stock_opname/<version>/upload_image_accessories', methods=['POST'], type='http', auth='none', csrf=False, json_rpc=False)
    @check_valid_token
    def upload_image_item_accessories(self, **post):
        uid = request.session.uid
        employee_obj = request.env['hr.employee'].sudo().search([('user_id', '=', uid)], limit=1)
        mandatory_fields = [
                'opname_id',
                'location_id',
                'foto_selfie',
                'foto_all_stock'
            ]  
        
        fields = [mandatory for mandatory in mandatory_fields if mandatory not in post]
        if len(fields):
            request._cr.rollback()
            error = 'Parameter is missing or invalid'
            info = "Parameter %s is not supplied!" %(fields)
            return invalid_response(400, error,info)
        
        opname_id = post.get('opname_id')
        location_id = post.get('location_id')
        foto_selfie = post.get('foto_selfie')
        foto_all_stock = post.get('foto_all_stock')
        filename_foto_all_stock=''
        filename_foto_selfie=''

        accessories_location_obj = request.env['tw.stock.opname.accessories.location'].sudo().search([
            ('location_id', '=', int(location_id)),
            ('opname_id', '=', int(opname_id))])
        
        if not accessories_location_obj:
            request._cr.rollback()
            error =  'Data not found'
            info =  'Accessories Location not found!'
            return invalid_response(400, error,info)

        foto_all_stock_base64 = ''
        foto_selfie_base64 = ''

        if foto_all_stock:
            filename_foto_all_stock = foto_all_stock.filename
            foto_all_stock_base64 = base64.b64encode(foto_all_stock.read()).decode('utf-8')
            
        if foto_selfie:
            filename_foto_selfie = foto_selfie.filename
            foto_selfie_base64 = base64.b64encode(foto_selfie.read()).decode('utf-8')
        
        vals_image = {
            'file_foto_selfie' : foto_selfie_base64,
            'filename_upload_foto_selfie' : filename_foto_selfie,
            'file_foto_all_stock' : foto_all_stock_base64,
            'filename_upload_foto_all_stock' : filename_foto_all_stock
        }

        accessories_location_obj.sudo().write(vals_image)
        
        return valid_response(200,'')
    
    @http.route('/api/stock_opname/<version>/post_image_unit', methods=['POST'], type='http', auth='none', csrf=False)
    @check_valid_token
    def post_image_stockopname(self,version,**post): 
        uid = request.session.uid
        employee_obj = request.env['hr.employee'].sudo().search([('user_id', '=', uid)], limit=1)
        mandatory_fields = [
                'location_id',
                'opname_id',
                'fotos',
            ]
        fields = [mandatory for mandatory in mandatory_fields if mandatory not in post]
        if len(fields):
            request._cr.rollback()
            error = 'Parameter is missing or invalid'
            info = "Parameter %s is not supplied!" %(fields)
            return invalid_response(400, error,info)
        opname_obj = request.env['tw.stock.opname'].sudo().search([
                    ('id', '=', int(post.get('opname_id')))
                ],limit=1)

        if not opname_obj:
            error = 'Data Not Found'
            info = "Stock Opname Tidak Ditemukan"
            return invalid_response(400, error,info)

        location_id = post.get('location_id')
        photos = request.httprequest.files.getlist('fotos')

        vals_list = []

        for photo in photos:
            if not photo:
                error = 'Photo Not Found'
                info = "File Photo is missing or invalid"
                return invalid_response(400, error,info)
            image = base64.b64encode(photo.read())
            if not image:
                error = 'Failed encode Base64 Image'
                info = "File Photo encoing Base64 invalid"
                return invalid_response(400, error,info)
            chassis_no = photo.filename.split('-')[0]
            watermark = photo.filename.split('-')[1].split('.')[0]

            opname_detail_obj = request.env['tw.stock.opname.detail'].sudo().search([
                ('opname_id', '=', opname_obj.id),
                ('employee_id', '=', employee_obj.id),
                ('location_id', '=', int(location_id)),
                ('chassis_no', '=', str(chassis_no)),
            ])
            filename_foto_unit = f"foto_unit_{opname_detail_obj.id}_{chassis_no}"
            foto_unit = request.env['tw.stock.opname'].sudo()._generate_watermark(image, watermark)

            vals_list.append([1, opname_detail_obj.id, {
                'file_foto': foto_unit,
                'filename_foto': filename_foto_unit,
            }])

        opname_obj.sudo().write({'detail_opname_ids': vals_list})
        return valid_response(200,'')

    @http.route('/api/stock_opname/<version>/upload_image_stockopname_unit', methods=['POST'], type='json', auth='none', csrf=False, json_rpc=False)
    @check_valid_token
    def upload_image_unit_so(self, **post):
        post = request.jsonrequest
        uid = request.session.uid

        vals_list = []
        if not post.get('opname_id'):
            request._cr.rollback()
            error = 'Parameter is missing or invalid'
            info = "Parameter opname_id is not supplied!"
            return invalid_response(400, error,info)

        opname_obj = request.env['tw.stock.opname'].sudo().search([
                    ('id', '=', int(post.get('opname_id')))
                ],limit=1)

        if not opname_obj: 
            error = 'Data Not Found'
            info = "Stock Opname Tidak Ditemukan"
            return invalid_response(400, error,info)
        
        for item in post.get('data'):
            mandatory_fields = ['location_id', 'chassis_no', 'foto_unit','watermark']
            fields = [mandatory for mandatory in mandatory_fields if mandatory not in item]
            if fields:
                request._cr.rollback()
                error = 'Parameter is missing or invalid'
                info = f"Parameter {fields} is not supplied or invalid!"
                return invalid_response(400, error,info)
            
            location_id = item.get('location_id')
            chassis_no = item.get('chassis_no')
            foto_unit = item.get('foto_unit')
            watermark = item.get('watermark')

            opname_detail_obj = request.env['tw.stock.opname.detail'].sudo().search([
                ('opname_id', '=', opname_obj.id),
                ('user_id', '=', int(uid)),
                ('location_id', '=', int(location_id)),
                ('chassis_no', '=', chassis_no),
            ])
            
            filename_foto_unit = ''
            if foto_unit:
                filename_foto_unit = f"foto_unit_{opname_detail_obj.id}_{chassis_no}"
                foto_unit = request.env['tw.stock.opname'].sudo()._generate_watermark(foto_unit, watermark)

            vals_list.append([1, opname_detail_obj.id, {
                'file_foto': foto_unit,
                'filename_foto': filename_foto_unit,
            }])

        opname_obj.sudo().write({'detail_opname_ids': vals_list})
        
        return valid_response(200,'')
        
    @http.route('/api/stock_opname/<version>/post_stockopname_accessories', methods=['POST'], type='http', auth='none', csrf=False)
    @check_valid_token
    def post_accessories_so(self, version, **post):
        uid = request.session.uid
        employee_obj = request.env['hr.employee'].sudo().search([('user_id', '=', uid)], limit=1)
        mandatory_fields = [
            'opname_id',
            'location_id',
            'product_id',
            'qty_good',
            'qty_notgood',
            'alasan_notgood',
            'fotos',
        ]

        fields = [mandatory for mandatory in mandatory_fields if mandatory not in post]
        if len(fields):
            request._cr.rollback()
            error = 'Parameter is missing or invalid'
            info = f"Parameter {fields} is not supplied!"
            return invalid_response(400, error,info)
        
        opname_id = post.get('opname_id')
        location_id = post.get('location_id')
        product_id = post.get('product_id')
        qty_good = int(post.get('qty_good'))
        qty_notgood = int(post.get('qty_notgood'))
        alasan_notgood = post.get('alasan_notgood')
        photos = request.httprequest.files.getlist('fotos')

        accessories_obj = request.env['tw.stock.opname.accessories'].sudo().search([
            ('product_id', '=', int(product_id)),
            ('opname_id', '=', int(opname_id)),
            ('location_id', '=', int(location_id))
        ],limit=1)

        if not accessories_obj:
            state = 'anomali'
            vals_accessories = {
                'opname_id': int(opname_id),
                'location_id': int(location_id),
                'product_id': int(product_id),
                'employee_id': employee_obj.id,
                'qty_system': 0,
                'qty_good' : qty_good,
                'qty_not_good' : qty_notgood,
                'alasan_notgood' : alasan_notgood,
                'is_count' : True,
                'state': state,
            }
            accessories_obj = request.env['tw.stock.opname.accessories'].sudo().create(vals_accessories)
        else:
            total_counted_qty = qty_good + qty_notgood
            state = 'done'
            if total_counted_qty != accessories_obj.qty_system:
                state = 'selisih'
            if accessories_obj.qty_system == 0 or not accessories_obj.qty_system:
                state = 'anomali'
            
            vals_accessories = {
                'qty_good' : qty_good,
                'qty_not_good' : qty_notgood,
                'alasan_notgood' : alasan_notgood,
                'is_count' : True,
                'state': state,
            }
            accessories_obj.write(vals_accessories)

        vals_list_images = []
        for photo in photos:
            if not photo:
                error = 'Photo Not Found'
                info = "File Photo is missing or invalid"
                return invalid_response(400, error,info)
            image = base64.b64encode(photo.read())
            if not image:
                error = 'Failed encode Base64 Image'
                info = "File Photo encoing Base64 invalid"
                return invalid_response(400, error,info)

            watermark = photo.filename.split('-')[1].split('.')[0] if '-' in photo.filename else ''

            filename_foto_accessories = f"foto_accessories_{accessories_obj.id}_{product_id}"
            foto_accessories = request.env['tw.stock.opname'].sudo()._generate_watermark(image, watermark)

            vals_list_images.append({
                'file_foto': foto_accessories,
                'filename_upload': filename_foto_accessories,
            })

        if vals_list_images:
            accessories_obj.write(vals_list_images[0])
        
        return valid_response(200,'')
        
    @http.route('/api/stock_opname/<version>/get_detail_stock_opname', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token 
    def get_stockopname_api(self, version, **params):
        url = str(request.httprequest.url).split('/api/')[0]
        limit = 10
        offset = 0
        
        opname_id = params.get('opname_id')
        if not opname_id:
            request._cr.rollback()
            error = 'Parameter is missing or invalid'
            info = "Parameter opname_id is not supplied!"
            return invalid_response(400, error,info)
            
        location_id = params.get('location_id')
        if not location_id:
            request._cr.rollback()
            error = 'Parameter is missing or invalid'
            info = "Parameter location_id is not supplied!"
            return invalid_response(400, error,info)
            
        list_unit = params.get('list_unit')
        list_accessories = params.get('list_accessories')
        
        query_where = ""
        if location_id:
            query_where = f"AND location.id = {int(location_id)}"
        
        if params.get('limit'):
            limit = int(params['limit'])
        if params.get('offset'):
            offset = int(params['offset'])

        query = f"""
            SELECT detail.rfs as rfs
            , detail.chassis_no as name
            , '{url}' || '/web/content/tw.stock.opname.detail/' || detail.id || '/file_foto_show' as foto
            , detail.penjelasan_nrfs as penjelasan_nrfs
            , CASE
                WHEN detail.qty_count isnull THEN False
                ELSE True
                END as is_count
            , CASE
                WHEN detail.qty_system isnull THEN False
                ELSE True
                END as from_sistem
            , COALESCE(product.default_code,'') as unit_series_kode_display
            , detail.latitude as lat
            , detail.longtitude as lon
            , COALESCE(lot.name, '') as engine
            , COALESCE(lot.production_year,'') as tahun_perakitan
            , False as rfs_sistem
            , json_build_object(
                'kode', to_jsonb(product.default_code),
                'nama', to_jsonb(prod_cat.name)
                ) as unit_series
            , json_build_object(
                'kode', to_jsonb(warna.code), 
                'nama', to_jsonb(warna.name->>'en_US')
                ) as color
            , CASE
                WHEN detail.chassis_no notnull AND detail.filename_upload notnull THEN 'done'
                else 'not_done'
            END as state_task
            FROM tw_stock_opname_detail detail
            LEFT JOIN tw_stock_opname opname ON opname.id = detail.opname_id
            LEFT JOIN stock_lot lot ON lot.id = detail.lot_id
            LEFT JOIN product_product product ON detail.product_id = product.id
            LEFT JOIN product_template tmpl ON tmpl.id = product.product_tmpl_id
            LEFT JOIN product_category prod_cat ON tmpl.categ_id = prod_cat.id
            LEFT JOIN product_variant_combination rel ON rel.product_product_id = product.id
            LEFT JOIN product_template_attribute_value temp_val ON rel.product_template_attribute_value_id = temp_val.id
            LEFT JOIN product_attribute_value warna ON temp_val.product_attribute_value_id = warna.id
            LEFT JOIN stock_location location on location.id = detail.location_id
            WHERE opname.division = 'Unit'
            AND detail.state != 'open'
            AND opname.id = {opname_id}
            {query_where}
            ORDER BY detail.opname_id
            LIMIT {limit}
            OFFSET {offset}
        """
        
        if list_accessories:
            query = f"""
                SELECT accessories.product_id as id
                , pt.default_code as name
                , accessories.qty_good as qty_good
                , accessories.qty_not_good as qty_notgood
                , accessories.qty_system as qty_sistem
                , accessories.is_count as is_count
                , accessories.alasan_notgood  as alasan_notgood
                , INITCAP(pc.name) as kategori
                , json_build_object(
                                    'id', pt.categ_id,
                                    'kategori', INITCAP(pc.name),
                                    'kode',pc.name,
                                    'nama', pt.default_code
                                    )::jsonb as accessories
                FROM tw_stock_opname_accessories accessories
                LEFT JOIN tw_stock_opname_location tsol ON tsol.id = accessories.location_id 
                LEFT JOIN tw_stock_opname opname ON opname.id = tsol.opname_id
                LEFT JOIN product_product pp ON pp.id = accessories.product_id
                LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id 
                LEFT JOIN product_category pc ON pc.id = pt.categ_id
                WHERE opname.division = 'Unit'
                AND pc.id notnull
                AND opname.id = {opname_id}
                GROUP BY accessories.id, pc.id, pt.id
                LIMIT {limit}
                OFFSET {offset}
            """
        request._cr.execute (query)

        if list_accessories:
            data =  request._cr.dictfetchall()
        else:
            data =  request._cr.dictfetchall()
        
        data_obj = data
        if list_unit or list_accessories:
            data_obj = data
        return valid_response(200,data_obj)
    
    @http.route('/api/stock_opname/<version>/get_detail_accessories_stock_opname', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token 
    def get_accessories_stockopname_api(self, version, **params):
        url = str(request.httprequest.url).split('/api/')[0]
        limit = 10
        offset = 0
        
        opname_id = params.get('opname_id')
        if not opname_id:
            request._cr.rollback()
            error = 'Parameter is missing or invalid'
            info = "Parameter opname_id is not supplied!"
            return invalid_response(400, error,info)
            
        location_id = params.get('location_id')
        if not location_id:
            request._cr.rollback()
            error = 'Parameter is missing or invalid'
            info = "Parameter location_id is not supplied!"
            return invalid_response(400, error,info)
        
        if params.get('limit'):
            limit = int(params['limit'])
        if params.get('string'):
            string = str(params['string'])
            query_where += f"AND pt.default_code ILIKE '%{string}%'"
        
        if params.get('offset'):
            offset = int(params['offset'])

        query_where = f"AND accessories.location_id = {int(location_id)}"

        query = f"""
            SELECT accessories.product_id as id
            , pt.default_code as name
            , accessories.qty_good as qty_good
            , accessories.qty_not_good as qty_notgood
            , accessories.qty_system as qty_sistem
            , accessories.is_count as is_count
            , accessories.alasan_notgood  as alasan_notgood
            , accessories.state as status
            , INITCAP(pc.name) as kategori
            , '{url}' || '/web/content/tw.stock.opname.accessories/' || accessories.id || '/file_foto_show' as foto
            FROM tw_stock_opname_accessories accessories
            LEFT JOIN tw_stock_opname opname ON opname.id = accessories.opname_id
            LEFT JOIN product_product pp ON pp.id = accessories.product_id
            LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id 
            LEFT JOIN product_category pc ON pc.id = pt.categ_id
            WHERE opname.division = 'Unit'
            AND pc.id notnull
            AND opname.id = {opname_id}
            {query_where}
            GROUP BY accessories.id, pc.id, pt.id
            LIMIT {limit}
            OFFSET {offset}
        """
        request._cr.execute (query)
        data =  request._cr.dictfetchall()
        
        return valid_response(200,data)
    
    @http.route('/api/stock_opname/<version>/get_chassis_list', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_chassis_list(self, version,**params):
        query_where = ''
        query_state = ''
        limit = 10
        offset = 0

        opname_id = params.get('opname_id')
        if not opname_id:
            request._cr.rollback()
            error = 'Parameter is missing or invalid'
            info = "Parameter opname_id is not supplied!"
            return invalid_response(400, error,info)
        
        location_id = params.get('location_id')
        if not location_id:
            request._cr.rollback()
            error = 'Parameter is missing or invalid'
            info = "Parameter location_id is not supplied!"
            return invalid_response(400, error,info)
        
        query_where = f"AND location.id = {int(location_id)}"
        
        if params.get('limit'):
            limit = int(params['limit'])
        if params.get('offset'):
            offset = int(params['offset'])
        if params.get('string'):
            string = params['string']
            query_where += f" AND chassis.chassis_number ilike '%{string}%'"
            query_state = " AND detail.state = 'open'"

        query = f"""
            SELECT chassis.id
                , COALESCE(chassis.chassis_number,'') AS name
                , COALESCE(chassis.name,'') AS engine_no
                , json_build_object(
                    'id', pp.id, 
                    'name', COALESCE('[' || pt.default_code || '] ' || (pt.name->>'en_US')  || ' (' || (pav.name->>'en_US')  || ')','')
                )::jsonb as product
                , COALESCE(detail.state,'') status
            FROM tw_stock_opname opname
            LEFT JOIN tw_stock_opname_detail detail ON detail.opname_id = opname.id
            LEFT JOIN stock_lot chassis ON chassis.id = detail.lot_id
            LEFT JOIN stock_location location on location.id = detail.location_id
            LEFT JOIN product_product pp ON pp.id = chassis.product_id
            LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
            JOIN product_variant_combination as combination on combination.product_product_id = pp.id
            JOIN product_template_attribute_value as ptav on ptav.id = combination.product_template_attribute_value_id
            JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
            WHERE 1=1
            AND opname.division = 'Unit'
            AND opname.state != 'done'
            AND opname.id = {opname_id}
            {query_state}
            {query_where}
            LIMIT {limit}
            OFFSET {offset}
        """
        request._cr.execute(query)
        ress =  request._cr.dictfetchall()
        return valid_response(200,ress)

    @http.route('/api/stock_opname/<version>/get_history_foto', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token 
    def get_history_foto(self, version, **params):
        uid = request.session.uid
        employee_obj = request.env['hr.employee'].sudo().search([('user_id', '=', uid)], limit=1)
        limit = 10
        offset = 0

        if params.get('limit'):
            limit = int(params['limit'])
        if params.get('offset'):
            offset = int(params['offset'])
            
        query = f"""
            SELECT opname.id opname_id
    			, detail.chassis_no as chassis_name
                , chassis.name as engine_number
                , detail.rfs as rfs
    			, detail.penjelasan_nrfs  as reason_nrfs
			    , loc.id as location_id
			    , loc.complete_name as location
			    , opname.name as so_number
			    , opname.code as code
			    , opname.state as status
			    , json_build_object(
			        'id', MAX(pp.id), 
			        'name', MAX(COALESCE('[' || pt.default_code || '] ' || (pt.name->>'en_US')  || ' (' || (pav.name->>'en_US')  || ')',''))
			    )::jsonb as product
			    , TO_CHAR(opname.date, 'YYYY-MM-DD') as date
			    , CASE
			        WHEN (COUNT(detail.id) filter(where detail.state = 'open')) > 0 THEN 'open'
			        ELSE 'done'
			      END state_so_unit
			    , opname.total_data as total_data
			FROM tw_stock_opname opname
			LEFT JOIN tw_stock_opname_detail detail ON opname.id = detail.opname_id
			LEFT JOIN stock_lot chassis ON chassis.id = detail.lot_id
			LEFT JOIN tw_stock_opname_location tsol ON tsol.opname_id= opname.id
			LEFT JOIN tw_stock_opname_accessories sum ON sum.location_id = tsol.id
			LEFT JOIN stock_location loc ON loc.id = detail.location_id
			LEFT JOIN product_product pp ON pp.id = chassis.product_id
			LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
			LEFT JOIN product_variant_combination as combination on combination.product_product_id = pp.id
			LEFT JOIN product_template_attribute_value as ptav on ptav.id = combination.product_template_attribute_value_id
			LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
			WHERE detail.employee_id = {employee_obj.id}
			AND detail.state != 'open'
            AND detail.filename_upload ISNULL
			AND opname.division = 'Unit'
			GROUP BY opname.id, loc.id, loc.complete_name, opname.name, opname.code, 
			         opname.state, opname.date, opname.total_data, detail.chassis_no,
                     chassis.name, detail.rfs, detail.penjelasan_nrfs
			ORDER BY opname.id
			LIMIT {limit}
            OFFSET {offset}
        """
        request._cr.execute (query)
        data =  request._cr.dictfetchall()
        if not data:
            request._cr.rollback()
            error =  'Data Not Found'
            info =  'Tidak ada daftar foto yang gagal kirim'
            return invalid_response(400, error,info)
        
        return valid_response(200,data)
    
    @http.route('/api/stock_opname/<version>/get_detail_lokasi', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token 
    def get_detail_lokasi(self, version, **params):
        url = str(request.httprequest.url).split('/api/')[0]
        uid = request.session.uid
        employee_obj = request.env['hr.employee'].sudo().search([('user_id', '=', uid)], limit=1)
        limit = 10
        offset = 0
        
        opname_id = params.get('opname_id')
        if not opname_id:
            request._cr.rollback()
            error = 'Parameter is missing or invalid'
            info = "Parameter opname_id is not supplied!"
            return invalid_response(400, error,info)
            
        location_id = params.get('location_id')
        if not location_id:
            request._cr.rollback()
            error = 'Parameter is missing or invalid'
            info = "Parameter location_id is not supplied!"
            return invalid_response(400, error,info)
            
        query_where = ""
        if location_id:
            query_where = f" AND location.id = {int(location_id)}"
        
        if params.get('limit'):
            limit = int(params['limit'])
        if params.get('offset'):
            offset = int(params['offset'])
            
        query= f"""
                WITH kondisi_lokasi AS (
                    SELECT kondisi.location_id
                        , kondisi.code code
                        , COALESCE(kondisi.status_kondisi,kondisi.other_information) status
                    FROM tw_stock_opname_condition kondisi
                    LEFT JOIN tw_stock_opname_location lokasi ON lokasi.id = kondisi.location_id
                    WHERE lokasi.opname_id = {opname_id}
                )
                SELECT opname.id as opname_id
                	, branch.name as branch
                    , lokasi.location_id
                    , pic.name pic_name
                    , opname.name as no
                    , opname.code
                    , detail.has_accessories
                    , lokasi.jumlah_unit as jumlah_unit
                    , rumah_gembok.status status_rumah_gembok
                    , kunci_gembok.status status_kunci_gembok
                    , pengaman_unit.status status_pengaman_unit
                    , kondisi_lain.status status_kondisi_lain
                    , CASE 
                        WHEN lokasi.filename_upload_foto_all_stock NOTNULL
                        THEN '{url}' || '/web/content/tw.stock.opname.location/' || lokasi.id || '/file_foto_all_stock_show'
                    ELSE NULL END foto_all_stock
                    , CASE 
                        WHEN lokasi.filename_upload_foto_selfie NOTNULL
                        THEN '{url}' || '/web/content/tw.stock.opname.location/' || lokasi.id || '/file_foto_selfie_show'
                    ELSE NULL END foto_selfie
                FROM tw_stock_opname opname
                LEFT JOIN tw_stock_opname_detail detail ON detail.opname_id = opname.id
                LEFT JOIN tw_stock_opname_location tsol ON tsol.opname_id= opname.id
                LEFT JOIN tw_stock_opname_accessories accessories_all ON accessories_all.location_id = tsol.id
                LEFT JOIN stock_lot chassis ON chassis.id = detail.lot_id
                LEFT JOIN tw_stock_opname_location lokasi ON lokasi.location_id = detail.location_id AND lokasi.opname_id = opname.id
                LEFT JOIN res_company branch ON branch.id = opname.company_id
                LEFT JOIN hr_employee pic ON pic.id = detail.employee_id
                LEFT JOIN stock_location location on location.id = detail.location_id
                LEFT JOIN kondisi_lokasi rumah_gembok on rumah_gembok.location_id = lokasi.id AND rumah_gembok.code = 'rumah_gembok'
                LEFT JOIN kondisi_lokasi kunci_gembok on kunci_gembok.location_id = lokasi.id AND kunci_gembok.code = 'kunci_gembok'
                LEFT JOIN kondisi_lokasi pengaman_unit on pengaman_unit.location_id = lokasi.id AND pengaman_unit.code = 'pengaman_unit'
                LEFT JOIN kondisi_lokasi kondisi_lain on kondisi_lain.location_id = lokasi.id AND kondisi_lain.code = 'kondisi_lain'
                WHERE detail.employee_id = {employee_obj.id}
                AND opname.division = 'Unit'
                AND opname.id = {opname_id}
                {query_where}
                LIMIT {limit}
                OFFSET {offset}
                """
        request._cr.execute(query)
        ress =  request._cr.dictfetchone()
        return valid_response(200,ress)
    
    @http.route('/api/stock_opname/<version>/get_dashboard', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_dashboard(self, version,**params):
        uid = request.session.uid
        employee_obj = request.env['hr.employee'].sudo().search([('user_id', '=', uid)], limit=1)

        opname_id = params.get('opname_id')
        if not opname_id:
            request._cr.rollback()
            error = 'Parameter is missing or invalid'
            info = "Parameter opname_id is not supplied!"
            return invalid_response(400, error,info)
        
        location_id = params.get('location_id')
        if not location_id:
            request._cr.rollback()
            error = 'Parameter is missing or invalid'
            info = "Parameter location_id is not supplied!"
            return invalid_response(400, error,info)
            
        query_where = ""
        if location_id:
            query_where = f" AND detail.location_id = {int(location_id)}"
        
        query = f"""
            SELECT opname.id opname_id
                , count(detail) filter (WHERE detail.state != 'open') as done
                , count(detail) filter (WHERE detail.state = 'open') as open
                , count(detail) filter (WHERE detail.state = 'anomali') as anomali
                , count(detail) filter (WHERE detail.state = 'selisih') as selisih
            FROM tw_stock_opname opname
            LEFT JOIN tw_stock_opname_detail detail ON detail.opname_id = opname.id
            WHERE detail.employee_id = {employee_obj.id}
            AND opname.division = 'Unit'
            AND opname.id = {opname_id}
            {query_where}
            GROUP BY opname.id
        """
        request._cr.execute(query)
        ress =  request._cr.dictfetchone()
        return valid_response(200,ress)

    @http.route('/api/stock_opname/<version>/get_product_segment', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_product_segment(self,version,**post):
        limit = 10
        WHERE = 'WHERE 1=1'
        if post.get('limit'):
            limit = int(post['limit'])
        if post.get('string'):
            string = post['string']
            WHERE += f" AND pc.name ilike '%{string}%'"

        prod = f"""
            SELECT 
                pc.id,
                pc.name
            FROM product_category pc
            {WHERE}
            LIMIT {limit}
        """

        request._cr.execute(prod)
        ress =  request._cr.dictfetchall()
        return valid_response(200,ress)