# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.tw_api.controllers.main import valid_response, invalid_response, check_sensitive_value
from odoo.addons.rest_api.controllers.main import check_valid_token, validate_payload
from odoo.http import request

try:
    import simplejson as json
except ImportError:
    import json

def _get_pricelist(division, company_id):
    current_pricelist=False
    if division.lower() =='unit':
        current_pricelist = company_id.branch_setting_id.pricelist_sale_unit_id
    elif division.lower() == 'sparepart':  
        current_pricelist = company_id.branch_setting_id.pricelist_sale_sparepart_id
    return current_pricelist

class ControllerREST(http.Controller):
    @http.route('/api/stock_distribution/<version>/create_stock_distribution', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def create_stock_distribution(self, version,**kwargs):
        payload = json.loads(request.httprequest.get_data(as_text=True))

        mandatory_fields = [
            'division','branch_code', 'po_name', 'line_ids', 'type',
            'start_date', 'end_date', 'transaction_id', 'model_name'
            ]
        
        po_type = payload.get('type')

        branch_code = payload.get('branch_code')
        po_name = payload.get('po_name')
        end_date = payload.get('end_date')
        start_date = payload.get('start_date') 
        end_date = payload.get('end_date') 
        transaction_id = payload.get('transaction_id')
        model_id = payload.get('model_id')
        model_name = payload.get('model_name')
        description = payload.get('description')
        is_add_from_hotline = payload.get('is_add_from_hotline')
        
        branch_requester_obj = request.env['res.partner'].search([('code', '=', branch_code)], limit=1)
        if not branch_requester_obj:
            request.env.cr.rollback()
            return invalid_response(400, 'Branch Requester not found', f"Branch Requester not found: {branch_code}")
        
        try :
            main_dealer_obj = request.env['res.company'].get_default_main_dealer()
        except Exception as e:
            request.env.cr.rollback()
            return invalid_response(400, 'Main Dealer not found', f"Main Dealer not found: {e}")

        is_valid, error_msg = validate_payload(payload, mandatory_fields)
        if not is_valid:
            return invalid_response(400, 'Missing mandatory fields', error_msg)

        division = payload.get('division')
        pricelist_id = _get_pricelist(division, main_dealer_obj)
        
        if not pricelist_id:
            request.env.cr.rollback()
            return invalid_response(400, 'Pricelist not found', f"Pricelist not found for division: {division}")
        
        po_type_obj = request.env['tw.stock.distribution']._validate_purchase_order_type(payload.get('type'), division)
        if not po_type_obj:
            return invalid_response(400, 'Purchase Order Type not found', f"Purchase Order Type not found: {payload.get('type')}")
        
        existing_stock_dist = request.env['tw.stock.distribution']._validate_stock_distribution(payload, po_type_obj.id)
        if existing_stock_dist:
            return invalid_response(400, 'Data already exists', f"Stock distribution for origin {payload.get('po_name')} already exists")
        
        mandatory_items = ['default_code', 'qty','attribute_code']
        if division.lower() != 'unit':
            mandatory_items.remove('attribute_code')
        
        line_ids = []
        for item in payload.get('line_ids'):
            is_valid, error_msg = validate_payload(item, mandatory_items)
            if not is_valid:
                request.env.cr.rollback()
                return invalid_response(400, 'Missing mandatory fields', error_msg)

            attribute_code = item.get('attribute_code', False)
            product_code = item.get('default_code', False)
            qty = item.get('qty', False)
            product_obj = request.env['product.product'].search([('default_code', '=', product_code)], limit=1)
            if attribute_code:
                try:
                    product_obj = request.env['product.template'].get_product_variant(product_code, attribute_code)
                except Exception as e:
                    request.env.cr.rollback()
                    return invalid_response(400, 'Product not found', str(e))
            
            if not product_obj:
                request.env.cr.rollback()
                return invalid_response(400, 'Product not found', f"Product {product_code} not found")
            
            if qty <= 0:
                request.env.cr.rollback()
                return invalid_response(400, 'Invalid quantity', "Quantity must be greater than 0")
            try:
                price = pricelist_id.with_company(main_dealer_obj.id)._price_get(product_obj, qty)[pricelist_id.id]
            except Exception as e:
                request.env.cr.rollback()
                return invalid_response(400, 'Price not found', f"Price for product {product_code} not found")
            
            line_ids.append([0, 0, {
                'product_id': product_obj.id,
                'requested_qty': qty,
                'price': price
            }])

        vals = {
                'company_id': main_dealer_obj.id,
                'requester_id': branch_requester_obj.id,
                'start_date': start_date,
                'end_date': end_date,
                'origin': po_name,
                'origin_transaction_id': transaction_id,
                'model_name': model_name,
                'description': description if po_type == 'additional' else po_name,
                'purchase_order_type_id': po_type_obj.id,
                'division': division.title(),
                'stock_distribution_ids': line_ids
            }
        try:
            stock_dist = request.env['tw.stock.distribution'].create(vals)
        except Exception as e:
            request.env.cr.rollback()
            return invalid_response(400, 'Failed to create stock distribution', f"Failed to create stock distribution: {e}")
        
        try:
            stock_dist.stock_distribution_ids.product_id_change()
        except Exception as e:
            request.env.cr.rollback()
            return invalid_response(400, 'Failed to create stock distribution', f"{str(e)}")
        data = {
            'origin': stock_dist.name,
        }
        return valid_response(200, data, 'Stock distribution created successfully')

    @http.route('/api/stock_distribution/<version>/reject_stock_distribution_hotline', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def reject_stock_distribution_hotline(self, version, **kwargs):
        payload = json.loads(request.httprequest.get_data(as_text=True))

        mandatory_fields = ['origin', 'model_name']

        is_valid, error_msg = validate_payload(payload, mandatory_fields)
        if not is_valid:
            return invalid_response(400, 'Missing mandatory fields', error_msg)

        origin = payload.get('origin')
        model_name = payload.get('model_name')

        stock_dist = request.env['tw.stock.distribution'].search([
            ('name', '=', origin),
            ('purchase_order_type_id.name', '=', 'Hotline'),
            ('is_add_from_hotline', '=', True),
            ('model_name', '=', model_name)], limit=1)
        if not stock_dist:
            return invalid_response(404, 'Stock distribution not found', f"Stock distribution dengan Nomor PO {origin} tidak ditemukan")

        if stock_dist.state == 'rejected':
            return valid_response(200, {}, 'Stock distribution is already rejected')

        if stock_dist.state != 'draft':
            return invalid_response(400, 'Stock distribution is not in draft state', f"Stock distribution dengan Nomor PO {origin} tidak bisa di-reject karena statusnya bukan draft")

        try:
            stock_dist.action_reject_request()
            return valid_response(200, {}, 'Stock distribution rejected successfully')
        except Exception as e:
            return invalid_response(400, 'Failed to reject stock distribution', f"Failed to reject stock distribution: {str(e)}")
