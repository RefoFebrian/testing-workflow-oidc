from datetime import datetime, date
import pytz
from pytz import timezone
import time

import logging
_logger = logging.getLogger(__name__)

from odoo import models, fields, api
from odoo.exceptions import UserError as Warning
# API
from json import dumps as json
from pprint import pprint as pp
import requests

class TwWorkOrder(models.Model):
    _inherit = "tw.work.order"
    
    @api.model
    def _get_default_date(self):
        return self.env['res.company'].get_default_date()

    sa_number = fields.Char('No Service Advisor')
    status_api = fields.Selection([
        ('draft','Draft'),
        ('error','Error'),
        ('done','Done'),
    ],default='draft',string='Status API')
    is_error_wo = fields.Boolean('DMS Error?')
    api_last_try_date = fields.Datetime(string='API Last Try', default=_get_default_date)
    
    def action_error_detail(self):
        logs = self.env['tw.api.log'].sudo().search([
            ('model_id.model','=','tw.work.order'),
            ('transaction_id','=',str(self.id))
        ])
        tree_id = self.env.ref('tw_api_configuration.view_tw_api_log_tree').id
        ids = [log.id for log in logs]
        return {
            'name': ('Error API'),
            'res_model': 'tw.api.log',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'views': [(tree_id, 'tree')],
            'view_mode': 'tree',
            'target': 'current',
            'view_type': 'form',
            'domain':[('id','in',ids)]
        }        

    def action_send_work_order_single(self):
        self.send_work_order_single(self.name)
        
    # MANUAL SLS / NON SLS
    # TODO: AREA_LAMPUNG belum ada pada data tw_area
    # TODO: Jika res_area_company_rel pakai company_id maka company_id diubah
    def send_work_order_single(self, origin):
        query = f"""
            SELECT wo.id, type.value as type
            FROM tw_work_order wo
            INNER JOIN (
                SELECT acr.company_id
                FROM res_area_company_rel acr 
                INNER JOIN res_area area ON area.id = acr.area_id
                WHERE area.code = 'AREA_LAMPUNG'
            ) cabang ON cabang.company_id = wo.company_id
            LEFT JOIN tw_selection type ON type.id = wo.type_id
            WHERE wo.name = '{origin}'
            AND wo.state in ('sale','done')
            AND wo.status_api in ('draft')
            LIMIT 1
        """
        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        for res in ress:
            self.api_work_order([res.get('id')])

    # 1 menit 1x NON SLS, EXCLUDE ERROR
    def send_work_order_limit(self,limit=5):
        # # NOTE: menggunakan pytz karena datetime.now() memberi nilai waktu UTC
        # now = pytz.UTC.localize(datetime.now()).astimezone(timezone('Asia/Jakarta'))
        # # NOTE: mencegah SerializationError a.k.a. scheduler bertabrakan maka waktu jalannya dibedakan
        # if now.hour >= 19 or now.hour < 8:
        #     _logger.warning("Kirim WO ke DMS: Exiting cause its not the right time...")
        #     return
        # # if its the time
        query = """
            SELECT wo.id
            FROM tw_work_order wo
            INNER JOIN (
                SELECT acr.company_id
                 FROM res_area_company_rel acr 
                 INNER JOIN res_area area ON area.id = acr.area_id
                 WHERE area.code = 'AREA_LAMPUNG'
            ) cabang ON cabang.company_id = wo.company_id
            LEFT JOIN tw_selection type ON type.id = wo.type_id
            WHERE wo.state in ('sale','done')
            AND wo.status_api in ('draft')
            AND type.value != 'SLS'
            AND wo.sa_number is not null
            AND (wo.is_error_wo = False OR wo.is_error_wo IS NULL)
            ORDER BY wo.api_last_try_date,wo.id
            LIMIT %d
        """ %(limit)
        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        if ress:
            self.api_work_order([res.get('id') for res in ress])
    
    # 1 menit 1x SLS / NON SLS ERROR
    def send_work_order_error(self,limit=5):
        # # NOTE: menggunakan pytz karena datetime.now() memberi nilai waktu UTC
        # now = pytz.UTC.localize(datetime.now()).astimezone(timezone('Asia/Jakarta'))
        # # NOTE: mencegah SerializationError a.k.a. scheduler bertabrakan maka waktu jalannya dibedakan
        # if now.hour >= 19 or now.hour < 8:
        #     _logger.warning("Kirim WO Error ke DMS: Exiting cause its not the right time...")
        #     return
        # if its the time
        query = """
            SELECT wo.id
            , type.value as type
            FROM tw_work_order wo
            INNER JOIN (
                SELECT acr.company_id
                 FROM res_area_company_rel acr 
                 INNER JOIN res_area area ON area.id = acr.area_id
                 WHERE area.code = 'AREA_LAMPUNG'
            ) cabang ON cabang.company_id = wo.company_id
            LEFT JOIN tw_selection type ON type.id = wo.type_id
            WHERE wo.state in ('sale','done')
            AND wo.status_api in ('draft','error')
            AND wo.is_error_wo = True
            ORDER BY wo.api_last_try_date ASC
            LIMIT %d
        """ %(limit)
        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        non_sls = []
        for res in ress:
            non_sls.append(res.get('id'))

        if non_sls:
            self.api_work_order(non_sls)

        # Update WO status API error to draft
        else:
            _logger.warning('Data Update Error to Draft Work Order')
            work_order_obj = self.env['tw.work.order'].sudo().search([('status_api', '=', 'error')])
            work_order_obj.write({'status_api': 'draft'})

    def api_work_order(self,datas):
        log_obj = self.env['tw.api.log']
        # API Config
        model_obj = self.env['ir.model'].sudo().search([('model','=',self._name)], limit=1)        

        for data in datas:
            work_order = self.env['tw.work.order'].sudo().browse(data)
            if work_order:
                _logger.info('Data found %s (ID %d)' % (work_order.name, work_order.id))

            config_user = self.env['tw.api.configuration'].sudo().search([('company_id', '=', work_order.company_id.id)], limit=1)
            if not config_user:
                message = 'Silahkan buat configuration terlebih dahulu (Company %s)' % work_order.company_id.name
                _logger.warning('%s' % message)
                log_name = 'Work Order - API Configuration Not Found'
                cek_log = log_obj.search([
                    ('name','=',log_name),
                    ('description','=',message),
                    ('transaction_id','=',work_order.id),
                    ('api_type_id','=',config_user.api_type_id.id),
                    ('model_id','=',model_obj.id)],limit=1)
                if not cek_log:
                    log_obj.sudo().create_api_log(
                        name=log_name,
                        url=False,
                        description=message,
                        ip_address=False,
                        response=False,
                        payload=False,
                        header=False,
                        response_code=False,
                        status_code=False,
                        reference=False,
                        transaction_id=work_order.id,
                        api_type_id=config_user.api_type_id.id,
                        method_id=False,
                        model_id=model_obj.id,
                    )
                continue

            # Check Access Token
            if not config_user.token:
                config_user.action_get_token()

            # Check URL
            if not config_user.base_url:
                message = 'Silahkan tambahkan URL terlebih dahulu (Company %s)' % work_order.company_id.name
                _logger.warning('%s' % message)
                log_name = 'Work Order - API Base URL Not Found'
                cek_log = log_obj.search([
                    ('name','=',log_name),
                    ('description','=',message),
                    ('transaction_id','=',work_order.id),
                    ('api_type_id','=',config_user.api_type_id.id),
                    ('model_id','=',model_obj.id)],limit=1)
                if not cek_log:
                    log_obj.sudo().create_api_log(
                        name=log_name,
                        url=False,
                        description=message,
                        ip_address=False,
                        response=False,
                        payload=False,
                        header=False,
                        response_code=False,
                        status_code=False,
                        reference=False,
                        transaction_id=work_order.id,
                        api_type_id=config_user.api_type_id.id,
                        method_id=False,
                        model_id=model_obj.id,
                    )
                continue
            url = config_user.base_url + '/api/workshop/v1/create_service_order'
            message = False
            # Type Service
            # [KPB =  1 , REG = 2 , WAR = 3 , CLA = 4 , PDI = 5]
            type_service = work_order.type_id.value
            if type_service not in ['KPB','REG','WAR','CLA','PDI','HOTLINE']:
                message = 'Tipe service %s tidak dikenal' % (type_service)
                _logger.warning('%s' % message)
                log_name = 'Work Order - Data Not Found'
                cek_log =  log_obj.search([
                    ('name','=',log_name),
                    ('description','=',message),
                    ('transaction_id','=',work_order.id),
                    ('api_type_id','=',config_user.api_type_id.id),
                    ('model_id','=',model_obj.id)],limit=1)
                if not cek_log:
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
                        transaction_id=work_order.id,
                        api_type_id=config_user.api_type_id.id,
                        method_id=False,
                        model_id=model_obj.id,
                    )
            if type_service == 'PDI':
                type_service = 'REG'
            
            # Alasan ke AHASS
            reason_to_ahass_value = work_order.reason_to_ahass_id.value
            # Keluhan Konsumen
            keluhan_konsumen = work_order.note
            # Kondisi Bensin
            # [25% = 1 , 50% = 2 , 75% = 3 , 100% = 4]
            kondisi_bensin = int(work_order.fuel)
            if kondisi_bensin == 0 or kondisi_bensin == 25:
                kondisi_bensin = 1
            elif kondisi_bensin == 50:
                kondisi_bensin = 2
            elif kondisi_bensin == 75:
                kondisi_bensin = 3
            elif kondisi_bensin == 100:
                kondisi_bensin = 4
            else:
                message = 'Bensin %s tidak dikenal' % (kondisi_bensin)
                log_name = 'Work Order - Data Not Found'
                _logger.warning('%s' % message)
                cek_log = log_obj.search([
                    ('name','=',log_name),
                    ('description','=',message),
                    ('transaction_id','=',work_order.id),
                    ('api_type_id','=',config_user.api_type_id.id),
                    ('model_id','=',model_obj.id)],limit=1)
                if not cek_log:
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
                        transaction_id=work_order.id,
                        api_type_id=config_user.api_type_id.id,
                        method_id=False,
                        model_id=model_obj.id,
                    )
            # Detail
            line = []
            query = """ 
                SELECT 
                    wol.division AS category,
                    pt.default_code AS product_code,
                    SUM(
                        CASE 
                            WHEN wol.division = 'Sparepart' AND wol.price_unit > 0 THEN wol.qty_delivered 
                            ELSE 0 
                        END
                    ) AS qty_spl_part,
                    SUM(
                        CASE 
                            WHEN wol.division = 'Service' AND wol.price_unit > 0 THEN wol.product_uom_qty 
                            ELSE 0 
                        END
                    ) AS qty_spl_service,
                    SUM(wol.discount) AS discount_cumulative,
                    SUM(
                        CASE 
                            WHEN wol.division = 'Service' THEN wol.product_uom_qty * wol.price_unit 
                            WHEN wol.division = 'Sparepart' THEN wol.qty_delivered * wol.price_unit 
                        END
                    ) AS price_cumulative
                FROM tw_work_order_line wol 
                LEFT JOIN product_product pp ON wol.product_id = pp.id
                LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
                WHERE wol.order_id = %d 
                GROUP BY 1, 2
            """ % (work_order.id)
            self._cr.execute(query)
            ress = self._cr.dictfetchall()
            for res in ress:
                qty_delivered = 0
                discount = 0
                price = 0
                if res.get('category',False) == 'Service':
                    qty_delivered = float(res.get('qty_spl_service',0))
                elif res.get('category',False) == 'Sparepart':
                    qty_delivered = float(res.get('qty_spl_part',0))
                else:
                    message = '[DETAIL] Kategori %s tidak valid' % (res.get('category',False))
                    log_name = 'Work Order - Data Not Valid'
                    _logger.warning('%s' % message)
                    cek_log = log_obj.search([
                        ('name','=',log_name),
                        ('description','=',message),
                        ('transaction_id','=',work_order.id),
                        ('api_type_id','=',config_user.api_type_id.id),
                        ('model_id','=',model_obj.id)],limit=1)
                    if not cek_log:
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
                            transaction_id=work_order.id,
                            api_type_id=config_user.api_type_id.id,
                            method_id=False,
                            model_id=model_obj.id,
                        )            
                try:
                    discount = float(res.get('discount_cumulative',0))/qty_delivered
                    price = float(res.get('price_cumulative',0))/qty_delivered
                except Exception as exc:
                    message = 'Setup detail %s: %s' % (work_order.name, exc)
                    log_name = 'Work Order - Error'
                    _logger.warning('%s' % message)
                    cek_log = log_obj.search([
                        ('name','=',log_name),
                        ('description','=',message),
                        ('transaction_id','=',work_order.id),
                        ('api_type_id','=',config_user.api_type_id.id),
                        ('model_id','=',model_obj.id)],limit=1)
                    if not cek_log:
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
                            transaction_id=work_order.id,
                            api_type_id=config_user.api_type_id.id,
                            method_id=False,
                            model_id=model_obj.id,
                        )
                line.append({
                    'category': res.get('category',False),
                    'product_code': res.get('product_code',False),
                    'qty': qty_delivered,
                    'diskon': discount,
                    'price': price,
                })
            # Hasil cek: ada potensi error
            if message:
                work_order_obj = self.env['tw.work.order'].sudo().search([('id', '=', work_order.id)])
                work_order_obj.write({'status_api': 'error', 'is_error_wo': True})
            # Hasil cek: OK => Send to DMS
            else:
                try:
                    payload = {
                        # DMS Mandatory Fields
                        'dealer_code': work_order.company_id.code if work_order.company_id.code else '',
                        'date': work_order.date.strftime('%Y-%m-%d') if work_order.date else '',
                        'nomor_sa': work_order.sa_number if work_order.sa_number else '',
                        'service_type': type_service if type_service else '',
                        'detail': line,
                        # End of DMS Mandatory Fields
                        'kpb_ke': work_order.kpb_ke if work_order.kpb_ke else '',
                        'no_engine': work_order.lot_id.name if work_order.lot_id.name else '',
                        'pembawa_sendiri': True if work_order.customer_stnk_id.id == work_order.partner_id.id else False,
                        'pembawa_name': work_order.partner_id.name if work_order.partner_id.name else '',
                        'pembawa_mobile': work_order.mobile if work_order.mobile else '',
                        'km': work_order.km if work_order.km else '',
                        'alasan_ke_ahass': reason_to_ahass_value if reason_to_ahass_value else '',
                        'kebutuhan_konsumen': keluhan_konsumen if keluhan_konsumen else '',
                        'mekanik_tunasId': self._get_tunas_id_sales(work_order.mechanic_id.id) if self._get_tunas_id_sales(work_order.mechanic_id.id) else '',
                        'kondisi_bensin': kondisi_bensin if kondisi_bensin else '',
                        'start': work_order.start_date.strftime('%Y-%m-%d %H:%M:%S') if work_order.start_date else '',
                        'finish': work_order.finish_date.strftime('%Y-%m-%d %H:%M:%S') if work_order.finish_date else '',
                        'state_lcr': work_order.state_lcr if work_order.state_lcr else '',
                        'notifikasi': work_order.notification if work_order.notification else '',
                        'kesediaan_konsumen': work_order.consumer_willingness if work_order.consumer_willingness else '',
                        'hasil_pengecekan': work_order.check_results if work_order.check_results else '',
                        'no_buku_claim': work_order.claim_number if work_order.claim_number else ''
                    }

                    # TODO: For testing DMS ASP only, sesuaikan pada TETO ASP
                    if 'asper' in url.lower():
                        payload['chassis_no'] = work_order.chassis_number
                        payload['prod_code'] = work_order.product_id.default_code
                        payload['prod_warna'] = self._get_product_color(work_order.product_id.id)
                        payload['name_stnk'] = work_order.customer_stnk_id.name
                        payload['ktp_stnk'] = work_order.customer_stnk_id.identification_number
                        payload['no_work_order'] = work_order.name
                        payload['est_waktu_pendaftaran'] = work_order.start_date.strftime('%Y-%m-%d %H:%M:%S') if work_order.start_date else ''
                        payload['est_waktu_selesai'] = work_order.finish_date.strftime('%Y-%m-%d %H:%M:%S') if work_order.finish_date else ''

                    headers = {
                        'Content-Type': 'application/json',
                        'access_token': config_user.token
                    }
                    
                    # Send as data with JSON string because external decorator changes type to 'http'
                    response = requests.post(url, data=json(payload), headers=headers)

                    if response.status_code == 200:
                        result = response.json()
                        if result.get('status') == 0:
                            _logger.warning('%s' % result.get('message'))
                            log_obj.sudo().create_api_log(
                                name=result.get('error', 'unknown_error'),
                                url=url,
                                description=result.get('remark', ''),
                                ip_address=False,
                                response=False,
                                payload=False,
                                header=False,
                                response_code=False,
                                status_code=0,
                                reference=False,
                                transaction_id=work_order.id,
                                api_type_id=config_user.api_type_id.id,
                                method_id=False,
                                model_id=model_obj.id,
                            )
                            work_order_obj = self.env['tw.work.order'].sudo().search([('id', '=', work_order.id)])
                            work_order_obj.write({'status_api': 'error', 'is_error_wo': True})
                        elif result.get('status') == 1:
                            _logger.warning('%s' % result.get('message'))
                            work_order_obj = self.env['tw.work.order'].sudo().search([('id', '=', work_order.id)])
                            work_order_obj.write({'status_api': 'done', 'is_error_wo': False})
                            model_obj = self.env['ir.model'].sudo().search([('model', '=', 'tw.work.order')])
                            api_log_obj = self.env['tw.api.log'].sudo().search([('transaction_id', '=', work_order.id), ('model_id', '=', model_obj.id)])
                            api_log_obj.unlink()
                            return {}
                    else:
                        log_obj.sudo().create_api_log(
                            name='Work Order - Connection Error',
                            url=url,
                            description=response.text,
                            ip_address=False,
                            response=False,
                            payload=False,
                            header=False,
                            response_code=False,
                            status_code=False,
                            reference=False,
                            transaction_id=work_order.id,
                            api_type_id=config_user.api_type_id.id,
                            method_id=False,
                            model_id=model_obj.id,
                        )
                        work_order_obj = self.env['tw.work.order'].sudo().search([('id', '=', work_order.id)])
                        work_order_obj.write({'status_api': 'error', 'is_error_wo': True})

                except Exception as exc:
                    _logger.warning('%s' % (exc))
                    log_obj.sudo().create_api_log(
                            name='Work Order - Connection Error',
                            url=url,
                            description=str(exc),
                            ip_address=False,
                            response=False,
                            payload=False,
                            header=False,
                            response_code=False,
                            status_code=False,
                            reference=False,
                            transaction_id=work_order.id,
                            api_type_id=config_user.api_type_id.id,
                            method_id=False,
                            model_id=model_obj.id,
                        )
                    work_order_obj = self.env['tw.work.order'].sudo().search([('id', '=', work_order.id)])
                    work_order_obj.write({'status_api': 'error', 'is_error_wo': True})
            self._cr.commit()

    def _get_tunas_id_sales(self,user_id):
        nip = False 
        emp = self.env['hr.employee'].sudo().search([('user_id','=',user_id)],limit=1)
        if emp:
            nip = emp.code_honda
        return nip 

    def _get_product_color(self,product_id):
        color = False
        if product_id:
            query = """
                SELECT pav.code as color
                FROM product_product pp
                LEFT JOIN product_variant_combination vcom on vcom.product_product_id = pp.id
                LEFT JOIN product_template_attribute_value ptav ON ptav.id = vcom.product_template_attribute_value_id
                LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id 
                WHERE pp.id = %s
            """
            self.env.cr.execute(query, (product_id,))
            result = self.env.cr.fetchone()
            if result:
                color = result[0]
        return color