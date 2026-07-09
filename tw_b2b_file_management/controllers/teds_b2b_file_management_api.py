from datetime import date, timedelta
from odoo import http
from odoo.http import request
from odoo.addons.rest_api.controllers.main import check_valid_token, valid_response, invalid_response

import json
import logging
_logger = logging.getLogger(__name__)


class MFTPodSalEksport(http.Controller):
    @check_valid_token
    @http.route('/api/teds/mft/pod/sal/eksport', methods=['POST'], type='json', auth='none', csrf=False)
    def mft_pod_sal_eksport(self, **post):
        message = []
        info = ""
        status = False
        try:
            format = post.get('format', '').upper().strip()
            if format not in ['POD', 'SAL']:
                return invalid_response(400, {'message': [{'error': True, 'info': 'Format Harus POD atau SAL'}]})

            model_mapping = {
                'POD': 'tw.export.mft.file.pod',
                'SAL': 'tw.export.mft.file.sal',
            }

            code_mapping = {
                'POD': 'schedule_auto_generate_mft_file_pod',
                'SAL': 'schedule_auto_generate_mft_file_sal'
            }

            model_name = model_mapping.get(format)
            cron_code = code_mapping.get(format)
            cron_obj = request.env['ir.cron'].sudo().search([
                ('model_id.model', '=', model_name),
                ('code', 'ilike', cron_code),
                ('active', 'in', [True, False])
            ], limit=1)
            if cron_obj:
                today = date.today()
                next_execution_date = cron_obj.nextcall.date()
                if next_execution_date < today + timedelta(days=1):
                    cron_obj.write({'nextcall': next_execution_date + timedelta(days=1)})

                    info = "Next Execution Date %s ditambah 1 hari" % cron_obj.name
                    _logger.info(info)
                    message.append({'error': False, 'info': info})
                else:
                    message.append({'error': False, 'info': 'Next call sudah lebih dari H+1, tidak diubah'})

                status = True

            else:
                info = "Scheduler %s tidak ditemukan!" % model_name
                _logger.warning(info)
                message.append({'error': True, 'info': info})

            response = valid_response(200, {'message': message})

        except Exception as exc:
            info = str(exc)
            _logger.exception("Exception saat eksekusi API mft_pod_sal_eksport: %s", info)
            message.append({'error': True, 'info': info})
            response = invalid_response(400, 'Failed', {'message': message})

        model_obj = request.env['ir.model'].sudo().search([('model', '=', 'ir.cron')], limit=1)
        request.env['tw.api.log'].sudo().create({
            'user_id': request.env.user.id,
            'response_code': 200 if status else 400,
            'description': f'Skip H+1 Scheduler {format}',
            'response': response,
            'status_code': 'success' if status else 'failed',
            'model_id': model_obj.id,
            'name': 'Skip POD/SAL',
            'request': str(json.dumps(post)),
            'api_type_id': request.env.ref('tw_b2b_file_management.tw_selection_type_api_mft_pod_sal').id,
        })
        return response