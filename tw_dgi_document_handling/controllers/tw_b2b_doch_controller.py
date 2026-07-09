# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging

try:
    import simplejson as json
except ImportError:
    import json

from datetime import datetime

# 2: imports of odoo
from odoo import http
from odoo.http import request

# 3: imports from odoo modules
from odoo.addons.tw_dgi.controllers.main import check_valid_dgi

_logger = logging.getLogger(__name__)


class ControllerREST(http.Controller):
    # --- Helper Methods ---
    def _get_json_data(self):
        try:
            data = json.loads(request.httprequest.get_data(as_text=True))
            # Handle both JSON-RPC (params) and flat JSON
            return data.get('params', data)
        except Exception:
            return {}

    def _make_json_response(self, data):
        return request.make_response(
            json.dumps({'result': data}),
            headers={'Content-Type': 'application/json'}
        )

    def _lookup_branch(self, dealer_code):
        if not dealer_code:
            return None, "Field 'idDealer' is required!"
        company_obj = request.env['res.company'].sudo().search(
            [('code', '=', dealer_code)], limit=1
        )
        if not company_obj:
            return None, f"Dealer with code '{dealer_code}' not found!"
        return company_obj, None

    def _lookup_lot(self, engine_no, company_obj):
        if not engine_no:
            return None, "Field 'noMesin' is required in unit!"
        lot_obj = request.env['stock.lot'].sudo().search([
            ('name', '=', engine_no),
            ('company_id', '=', company_obj.id),
        ], limit=1)
        if not lot_obj:
            return None, f"Engine number '{engine_no}' not found for dealer '{company_obj.atpm_code}'!"
        return lot_obj, None

    def _lookup_biro_jasa(self, biro_jasa_code):
        if not biro_jasa_code:
            return None, "Field 'kodeBirojasa' is required!"
        biro_jasa_obj = request.env['res.partner'].sudo().search([
            ('code', '=', biro_jasa_code),
            ('category_id.name', '=', 'Birojasa'),
        ], limit=1)
        if not biro_jasa_obj:
            return None, f"Biro Jasa with code '{biro_jasa_code}' not found!"
        return biro_jasa_obj, None

    # --- Penerimaan STNK ---
    @http.route('/api/b2b/dgi-api/<version>/penerimaan-stnk/add', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_dgi
    def process_data_penerimaan_stnk(self, version, **post):
        try:
            if not post:
                data = self._get_json_data()
            else:
                data = post

            # Validate mandatory fields
            for field in ['idDealer', 'kodeBirojasa', 'noPST', 'unit']:
                if field not in data:
                    return self._make_json_response({'status': 0, 'message': f"Mandatory field '{field}' is missing!"})

            # Check duplicate by MD reference (noPST)
            md_reference_number = data.get('noPST')
            if md_reference_number:
                existing_ref = request.env['tw.vehicle.registration.receipt'].sudo().search([
                    ('md_reference_number', '=', md_reference_number)
                ], limit=1)
                if existing_ref:
                    return self._make_json_response({'status': 1, 'message': f"Penerimaan STNK dengan nomor MD {md_reference_number} sudah ada: {existing_ref.name}", 'data': {'id': existing_ref.id, 'name': existing_ref.name}})

            # Lookup branch
            company_obj, error_msg = self._lookup_branch(data.get('idDealer'))
            if error_msg:
                return self._make_json_response({'status': 0, 'message': error_msg})

            # Lookup biro jasa
            biro_jasa_obj, error_msg = self._lookup_biro_jasa(data.get('kodeBirojasa'))
            if error_msg:
                return self._make_json_response({'status': 0, 'message': error_msg})

            # Process units
            units = data.get('unit', [])
            if not units:
                return self._make_json_response({'status': 0, 'message': "Unit list is empty!"})

            line_vals_list = []
            for unit in units:
                lot_obj, error_msg = self._lookup_lot(unit.get('nomorMesin'), company_obj)
                if error_msg:
                    return self._make_json_response({'status': 0, 'message': error_msg})

                line_val = {
                    'lot_id': lot_obj.id,
                    'vehicle_registration_number': unit.get('nomorSTNK', ''),
                    'stnk_date': unit.get('tglJTPSTNK') or False,
                    'plate_number': unit.get('nomorPolisi', ''),
                    'notice_number': unit.get('nomorNotice', ''),
                    'notice_date': unit.get('tglJTPNotice') or False,
                    'is_receive_plate': bool(unit.get('nomorPolisi')),
                }
                line_vals_list.append(line_val)

            # Check duplicate by lot
            existing = request.env['tw.vehicle.registration.receipt'].sudo().search([
                ('company_id', '=', company_obj.id),
                ('biro_jasa_id', '=', biro_jasa_obj.id),
                ('state', '!=', 'cancel'),
                ('vehicle_registration_receipt_line_ids.lot_id', 'in',
                 [line_val['lot_id'] for line_val in line_vals_list]),
            ], limit=1)
            if existing:
                return self._make_json_response({'status': 0, 'message': f"Penerimaan STNK already exists: {existing.name}"})

            # Create record
            header_vals = {
                'company_id': company_obj.id,
                'biro_jasa_id': biro_jasa_obj.id,
                'division': 'Unit',
                'is_dgi': True,
                'vehicle_registration_receipt_line_ids': [(0, 0, line_val) for line_val in line_vals_list],
            }
            if md_reference_number:
                header_vals['md_reference_number'] = md_reference_number

            created = request.env['tw.vehicle.registration.receipt'].sudo().create(header_vals)

            return self._make_json_response({'status': 1, 'message': f"Penerimaan STNK '{created.name}' created successfully.", 'data': {'id': created.id, 'name': created.name}})

        except Exception as error:
            _logger.exception("Error in process_data_penerimaan_stnk")
            return self._make_json_response({'status': 0, 'message': f"Exception: {str(error)}"})

    # --- Penerimaan BPKB ---
    @http.route('/api/b2b/dgi-api/<version>/penerimaan-bpkb/add', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_dgi
    def process_data_penerimaan_bpkb(self, version, **post):
        try:
            if not post:
                data = self._get_json_data()
            else:
                data = post

            # Validate mandatory fields
            for field in ['idDealer', 'kodeBirojasa', 'noPSB', 'unit']:
                if field not in data:
                    return self._make_json_response({'status': 0, 'message': f"Mandatory field '{field}' is missing!"})

            # Check duplicate by MD reference (noPSB)
            md_reference_number = data.get('noPSB')
            if md_reference_number:
                existing_ref = request.env['tw.vehicle.ownership.receipt'].sudo().search([
                    ('md_reference_number', '=', md_reference_number)
                ], limit=1)
                if existing_ref:
                    return self._make_json_response({'status': 1, 'message': f"Penerimaan BPKB dengan nomor MD {md_reference_number} sudah ada: {existing_ref.name}", 'data': {'id': existing_ref.id, 'name': existing_ref.name}})

            # Lookup branch
            company_obj, error_msg = self._lookup_branch(data.get('idDealer'))
            if error_msg:
                return self._make_json_response({'status': 0, 'message': error_msg})

            # Lookup biro jasa
            biro_jasa_obj, error_msg = self._lookup_biro_jasa(data.get('kodeBirojasa'))
            if error_msg:
                return self._make_json_response({'status': 0, 'message': error_msg})

            # Process units
            units = data.get('unit', [])
            if not units:
                return self._make_json_response({'status': 0, 'message': "Unit list is empty!"})

            line_vals_list = []
            for unit in units:
                lot_obj, error_msg = self._lookup_lot(unit.get('nomorMesin'), company_obj)
                if error_msg:
                    return self._make_json_response({'status': 0, 'message': error_msg})

                line_val = {
                    'lot_id': lot_obj.id,
                    'vehicle_ownership_number': unit.get('nomorBPKB', ''),
                    'vehicle_ownership_date': unit.get('tglBPKB') or False,
                }
                line_vals_list.append(line_val)

            # Check duplicate by lot
            existing = request.env['tw.vehicle.ownership.receipt'].sudo().search([
                ('company_id', '=', company_obj.id),
                ('biro_jasa_id', '=', biro_jasa_obj.id),
                ('state', '!=', 'cancel'),
                ('vehicle_ownership_receipt_line_ids.lot_id', 'in',
                 [line_val['lot_id'] for line_val in line_vals_list]),
            ], limit=1)
            if existing:
                return self._make_json_response({'status': 0, 'message': f"Penerimaan BPKB already exists: {existing.name}"})

            # Create record
            header_vals = {
                'company_id': company_obj.id,
                'biro_jasa_id': biro_jasa_obj.id,
                'division': 'Unit',
                'is_dgi': True,
                'vehicle_ownership_receipt_line_ids': [(0, 0, line_val) for line_val in line_vals_list],
            }
            if md_reference_number:
                header_vals['md_reference_number'] = md_reference_number

            created = request.env['tw.vehicle.ownership.receipt'].sudo().create(header_vals)

            return self._make_json_response({'status': 1, 'message': f"Penerimaan BPKB '{created.name}' created successfully.", 'data': {'id': created.id, 'name': created.name}})

        except Exception as error:
            _logger.exception("Error in process_data_penerimaan_bpkb")
            return self._make_json_response({'status': 0, 'message': f"Exception: {str(error)}"})

    # --- Penyerahan STNK ---
    @http.route('/api/b2b/dgi-api/<version>/penyerahan-stnk/add', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_dgi
    def process_data_penyerahan_stnk(self, version, **post):
        try:
            if not post:
                data = self._get_json_data()
            else:
                data = post

            # Validate mandatory fields
            for field in ['idDealer', 'noENCS', 'unit']:
                if field not in data:
                    return self._make_json_response({'status': 0, 'message': f"Mandatory field '{field}' is missing!"})

            # Check duplicate by MD reference (noENCS)
            md_reference_number = data.get('noENCS')
            if md_reference_number:
                existing_ref = request.env['tw.vehicle.registration.handover'].sudo().search([
                    ('md_reference_number', '=', md_reference_number)
                ], limit=1)
                if existing_ref:
                    return self._make_json_response({'status': 1, 'message': f"Penyerahan STNK dengan nomor MD {md_reference_number} sudah ada: {existing_ref.name}", 'data': {'id': existing_ref.id, 'name': existing_ref.name}})

            # Lookup branch
            company_obj, error_msg = self._lookup_branch(data.get('idDealer'))
            if error_msg:
                return self._make_json_response({'status': 0, 'message': error_msg})

            # Process units
            units = data.get('unit', [])
            if not units:
                return self._make_json_response({'status': 0, 'message': "Unit list is empty!"})

            line_vals_list = []
            customer_obj = None
            for unit in units:
                lot_obj, error_msg = self._lookup_lot(unit.get('nomorMesin'), company_obj)
                if error_msg:
                    return self._make_json_response({'status': 0, 'message': error_msg})

                # Validate: at least one date must be provided
                if not unit.get('tglAmbilNotice') and not unit.get('tglAmbilSTNK') and not unit.get('tglAmbilNopol'):
                    return self._make_json_response({'status': 0, 'message': f"Unit '{unit.get('nomorMesin')}' must have at least one of tglAmbilNotice, tglAmbilSTNK, or tglAmbilNopol!"})

                # Use the customer from the first lot for the header partner_id
                if not customer_obj and lot_obj.customer_stnk_id:
                    customer_obj = lot_obj.customer_stnk_id

                line_val = {
                    'lot_id': lot_obj.id,
                    'notice_handover_date': unit.get('tglAmbilNotice') or False,
                    'stnk_handover_date': unit.get('tglAmbilSTNK') or False,
                    'plate_handover_date': unit.get('tglAmbilNopol') or False,
                }
                line_vals_list.append(line_val)

            # Check duplicate by lot
            existing = request.env['tw.vehicle.registration.handover'].sudo().search([
                ('company_id', '=', company_obj.id),
                ('state', '!=', 'cancel'),
                ('registration_handover_line_ids.lot_id', 'in',
                 [line_val['lot_id'] for line_val in line_vals_list]),
            ], limit=1)
            if existing:
                return self._make_json_response({'status': 0, 'message': f"Penyerahan STNK already exists: {existing.name}"})

            # Create record
            header_vals = {
                'company_id': company_obj.id,
                'receiver': customer_obj.name if customer_obj else '',
                'partner_id': customer_obj.id if customer_obj else False,
                'division': 'Unit',
                'is_dgi': True,
                'registration_handover_line_ids': [(0, 0, line_val) for line_val in line_vals_list],
            }
            if md_reference_number:
                header_vals['md_reference_number'] = md_reference_number

            created = request.env['tw.vehicle.registration.handover'].sudo().create(header_vals)

            return self._make_json_response({'status': 1, 'message': f"Penyerahan STNK '{created.name}' created successfully.", 'data': {'id': created.id, 'name': created.name}})

        except Exception as error:
            _logger.exception("Error in process_data_penyerahan_stnk")
            return self._make_json_response({'status': 0, 'message': f"Exception: {str(error)}"})

    # Penyerahan BPKB
    @http.route('/api/b2b/dgi-api/<version>/penyerahan-bpkb/add', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_dgi
    def process_data_penyerahan_bpkb(self, version, **post):
        try:
            if not post:
                data = self._get_json_data()
            else:
                data = post

            # Validate mandatory fields
            for field in ['idDealer', 'idFinco', 'noENCB', 'penerima', 'unit', 'tglAmbilBPKB']:
                if field not in data:
                    return self._make_json_response({'status': 0, 'message': f"Mandatory field '{field}' is missing!"})

            # Check duplicate by MD reference (noENCB)
            md_reference_number = data.get('noENCB')
            if md_reference_number:
                existing_ref = request.env['tw.vehicle.ownership.handover'].sudo().search([
                    ('md_reference_number', '=', md_reference_number)
                ], limit=1)
                if existing_ref:
                    return self._make_json_response({'status': 1, 'message': f"Penyerahan BPKB dengan nomor MD {md_reference_number} sudah ada: {existing_ref.name}", 'data': {'id': existing_ref.id, 'name': existing_ref.name}})

            # Lookup branch
            company_obj, error_msg = self._lookup_branch(data.get('idDealer'))
            if error_msg:
                return self._make_json_response({'status': 0, 'message': error_msg})

            penerima = data.get('penerima', '')
            tgl_ambil_bpkb = data.get('tglAmbilBPKB') or False

            # Lookup finco
            finco_obj = None
            finco_code = data.get('idFinco')
            if finco_code:
                finco_obj = request.env['res.partner'].sudo().search([
                    ('code', '=', finco_code),
                ], limit=1)

            # Process units (list of engine number strings)
            units = data.get('unit', [])
            if not units:
                return self._make_json_response({'status': 0, 'message': "Unit list is empty!"})

            line_vals_list = []
            customer_obj = None
            for engine_no in units:
                lot_obj, error_msg = self._lookup_lot(str(engine_no), company_obj)
                if error_msg:
                    return self._make_json_response({'status': 0, 'message': error_msg})

                # Use the customer from the first lot for fallback partner
                if not customer_obj and lot_obj.customer_stnk_id:
                    customer_obj = lot_obj.customer_stnk_id

                line_val = {
                    'lot_id': lot_obj.id,
                    'ownership_handover_date': tgl_ambil_bpkb,
                }
                line_vals_list.append(line_val)

            # Determine partner type
            if finco_obj:
                partner_type = 'finco'
                partner_id = finco_obj.id
            else:
                partner_type = 'customer'
                partner_id = customer_obj.id if customer_obj else False

            # Check duplicate
            existing = request.env['tw.vehicle.ownership.handover'].sudo().search([
                ('company_id', '=', company_obj.id),
                ('state', '!=', 'cancel'),
                ('ownership_handover_line_ids.lot_id', 'in',
                 [line_val['lot_id'] for line_val in line_vals_list]),
            ], limit=1)
            if existing:
                return self._make_json_response({'status': 0, 'message': f"Penyerahan BPKB already exists: {existing.name}"})

            # Create record
            header_vals = {
                'company_id': company_obj.id,
                'partner_type': partner_type,
                'partner_id': partner_id,
                'receiver': penerima,
                'division': 'Unit',
                'is_dgi': True,
                'ownership_handover_date': tgl_ambil_bpkb,
                'ownership_handover_line_ids': [(0, 0, line_val) for line_val in line_vals_list],
            }

            if md_reference_number:
                header_vals['md_reference_number'] = md_reference_number

            created = request.env['tw.vehicle.ownership.handover'].sudo().create(header_vals)

            return self._make_json_response({'status': 1, 'message': f"Penyerahan BPKB '{created.name}' created successfully.", 'data': {'id': created.id, 'name': created.name}})

        except Exception as error:
            _logger.exception("Error in process_data_penyerahan_bpkb")
            return self._make_json_response({'status': 0, 'message': f"Exception: {str(error)}"})
