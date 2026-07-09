# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime
import re

# 2: import of known third party lib
import json
import requests

# 3: imports of odoo
from odoo import models, fields, api

# 4: imports from odoo modules
from odoo.exceptions import UserError

# 5: local imports
import logging
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    status_api = fields.Selection([
        ('draft', 'Draft'),
        ('error', 'Error'),
        ('done', 'Done'),
    ], default='draft', string='Status API')

    def api_create_account_invoice(self,limit=10,start_date=False,end_date=False,invoice_number=False):
        request_type = 'post'
        log_obj = self.env['tw.api.log'].sudo()
        model_obj = self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1)
        method_obj = self.env['tw.selection'].sudo().get_selection('ApiMethod', value=request_type)
        account_move_obj = self.env['account.move'].sudo()

        query_where = ""
        if start_date and end_date:
            query_where += f"AND am.invoice_date BETWEEN '{start_date}' AND '{end_date}'"
        if invoice_number:
            query_where += f"AND am.name = '{invoice_number}'"

        search = f"""
            SELECT am.id
            , sd.origin as dms_po_name
            , sd.origin_transaction_id as dms_transaction_id
            , sd.model_name as dms_model_name
            , am.company_id
            , b.parent_id as company_parent_id
            FROM account_move am
            INNER JOIN res_company b ON b.id = am.company_id
            LEFT JOIN tw_selection branch_type ON branch_type.id = b.branch_type_id
            LEFT JOIN tw_sale_order so ON so.name = am.invoice_origin
            LEFT JOIN tw_stock_distribution sd ON sd.id = so.stock_distribution_id
            WHERE branch_type.value = 'MD'
            AND am.state = 'open'
            AND am.move_type = 'out_invoice'
            AND am.status_api = 'draft'
            {query_where}
            ORDER BY am.id ASC
            LIMIT {limit}
        """
        self._cr.execute(search)
        ress = self._cr.dictfetchall()
        if ress:
            for res in ress:
                url = ''
                dms_origin = res.get('dms_po_name')
                dms_transaction_id = res.get('dms_transaction_id')
                dms_model_name = res.get('dms_model_name')
                invoice_id = res.get('id')
                company_id = res.get('company_id')
                company_parent_id = res.get('company_parent_id')

                invoice_obj = self.sudo().browse(invoice_id)
                invoice_name = invoice_obj.name

                # Cek Config per branch
                config_user_branch = self.env['tw.api.configuration'].sudo().search([('company_id', '=', company_parent_id)], limit=1)
                url = config_user_branch.base_url + '/api/sale_order/v1/create_account_invoice'
                if not config_user_branch:
                    log_name = 'Account Move - Config Not Found'
                    message = 'Invoice Supplier %s silahkan buat configuration terlebih dahulu untuk bisa mengakses ke DMS' % invoice_name
                    _logger.warning(message)
                    log_obj.sudo().create_api_log(
                        name=log_name,
                        url=url,
                        description=message,
                        ip_address=False,
                        response=False,
                        payload=False,
                        header=False,
                        response_code=False,
                        status_code=False,
                        reference=False,
                        transaction_id=invoice_id,
                        api_type_id=config_user_branch.api_type_id.id,
                        method_id=False,
                        model_id=model_obj.id,
                    )
                    account_move_obj.browse(invoice_id).write({'status_api': 'error'})
                    continue

                line = []
                for x in invoice_obj.invoice_line_ids:
                    if invoice_obj.division == 'Unit':
                        warna = """
                            SELECT pav.code as warna
                            FROM product_product pp
                            INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id 
                            LEFT JOIN product_variant_combination vcom ON vcom.product_product_id = pp.id
                            LEFT JOIN product_template_attribute_value ptav ON ptav.id = vcom.product_template_attribute_value_id
                            LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id 
                            WHERE pp.id = %s LIMIT 1
                        """
                        self._cr.execute(warna, (x.product_id.id,))
                        res_warna = self._cr.dictfetchall()
                        warna_code = res_warna[0].get('warna') if res_warna else False

                        line.append({
                            'product_code': x.product_id.default_code or '',
                            'warna_code': warna_code or '',
                            'description': x.name or '',
                            'quantity': x.quantity,
                            'price': x.price_unit,
                            'discount': x.discount,
                        })
                    else:
                        line.append({
                            'product_code': x.product_id.default_code or '',
                            'description': x.name or '',
                            'quantity': x.quantity,
                            'price': x.price_unit,
                            'discount': x.discount,
                        })

                try:
                    headers = {
                        'Content-Type': 'application/json',
                        'access_token': config_user_branch.token
                    }

                    payload = {
                        'code_md': invoice_obj.company_id.code or '',
                        'code_dealer': invoice_obj.partner_id.code or '',
                        'dms_origin': dms_origin or '',
                        'dms_model_name': dms_model_name or '',
                        'dms_transaction_id': dms_transaction_id or 0,
                        'origin': invoice_obj.name or '',
                        'date_due': invoice_obj.invoice_date_due.strftime('%Y-%m-%d') if invoice_obj.invoice_date_due else '',
                        'date_invoice': invoice_obj.invoice_date.strftime('%Y-%m-%d') if invoice_obj.invoice_date else '',
                        'detail': line,
                        'division': invoice_obj.division or '',
                        'discount_cash': invoice_obj.discount_cash if hasattr(invoice_obj, 'discount_cash') else 0,
                        'discount_program': invoice_obj.discount_program if hasattr(invoice_obj, 'discount_program') else 0,
                        'discount_lain': invoice_obj.discount_lain if hasattr(invoice_obj, 'discount_lain') else 0,
                        'source_document': invoice_obj.ref or '',
                        'comment': re.sub('<[^<]+?>', '', invoice_obj.narration or '').strip(),
                        'amount_total': invoice_obj.amount_total,
                    }

                    request_timestamp = datetime.now()
                    response = requests.post(url, data=json.dumps(payload), headers=headers)

                    _logger.info(">>>>>>>> %s -> api_create_account_invoice request time : %s" % (self._name, str(datetime.now() - request_timestamp)))
                    response_data = response.json() if response.content else {}

                    if response_data:
                        result_status = response_data.get('status')
                        result_message = response_data.get('message', False)
                        result_error = response_data.get('error', False)
                        result_remark = response_data.get('remark', False)

                        if result_status == 0:
                            _logger.warning(result_message)
                            log_obj.sudo().create_api_log(
                                name=result_error or 'Account Move - Unknown Error',
                                url=url,
                                description=result_remark or '',
                                ip_address=url,
                                response=json.dumps(response_data),
                                payload=json.dumps(payload),
                                header=json.dumps(headers),
                                response_code=False,
                                status_code=0,
                                reference=False,
                                transaction_id=invoice_id,
                                api_type_id=config_user_branch.api_type_id.id,
                                method_id=method_obj.id if method_obj else False,
                                model_id=model_obj.id,
                            )
                            account_move_obj.browse(invoice_id).write({'status_api': 'error'})

                        elif result_status == 1:
                            _logger.warning(result_message)
                            account_move_obj.browse(invoice_id).write({'status_api': 'done'})
                    else:
                        message = 'Invoice %s Result not found !' % invoice_name
                        log_name = 'Account Move - Data Not Found'
                        _logger.warning(message)
                        log_obj.sudo().create_api_log(
                            name=log_name,
                            url=url,
                            description=message,
                            ip_address=False,
                            response=False,
                            payload=False,
                            header=False,
                            response_code=False,
                            status_code=False,
                            reference=False,
                            transaction_id=invoice_id,
                            api_type_id=config_user_branch.api_type_id.id,
                            method_id=False,
                            model_id=model_obj.id,
                        )
                        account_move_obj.browse(invoice_id).write({'status_api': 'error'})

                except Exception as exc:
                    _logger.warning(str(exc))
                    log_obj.sudo().create_api_log(
                        name='Account Move - Connection Error',
                        url=url,
                        description=str(exc),
                        ip_address=False,
                        response=False,
                        payload=False,
                        header=False,
                        response_code=False,
                        status_code=False,
                        reference=False,
                        transaction_id=invoice_id,
                        api_type_id=config_user_branch.api_type_id.id,
                        method_id=False,
                        model_id=model_obj.id,
                    )
                    account_move_obj.browse(invoice_id).write({'status_api': 'error'})
        else:
            _logger.warning('Data Update Error to Draft Account Move')
            account_move_obj = self.env['account.move'].sudo()
            account_move_obj.search([('status_api', '=', 'error'), ('move_type', '=', 'out_invoice')]).write({'status_api': 'draft'})