# 1: imports of python lib
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
import json
try:
    import simplejson as json
except ImportError:
    import json
import logging
_logger = logging.getLogger(__name__)

# 2: import of known third party lib
from odoo.addons.tw_api.controllers.main import invalid_response, valid_response
from odoo.addons.rest_api.controllers.main import check_valid_token

# 3:  imports of odoo
from odoo import http

# 4:  imports from odoo modules
from odoo.http import request

# 5: local imports

# 6: Import of unknown third party lib


class ControllerREST(http.Controller):
    @http.route('/api/absensi/v1/get_absensi', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_absensi(self, **post):
        uid = request.session.uid
        company_ids = request.env.user.company_ids
        employee = request.env['hr.employee'].sudo().search([
            ('user_id','=',uid)
        ], limit=1)
        tanggal = request.env['tw.attendance'].sudo()._get_default_date()
        query_where = " WHERE employee.id = %d and absen.date='%s'" % (employee.id,tanggal)

        query = f"""
             SELECT 
                employee.id employee_id
                ,absen.id
                ,COALESCE(to_char(absen.date, 'YYYY-MM-DD'),'') date_absen
                ,COALESCE(to_char(absen.check_in + INTERVAL '7 hours', 'HH24:MI:SS'),'') as "jam_masuk"
                ,COALESCE(to_char(absen.check_out + INTERVAL '7 hours', 'HH24:MI:SS'),'') as "jam_keluar"
   
                from  hr_employee as employee
                LEFT JOIN tw_attendance as absen on employee.id=absen.employee_id
                %s
        """ %(query_where)
        request._cr.execute(query)
        ress = request._cr.dictfetchone()
        if ress :
            data=ress
        else :
            data = {
            'employee_id': employee.id,
            'id': None,
            'date_absen': None,
            'jam_masuk':None ,
            'jam_keluar':None,
            }
        return valid_response(200, data)
    
    @http.route('/api/absensi/v1/get_absensi_history', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_absensi_history(self, **post):
        uid = request.session.uid
        employee = request.env['hr.employee'].sudo().search([
            ('user_id', '=', uid)
        ], limit=1)

        if not employee:
            info = "Employee not found"
            error = 'employee_not_found'
            _logger.error(info)
            return invalid_response(400, error, info)

        # Validate mandatory parameters
        start_date = post.get('start_date')
        end_date = post.get('end_date')

        if not start_date or not end_date:
            info = "Parameter start_date dan end_date wajib diisi"
            error = "missing_parameters"
            _logger.error(info)
            return invalid_response(400, error, info)

        # Validate date format
        try:
            dt.strptime(start_date, '%Y-%m-%d')
            dt.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            info = "Format tanggal harus YYYY-MM-DD"
            error = "format_tanggal_tidak_sesuai"
            _logger.error(info)
            return invalid_response(400, error, info)

        query = """
            SELECT
                absen.id,
                employee.id AS employee_id,
                employee.name AS employee_name,
                COALESCE(to_char(absen.date, 'YYYY-MM-DD'), '') AS date_absen,
                COALESCE(to_char(absen.check_in + INTERVAL '7 hours', 'YYYY-MM-DD HH24:MI:SS'), '') AS jam_masuk,
                COALESCE(to_char(absen.check_out + INTERVAL '7 hours', 'YYYY-MM-DD HH24:MI:SS'), '') AS jam_keluar,
                COALESCE(wp_in.name::text, '') AS workplace_in,
                COALESCE(wp_out.name::text, '') AS workplace_out
            FROM tw_attendance AS absen
            JOIN hr_employee AS employee ON employee.id = absen.employee_id
            LEFT JOIN res_company AS wp_in ON wp_in.id = absen.workplace_in_id
            LEFT JOIN res_company AS wp_out ON wp_out.id = absen.workplace_out_id
            WHERE employee.id = %s
                AND absen.date >= %s
                AND absen.date <= %s
            ORDER BY absen.date ASC, absen.check_in ASC
        """
        request._cr.execute(query, (employee.id, start_date, end_date))
        results = request._cr.dictfetchall()

        data = {
            'employee_id': employee.id,
            'employee_name': employee.name,
            'start_date': start_date,
            'end_date': end_date,
            'total_records': len(results),
            'records': results,
        }
        return valid_response(200, data)

    @http.route('/api/absensi/v1/post_absen_masuk', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_absen_masuk(self, **post):
        id_work_place = False
        method = request.httprequest.method
        uid = request.session.uid
        today = request.env['tw.attendance'].sudo()._get_default_date()
        employee = request.env['hr.employee'].sudo().search([
            ('user_id','=',uid)
        ], limit=1)
        attendance_object = request.env['tw.attendance']

        # Check mandatory fields
        mandatory_field = [
            'lat',
            'long',
            'check_in'
        ]

        fields = []
        for mandatory in mandatory_field:
            if mandatory not in post:
                fields.append(mandatory)
        if len(fields) > 0:
            info = "Mandatory request in body %s!" %(fields)
            error = "Missing mandatory fields"
            _logger.error(info)
            return invalid_response(400, error, info)
        
        # Check in date format
        try:
            check_in_7 = dt.strptime(post['check_in'], '%Y-%m-%d %H:%M:%S')
            check_in = check_in_7 - relativedelta(hours = 7)
        except:
            info = "Format Tanggal Tidak Sesuai"
            error = 'format_tanggal_tidak_sesuai'
            _logger.error(info)
            return invalid_response(400, error, info)
        
        # Check if employee already check in
        existed_attendance = attendance_object.sudo().search([
            ('employee_id','=',employee.id),
            ('date','=',today),
            ('check_in','!=',False)
        ], limit=1)
        if existed_attendance:
            info = "Anda sudah absen hari ini"
            error = 'sudah_absen'
            _logger.error(info)
            return invalid_response(400, error, info)
        
        # Get Work Place of the loged user
        work_place = attendance_object.work_place(employee.id,float(post['lat']),float(post['long']))
        if not work_place:
            info = "Anda tidak berada di area kerja"
            error = 'tidak_di_area_kerja'
            _logger.error(info)
            return invalid_response(400, error, info)
        
        vals = {}
        vals['employee_id'] = employee.id
        vals['date'] = today
        vals['check_in'] = check_in
        vals['workplace_in_id'] = work_place['id']
        vals['lat_in'] = post['lat']
        vals['long_in'] = post['long']
        vals['radius_in'] = work_place['radius']
        attendance = attendance_object.sudo().create(vals)


        date_absen = ''
        jam_masuk = ''
        jam_keluar = ''
        if attendance :
            if attendance.date :
                date_absen = attendance.date.strftime('%Y-%m-%d')
            if attendance.check_in :
                jam_masuk_jakarta = attendance.check_in + relativedelta(hours = 7)
                jam_masuk = jam_masuk_jakarta.strftime('%H:%M:%S')
            if attendance.check_out :
                jam_keluar_jakarta = attendance.check_out + relativedelta(hours = 7)
                jam_keluar = jam_keluar_jakarta.strftime('%H:%M:%S')
        
        data = {
            'employee_id':employee.id,
            'id':attendance.id,
            'date_absen':date_absen,
            'jam_masuk':jam_masuk,
            'jam_keluar':jam_keluar,
        }
        return valid_response(200, data)

    @http.route('/api/absensi/v1/post_absen_keluar', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_absen_keluar(self,**post):
        id_work_place=False
        method = request.httprequest.method
        uid = request.session.uid
        today = request.env['tw.attendance'].sudo()._get_default_date()
        employee = request.env['hr.employee'].sudo().search([
            ('user_id','=',uid)
        ], limit=1)
        attendance_object = request.env['tw.attendance']

        # Check mandatory fields
        mandatory_field = [
            'lat',
            'long',
            'check_out'
        ]

        fields = []
        for mandatory in mandatory_field:
            if mandatory not in post:
                fields.append(mandatory)
        if len(fields) > 0:
            info = "Mandatory request in body %s!" %(fields)
            error = "Missing mandatory fields"
            _logger.error(info)
            return invalid_response(400, error, info)
        
        # Check in date format
        try:
            check_out_7 = dt.strptime(post['check_out'], '%Y-%m-%d %H:%M:%S')
            check_out = check_out_7 - relativedelta(hours = 7)
        except:
            info = "Format Tanggal Tidak Sesuai"
            error = 'format_tanggal_tidak_sesuai'
            _logger.error(info)
            return invalid_response(400, error, info)
        
        # Check if employee already check in
        existed_attendance = attendance_object.sudo().search([
            ('employee_id','=',employee.id),
            ('date','=',today),
            ('check_in','!=',False),
        ], limit=1)
        if not existed_attendance:
            info = "Not checked in yet"
            error = 'not_checked_in_yet'
            _logger.error(info)
            return invalid_response(400, error, info)
        
        # Get Work Place of the loged user
        work_place = attendance_object.work_place(employee.id,float(post['lat']),float(post['long']))
        if not work_place:
            info = "Anda tidak berada di area kerja"
            error = 'tidak_di_area_kerja'
            _logger.error(info)
            return invalid_response(400, error, info)
        
        vals = {}
        try:
            check_out_7 = dt.strptime(post['check_out'], '%Y-%m-%d %H:%M:%S')
            vals['check_out'] = check_out_7 - relativedelta(hours = 7)
        except:
            info = "Format Tanggal Tidak Sesuai"
            error = 'format_tanggal_tidak_sesuai'
            _logger.error(info)
            return invalid_response(400, error, info)
        
        vals['employee_id'] = employee.id
        vals['date'] = today
        check_out_datetime = check_out_7 + relativedelta(hours = 7)
        get_hours = existed_attendance.get_work_hours(check_out_datetime)
        vals['work_hours'] = get_hours['work_hours']
        vals['work_mins'] = get_hours['work_mins']
        vals['work_secs'] = get_hours['work_secs']
        work_place = attendance_object.work_place(employee.id,float(post['lat']),float(post['long']))
        if not work_place :
            info = "Anda tidak berada di area kerja"
            error = 'tidak_di_area_kerja'
            _logger.error(info)
            return invalid_response(400, error, info)
        vals['workplace_out_id'] = work_place['id']
        vals['lat_out'] = post['lat']
        vals['long_out'] = post['long']
        vals['radius_out'] = work_place['radius']
        existed_attendance.sudo().write(vals)

        date_absen = ''
        jam_masuk = ''
        jam_keluar = ''
        if existed_attendance:
            if existed_attendance.date:
                date_absen = existed_attendance.date.strftime('%Y-%m-%d')
            if existed_attendance.check_in:
                jam_masuk_jakarta = existed_attendance.check_in + relativedelta(hours = 7)
                jam_masuk = jam_masuk_jakarta.strftime('%H:%M:%S')
            if existed_attendance.check_out:
                jam_keluar_jakarta = existed_attendance.check_out + relativedelta(hours = 7)
                jam_keluar = jam_keluar_jakarta.strftime('%H:%M:%S')
        
        data = {
            'employee_id':employee.id,
            'id':existed_attendance.id,
            'date_absen':date_absen,
            'jam_masuk':jam_masuk,
            'jam_keluar':jam_keluar,
        }
        return valid_response(200, data)

    @http.route('/api/absensi/v1/post_request_attendance', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_request_attendance(self, **post):
        uid = request.session.uid
        employee = request.env['hr.employee'].sudo().search([
            ('user_id', '=', uid)
        ], limit=1)

        if not employee:
            info = "Employee not found"
            error = 'employee_not_found'
            _logger.error(info)
            return invalid_response(400, error, info)

        # Accept array of records
        records = post.get('records', [])
        if not records or not isinstance(records, list):
            info = "Body harus berisi 'records' berupa array"
            error = 'invalid_body'
            _logger.error(info)
            return invalid_response(400, error, info)

        mandatory_fields = ['date', 'check_in', 'check_out']
        success_list = []
        error_list = []

        for idx, rec in enumerate(records):
            row_num = idx + 1

            # Check mandatory fields
            missing = [f for f in mandatory_fields if f not in rec]
            if missing:
                error_list.append({
                    'row': row_num,
                    'date': rec.get('date', ''),
                    'error': 'missing_mandatory_fields',
                    'info': "Field wajib belum diisi: %s" % missing,
                })
                continue

            # Validate date format
            try:
                req_date = dt.strptime(rec['date'], '%Y-%m-%d').date()
            except Exception:
                error_list.append({
                    'row': row_num,
                    'date': rec.get('date', ''),
                    'error': 'format_tanggal_tidak_sesuai',
                    'info': "Format 'date' harus YYYY-MM-DD",
                })
                continue

            # Validate check_in datetime format and convert to UTC
            try:
                check_in_local = dt.strptime(rec['check_in'], '%Y-%m-%d %H:%M:%S')
                check_in_utc = check_in_local - relativedelta(hours=7)
            except Exception:
                error_list.append({
                    'row': row_num,
                    'date': rec.get('date', ''),
                    'error': 'format_tanggal_tidak_sesuai',
                    'info': "Format 'check_in' harus YYYY-MM-DD HH:MM:SS",
                })
                continue

            # Validate check_out datetime format and convert to UTC
            try:
                check_out_local = dt.strptime(rec['check_out'], '%Y-%m-%d %H:%M:%S')
                check_out_utc = check_out_local - relativedelta(hours=7)
            except Exception:
                error_list.append({
                    'row': row_num,
                    'date': rec.get('date', ''),
                    'error': 'format_tanggal_tidak_sesuai',
                    'info': "Format 'check_out' harus YYYY-MM-DD HH:MM:SS",
                })
                continue

            # Check if request already exists for the same date
            existing_line = request.env['tw.attendance.request.line'].sudo().search([
                ('request_id.employee_id', '=', employee.id),
                ('date', '=', req_date),
                ('request_id.state', 'not in', ['rejected']),
            ], limit=1)
            if existing_line:
                error_list.append({
                    'row': row_num,
                    'date': rec['date'],
                    'error': 'request_already_exists',
                    'info': "Request Attendance untuk tanggal %s sudah ada" % rec['date'],
                })
                continue

            # Get work_place_id: from request body, or fallback to employee's company
            work_place_id = False
            if rec.get('work_place_id'):
                try:
                    work_place_id = int(rec['work_place_id'])
                    wp = request.env['res.company'].sudo().browse(work_place_id)
                    if not wp.exists():
                        work_place_id = False
                except (ValueError, TypeError):
                    work_place_id = False

            if not work_place_id and employee.company_id:
                work_place_id = employee.company_id.id

            # Prepare line for the Attendance Request
            line_vals = {
                'date': req_date,
                'start_date': check_in_utc,
                'end_date': check_out_utc,
            }
            if rec.get('reason'):
                line_vals['reason'] = rec['reason']
            if work_place_id:
                line_vals['work_place_id'] = work_place_id
                
            success_list.append({
                'row': row_num,
                'line_vals': line_vals,
                'work_place_name': wp.name if work_place_id and 'wp' in locals() and wp.exists() else '',
                'work_place_id': work_place_id,
            })

        if error_list:
            error_messages = '; '.join([e['info'] for e in error_list])
            return invalid_response(422, 'request_attendance_failed', error_messages)

        final_success_list = []
        if success_list:
            master_vals = {
                'employee_id': employee.id,
                'state': 'draft',
                'request_line_ids': [(0, 0, s['line_vals']) for s in success_list]
            }
            try:
                att_req = request.env['tw.attendance.request'].sudo().create(master_vals)
            except Exception as e:
                return invalid_response(422, 'create_failed', "Gagal membuat Request Attendance: %s" % str(e))
                
            for s in success_list:
                line = s['line_vals']
                start_local = line['start_date'] + relativedelta(hours=7)
                end_local = line['end_date'] + relativedelta(hours=7)
                
                final_success_list.append({
                    'id': att_req.id,
                    'name': att_req.name,
                    'employee_id': employee.id,
                    'date': line['date'].strftime('%Y-%m-%d'),
                    'start_date': start_local.strftime('%Y-%m-%d %H:%M:%S'),
                    'end_date': end_local.strftime('%Y-%m-%d %H:%M:%S'),
                    'state': att_req.state,
                    'reason': line.get('reason', ''),
                    'work_place_id': s['work_place_id'] or False,
                    'work_place_name': s['work_place_name'],
                })

        data = {
            'employee_id': employee.id,
            'employee_name': employee.name,
            'total_submitted': len(records),
            'total_success': len(final_success_list),
            'total_failed': len(error_list),
            'success': final_success_list,
            'errors': error_list,
        }

        return valid_response(200, data)

    @http.route('/api/absensi/v1/get_request_attendance', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_request_attendance(self, **post):
        uid = request.session.uid
        employee = request.env['hr.employee'].sudo().search([
            ('user_id', '=', uid)
        ], limit=1)

        if not employee:
            info = "Employee not found"
            error = 'employee_not_found'
            _logger.error(info)
            return invalid_response(400, error, info)

        domain = [('employee_id', '=', employee.id)]

        start_date = post.get('start_date')
        end_date = post.get('end_date')
        state = post.get('state')

        if start_date:
            domain.append(('date', '>=', start_date))
        if end_date:
            domain.append(('date', '<=', end_date))
        if state:
            domain.append(('state', '=', state))

        requests_records = request.env['tw.attendance.request'].sudo().search(domain, order='date desc, id desc')
        
        results = []
        for req in requests_records:
            lines = []
            for line in req.request_line_ids:
                start_local = line.start_date + relativedelta(hours=7) if line.start_date else False
                end_local = line.end_date + relativedelta(hours=7) if line.end_date else False
                lines.append({
                    'id': line.id,
                    'date': line.date.strftime('%Y-%m-%d') if line.date else '',
                    'start_date': start_local.strftime('%Y-%m-%d %H:%M:%S') if start_local else '',
                    'end_date': end_local.strftime('%Y-%m-%d %H:%M:%S') if end_local else '',
                    'reason': line.reason or '',
                    'work_place_id': line.work_place_id.id or False,
                    'work_place_name': line.work_place_id.name or '',
                })
            
            results.append({
                'id': req.id,
                'name': req.name,
                'date': req.date.strftime('%Y-%m-%d') if req.date else '',
                'state': req.state,
                'reject_reason': req.reject_reason or '',
                'lines': lines
            })

        data = {
            'employee_id': employee.id,
            'employee_name': employee.name,
            'total_records': len(results),
            'records': results,
        }
        return valid_response(200, data)