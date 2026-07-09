#-*- coding: utf-8 -*-

# 1: imports of python lib
import base64
import json
import logging
import io

from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta
from PIL import Image
# 2: import of known third party lib
from odoo.addons.tw_api.controllers.main import valid_response, invalid_response, check_sensitive_value
from odoo.addons.rest_api.controllers.main import check_valid_token

# 3:  imports of odoo

from odoo import _
from odoo import http

# 4:  imports from odoo modules
from odoo.http import request
from odoo.http import Response
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError

# 5: local imports

# 6: Import of unknown third party lib

_logger = logging.getLogger(__name__)

class ControllerREST(http.Controller):
    @http.route('/api/expedition/<version>/post_submit_expedition', methods=['POST'], type='http', auth='none', csrf=False)
    @check_valid_token
    def post_submit_expedition(self, **params):
        vals = {'delivery_date': datetime.now()}
        if not params.get('picking_id'):
            return invalid_response(400, 'Mandatory Parameter Not Found', 'Parameter picking_id tidak ada.')
        
        picking_obj = request.env['stock.picking'].suspend_security().search([('id','=',params['picking_id'])],limit=1)
        if not picking_obj:
            return invalid_response(400, 'Data Not Found', 'Data Picking tidak ditemukan')

        if params.get('update_state'):
            if picking_obj.delivery_state == 'draft':
                picking_obj.write({
                    'delivery_state': 'intransit',
                    'intransit_date': datetime.now(),
                    'intransit_uid': request.env.user.id,
                })
            else:
                return invalid_response(400, 'Picking State Not Draft', 'Status Picking sudah tidak draft atau picking sudah terkirim')

            data = {
                'picking_id': picking_obj.id,
                'previous_state': picking_obj.delivery_state
            }
            return valid_response(200, data, 'Success Update State to Intransit')
            
        if not params.get('image'):
            return invalid_response(400, 'Mandatory Parameter Not Found', 'Parameter image tidak ada.')

        image = params['image']
        image_binary = image.read() if image else None
        
        if not image_binary:
            return invalid_response(400, 'Image Not Found', 'Foto Expedisi tidak terbaca / kosong.')

        # Kompresi gambar
        try:
            # Buka gambar dengan PIL
            img = Image.open(io.BytesIO(image_binary))
            
            # Convert RGBA ke RGB jika perlu (untuk PNG dengan transparency)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Resize jika terlalu besar (max 1920px)
            max_size = 480
            if img.width > max_size or img.height > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Compress dan simpan ke buffer
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=75, optimize=True)
            compressed_binary = buffer.getvalue()
            
            # Encode ke base64
            image_expedition = base64.b64encode(compressed_binary).decode('utf-8')
            
        except Exception as e:
            _logger.error(f"Error compressing image: {str(e)}")
            return invalid_response(400, 'Image Processing Error', 'Gagal memproses gambar.')

        filename = params.get('filename_image')
        if not filename:
            filename = f"picture_expedition_{params.get('picking_id')}.jpg"

        vals['file_image'] = image_expedition
        vals['filename_upload_image'] = str(filename)
        
        try:
            picking_obj.sudo().write(vals)
            data = {
                'picking_id': picking_obj.id,
                'name': picking_obj.name
            }
            return valid_response(200, data, 'Success Upload Image')
        
        except Exception as error:
            _logger.info(str(error))
            request._cr.rollback()
            return invalid_response(400, "There's an error while uploading image!", str(error))

class ControllerREST(http.Controller):
    @http.route('/api/expedition/<version>/post_submit_extras', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_submit_extras(self, **post):
        post = json.loads(request.httprequest.get_data(as_text=True))
        data = post.get('data')
        if not data:
            return invalid_response(400, 'Mandatory Parameter Not Found', 'Parameter Data tidak ada.')
        
        response = []
        for rec in data:
            move_line_obj = request.env['stock.move.line'].suspend_security().search([('id','=',rec.get('move_line_id'))],limit=1)
            if not move_line_obj:
                return invalid_response(400, 'Data Not Found', 'Data Move Line tidak ditemukan')
            
            try:
                move_line_obj.sudo().write({'actual_quantity': rec.get('quantity')})
                data = {
                    'move_line_id': move_line_obj.id,
                    'product_code' : move_line_obj.product_id.default_code,
                    'quantity' : move_line_obj.quantity,
                    'actual_quantity' : move_line_obj.actual_quantity
                }
                response.append(data)
            
            except Exception as error:
                _logger.info(str(error))
                request._cr.rollback()
                return invalid_response(400, "There's an error while submit extras!", str(error))

        return valid_response(200, response, 'Success Submit Extras')

