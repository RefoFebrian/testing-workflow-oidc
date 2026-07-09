# -*- coding: utf-8 -*-
# from odoo import http
import json
import logging
import urllib.parse

import requests

from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.web import Home

_logger = logging.getLogger(__name__)


class WebsiteForm(Home):
    @http.route('/self-register',methods=['GET'], type='http', auth='public', website=True)
    def base_self_register(self, **kwargs):
        branch_code = False
        return request.redirect('/self-register/%s' %(branch_code))

    @http.route('/self-register/<branch_code>',methods=['GET', 'POST'], type='http', auth='public', website=True, csrf=False)
    def self_register(self,branch_code, **kwargs):
        if branch_code == 'False':
            return http.request.render('website_self_register.self_register_non_active', {
                'message': "Alamat website tidak tersedia, silahkan hubungi Helpdesk."
                })
        
        # * Check Website availability on HOKI 
        config = request.env['tw.api.configuration'].sudo().search([('api_type_id.value', '=', 'hoki')], limit=1)
        if not config:
            return http.request.render('website_self_register.self_register_non_active', {
                'message': "Konfigurasi API HOKI belum ditemukan."
            })
            
        url = config.base_url + "/api/hoki/v1/get_check_avaibility_website"
        headers = {
            'access_token': config.token,
            'Content-Type': 'application/json'
        }
        vals = json.dumps({
            'branch_code': branch_code
        })
        try:
            response = requests.get(url=url, data=vals, headers=headers, timeout=10)
            status_code = response.status_code
            content = response.content
        except Exception as e:
            _logger.error("HOKI API Error: %s", str(e))
            return http.request.render('website_self_register.self_register_non_active', {
                'message': "Koneksi ke server pusat (HOKI) bermasalah. Silahkan coba lagi nanti."
            })
       
        if status_code == 404:
            return http.request.render('website_self_register.self_register_non_active', {
                'message': "Alamat website tidak tersedia, silahkan hubungi Helpdesk."
                })

        if status_code == 200:
            data = {}
            load_content =json.loads(content)
            content = load_content['result'] if 'result' in load_content else load_content
            error = content.get('error', False)
            if error:
                error = str(error)
                if 'Odoo Server Error' in error:
                    error = 'Terdapat error pada Self Register, Silahkan hubungi SA / Helpdesk pada Counter Ahaas'
            branch_name = content.get('branch_name',False)
            active = content.get('active',False)
            paket_service = content.get('paket_service',False)

            if error:
                return http.request.render('website_self_register.self_register_non_active', {
                'message': error
                })    
            
            if not branch_name:
                return http.request.render('website_self_register.self_register_non_active', {
                'message': "Alamat website tidak tersedia, silahkan hubungi Helpdesk."
                })

            if not active:
                message = "Cabang %s tidak memiliki Self Register, silahkan hubungi Counter SA pada Ahaas yang anda kunjungi." %(branch_name)
                return http.request.render('website_self_register.self_register_non_active', {
                'message': message
                })    
            
            if 'user_self_register' in request.session:
                del request.session['user_self_register']
            
            request.session['user_self_register'] = {
                'branch_code': branch_code,
            }

            return http.request.render('website_self_register.self_register_home', {
                'branch_code': branch_code,
                'paket_service': paket_service,
                'privacy_policy_content': False,
                'privacy_policy_id': False,
            })

    @http.route('/post-search-by-no-plat', methods=['POST'],type='json', auth='public', website=True, csrf=False)
    def post_search_by_no_plat(self, **post):
        post = request.httprequest.json
        data = {}
        data['message_error'] = False

        warning_message = ''
        plat_kendaraan = post.get('plat_kendaraan','-')
        
        # Get branch_code safely from referrer OR session
        branch_code = False
        referer = request.httprequest.headers.get('Referer')
        if referer:
            path = urllib.parse.urlparse(referer).path
            path_parts = path.strip('/').split('/')
            if len(path_parts) >= 2 and path_parts[0] == 'self-register':
                branch_code = path_parts[1]
                
        user_self_register = request.session.get('user_self_register')
        if user_self_register:
            branch_code =  user_self_register.get('branch_code', branch_code)

        if not branch_code:
             return 400, {'error': 'Branch code not found'}

        # * Check Booking Service on HOKI 
        config = request.env['tw.api.configuration'].sudo().search([('api_type_id.value','=','hoki')],limit=1)
        if not config:
            return 404, {'error': 'API Configuration Missing'}
            
        url = config.base_url + "/api/hoki/v1/get_booking_service" 
        headers = {
            'access_token': config.token,
            'Content-Type': 'application/json'
        }
        vals = json.dumps({
            'branch_code': branch_code,
            'no_plat': plat_kendaraan
        })
        try:
            response = requests.get(url=url, data=vals, headers=headers, timeout=10)
            status_code = response.status_code
            content = response.content
        except Exception as e:
            _logger.error("HOKI API Error (Search): %s", str(e))
            return 500, {'error': 'Koneksi ke server pusat bermasalah.'}
        
        if status_code == 404:
            return http.request.render('website_self_register.self_register_non_active', {
                'message': "Alamat website tidak tersedia, silahkan hubungi Helpdesk."
                })

        if status_code == 200:
            load_content =json.loads(content)
            content = load_content['result'] if 'result' in load_content else load_content
            if content.get('data',False):
                content = content['data']
            error = str(content.get('error', False))
            if 'Odoo Server Error' in error:
                error = 'Terdapat error pada Self Register, Silahkan hubungi SA / Helpdesk pada Counter Ahaas'
            status = content.get('status',False)
            km = content.get('km',0)
            keluhan = content.get('keluhan',False)
            chassis_no = content.get('chassis_no',False)
            engine_no = content.get('engine_no',False)
            status = content.get('status',False)
            no_booking_service = content.get('no_booking_service',False)
            branch_name = content.get('branch_name',False)
            paket_service = content.get('paket_service',False)
            name_customer = content.get('name_customer',False)
            product = content.get('product',False)
            no_self_register = content.get('no_self_register',False)
            self_register_status = content.get('self_register_status','not_registered')

            # * Fetch Privacy Policy from HOKI
            # Login param dikirim sebagai "Nama Customer - Nomor Mesin"
            # agar HOKI API bisa menemukan privacy policy (external/customer)
            privacy_policy_content = False
            privacy_policy_id = False
            try:
                pp_url = config.base_url + "/api/v1/privacy_policy"
                login_param = '%s - %s' % (
                    name_customer or 'Customer',
                    engine_no or '-'
                )
                pp_vals = json.dumps({
                    'policy_type': 'external',
                    'type': 'self_register',
                    'login': login_param,
                })
                pp_response = requests.post(
                    url=pp_url, data=pp_vals,
                    headers=headers, timeout=10
                )

                if pp_response.status_code == 200:
                    pp_data = pp_response.json()
                    # Handle multiple response formats:
                    # JSON-RPC: {result: {data}} | HOKI raw: {status, data: {}}
                    if 'result' in pp_data:
                        pp_result = pp_data['result']
                    elif 'data' in pp_data:
                        pp_result = pp_data['data']
                    else:
                        pp_result = pp_data
                    if pp_result:
                        privacy_policy_content = pp_result.get(
                            'privacy_policy_content', False
                        )
                        privacy_policy_id = pp_result.get(
                            'privacy_policy_id', False
                        )
            except Exception as e:
                _logger.warning(
                    "Failed to fetch Privacy Policy from HOKI: %s", str(e)
                )

            data = {
                'branch_code': branch_code,
                'branch_name': branch_name,
                'keluhan': keluhan,
                'chassis_no': chassis_no,
                'engine_no': engine_no,
                'km': km,
                'paket_service': paket_service,
                'status': status,
                'no_booking_service': no_booking_service,
                'name_customer': name_customer if name_customer else 'Silahkan isi nama anda',
                'error': str(error),
                'product': product,
                'no_self_register': no_self_register if no_self_register else 'False',
                'self_register_status': self_register_status,
                'message': 'False',
                'privacy_policy_content': privacy_policy_content,
                'privacy_policy_id': privacy_policy_id,
            }
              
            return 200, data
                

        else:
            data['message_error'] = 'Terjadi Error silahkan hubungi Helpdesk / Laporkan pada SA Counter Ahaas'
            return request.make_response(
                json.dumps(data),
                headers=[('Content-Type', 'application/json')]
            )
        
    @http.route('/post-self-register', methods=['POST'],type='json', auth='public', website=True, csrf=False)
    def post_self_register(self, **post):
        post = request.httprequest.json
        data = {}
        data['message_error'] = False
        warning_message = ''
        plat_kendaraan = post.get('plat_kendaraan','-')
        
        # Get branch_code safely
        branch_code = False
        referer = request.httprequest.headers.get('Referer')
        if referer:
            path = urllib.parse.urlparse(referer).path
            path_parts = path.strip('/').split('/')
            if len(path_parts) >= 2 and path_parts[0] == 'self-register':
                branch_code = path_parts[1]
                
        user_self_register = request.session.get('user_self_register')
        if user_self_register:
            branch_code =  user_self_register.get('branch_code', branch_code)

        if not branch_code:
            return 400, {'error': 'Branch code not found'}

        keluhan = post.get('keluhan',False)
        nomor_mesin = post.get('nomor_mesin',False)
        nomor_rangka = post.get('nomor_rangka',False)
        status = post.get('status',False)
        no_booking_service = post.get('no_booking_service',False)
        paket_service = post.get('paket_service',False)
        name_customer = post.get('name_customer',False)
        service_type = post.get('service_type',False)
        no_telp = post.get('no_telp',False)
        km = post.get('km',False)
        privacy_policy_id = post.get('privacy_policy_id', False)

        # * Check Booking Service on HOKI 
        config = request.env['tw.api.configuration'].sudo().search([('api_type_id.value','=','hoki')],limit=1)        
        if not config:
            return 404, {'error': 'API Configuration Missing'}

        url = config.base_url + "/api/hoki/v1/post_self_register"
        headers = {
            'access_token': config.token,
            'Content-Type': 'application/json'
        }
        keluhan = False if keluhan in ('false','-') else keluhan
        no_booking_service = False if no_booking_service in ('false','-') else no_booking_service
        paket_service = False if paket_service in ('#','false','-') else paket_service
        vals = {
            'keluhan': keluhan,
            'chassis_no': nomor_rangka,
            'engine_no': nomor_mesin,
            'status': status,
            'no_booking_service': no_booking_service,
            'paket_service': paket_service,
            'name_customer': name_customer,
            'branch_code': branch_code,
            'service_type': service_type,
            'no_telp': no_telp,
            'km': km
        }

        # * Get Priority
        if no_booking_service and paket_service and not keluhan:
            vals['priority'] = '1'
        elif no_booking_service and keluhan and paket_service:
            vals['priority'] = '2'
        elif not no_booking_service and not keluhan and paket_service:
            vals['priority'] = '3'
        else:
            vals['priority'] = '4'


        try:
            response = requests.post(url=url, data=json.dumps(vals), headers=headers, timeout=10)   
            status_code = response.status_code
            content = response.content
        except Exception as e:
            _logger.error("HOKI API Error (Post): %s", str(e))
            return 500, {'error': 'Koneksi ke server pusat bermasalah.'}

        if status_code == 404:
            return http.request.render('website_self_register.self_register_non_active', {
                'message': "Alamat website tidak tersedia, silahkan hubungi Helpdesk."
                })

        if status_code == 200:
            load_content =json.loads(content)
            content = load_content['result'] if 'result' in load_content else load_content
            error = content.get('error', False)
            if content and not 'error' in content:
                no_self_register = content.get('no_self_register',False) or content.get('data')['no_self_register']

                # * Accept Privacy Policy on HOKI
                if privacy_policy_id:
                    login = nomor_mesin + '-' + name_customer
                    try:
                        pp_url = config.base_url + "/api/v1/accept_privacy_policy"
                        pp_vals = json.dumps({
                            'privacy_policy_id': privacy_policy_id,
                            'login': login,
                            'type': 'self_register',
                        })
                        requests.post(url=pp_url, data=pp_vals, headers=headers, timeout=10)
                    except Exception as e:
                        _logger.warning("Failed to accept Privacy Policy on HOKI: %s", str(e))

                data = {
                    'message': "Terima kasih sudah melakukan Self Register. Silahkan simpan Nomor Register berikut ini.",
                    'error': str(error),
                    'no_self_register': str(no_self_register),
                    'name_customer': name_customer,
                    'no_telp': no_telp
                }
            else:
                data = {
                    'error': 'Terdapat error saat self register %s' %(str(load_content))
                }
              
            return 200, data