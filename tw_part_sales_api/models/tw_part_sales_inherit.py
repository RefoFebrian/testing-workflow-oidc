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

class TwPartSales(models.Model):
    _inherit = "tw.part.sales"
    
    @api.model
    def _get_default_date(self):
        return self.env['res.company'].get_default_date()

    ps_number = fields.Char('Ref Part Sales (NMS)')
    status_api = fields.Selection([
        ('draft','Draft'),
        ('error','Error'),
        ('done','Done'),
    ],default='draft',string='Status API')
    is_error_ps = fields.Boolean('DMS Error?')
    api_last_try_date = fields.Datetime(string='API Last Try', default=_get_default_date)
    
    def action_error_detail(self):
        logs = self.env['tw.api.log'].sudo().search([
            ('model_name','=','tw.part.sales'),
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

    def action_send_part_sales_single(self):
        self.send_part_sales_single(self.name)
        
    # MANUAL SLS / NON SLS
    # TODO: AREA_LAMPUNG belum ada pada data tw_area
    # TODO: Jika res_area_company_rel pakai company_id maka company_id diubah
    def send_part_sales_single(self, origin):
        query = f"""
            SELECT ps.id
            FROM tw_part_sales ps
            INNER JOIN (
                SELECT acr.company_id
                FROM res_area_company_rel acr 
                INNER JOIN res_area area ON area.id = acr.area_id
                WHERE area.code = 'AREA_LAMPUNG'
            ) cabang ON cabang.company_id = ps.company_id
            WHERE name = '{origin}'
            AND ps.state in ('sale','done')
            AND ps.status_api in ('draft')
            LIMIT 1
        """
        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        for res in ress:
            self.api_part_sales([res.get('id')])
    
    # 1 menit 1x ERROR
    def send_part_sales_error(self,limit=5):
        # # NOTE: menggunakan pytz karena datetime.now() memberi nilai waktu UTC
        # now = pytz.UTC.localize(datetime.now()).astimezone(timezone('Asia/Jakarta'))
        # # NOTE: mencegah SerializationError a.k.a. scheduler bertabrakan maka waktu jalannya dibedakan
        # if now.hour >= 19 or now.hour < 8:
        #     _logger.warning("Kirim WO Error ke DMS: Exiting cause its not the right time...")
        #     return
        # if its the time
        query = """
            SELECT ps.id
            FROM tw_part_sales ps
            INNER JOIN (
                SELECT acr.company_id
                 FROM res_area_company_rel acr 
                 INNER JOIN res_area area ON area.id = acr.area_id
                 WHERE area.code = 'AREA_LAMPUNG'
            ) cabang ON cabang.company_id = ps.company_id
            WHERE ps.state in ('sale','done')
            AND ps.status_api in ('draft','error')
            AND ps.is_error_ps = True
            ORDER BY ps.api_last_try_date ASC
            LIMIT %d
        """ %(limit)
        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        sls = []
        for res in ress:
            sls.append(res.get('id'))

        if sls:
            self.api_part_sales(sls)

        # Update WO status API error to draft
        else:
            part_sales_obj = self.env['tw.part.sales'].sudo().search([('status_api','=','error')])
            _logger.info('Data Update Error to Draft Work Order')
            part_sales_obj.write({
                'status_api': 'draft',
                'is_error_ps': False,
            })

    # 1 menit 1x SLS, EXCLUDE ERROR
    def send_part_sales(self):
        # # NOTE: menggunakan pytz karena datetime.now() memberi nilai waktu UTC
        # now = pytz.UTC.localize(datetime.now()).astimezone(timezone('Asia/Jakarta'))
        # # NOTE: mencegah SerializationError a.k.a. scheduler bertabrakan maka waktu jalannya dibedakan
        # if now.hour >= 19 or now.hour < 8:
        #     _logger.warning("Kirim WO SLS ke DMS: Exiting cause its not the right time...")
        #     return
        # # if its the time
        query = """
            SELECT ps.id
            FROM tw_part_sales ps
            INNER JOIN (
                SELECT acr.company_id
                 FROM res_area_company_rel acr 
                 INNER JOIN res_area area ON area.id = acr.area_id
                 WHERE area.code = 'AREA_LAMPUNG'
            ) cabang ON cabang.company_id = ps.company_id
            WHERE ps.state in ('sale','done')
            AND ps.status_api in ('draft')
            AND create_date >= '2018-12-30'
            AND (is_error_ps = False OR is_error_ps IS NULL)
            ORDER BY id ASC
            LIMIT 20
        """
        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        if ress:
            self.api_part_sales([res.get('id') for res in ress])

    def api_part_sales(self,datas):
        log_obj = self.env['tw.api.log']
        # API Config
        model_obj = self.env['ir.model'].sudo().search([('model','=',self._name)], limit=1)
        for data in datas:
            message = False
            part_sales = self.env['tw.part.sales'].sudo().browse(data)
            if part_sales:
                _logger.info('Data found %s SLS (ID %d)' % (part_sales.name, part_sales.id))
            config_user = self.env['tw.api.configuration'].sudo().search([('company_id', '=', part_sales.company_id.id)], limit=1)
            if not config_user:
                message = 'Silahkan buat configuration terlebih dahulu (Company %s)' % part_sales.company_id.name
                _logger.warning('%s' % message)
                log_name = 'Part Sales - API Configuration Not Found'
                cek_log = log_obj.search([
                    ('name','=',log_name),
                    ('description','=',message),
                    ('transaction_id','=',part_sales.id),
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
                        transaction_id=part_sales.id,
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
                message = 'Silahkan tambahkan URL terlebih dahulu (Company %s)' % part_sales.company_id.name
                _logger.warning('%s' % message)
                log_name = 'Part Sales - API Base URL Not Found'
                cek_log = log_obj.search([
                    ('name','=',log_name),
                    ('description','=',message),
                    ('transaction_id','=',part_sales.id),
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
                        transaction_id=part_sales.id,
                        api_type_id=config_user.api_type_id.id,
                        method_id=False,
                        model_id=model_obj.id,
                    )
                continue

            url = config_user.base_url + '/api/workshop/v1/create_part_sales'            
            # Detail
            line = []
            query = """ 
                SELECT 
                    'Sparepart' AS category,
                    pt.default_code AS product_code,
                    SUM(psl.qty_delivered) AS qty_spl_part,
                    SUM(psl.discount) AS discount_cumulative,
                    SUM(psl.qty_delivered * psl.price_unit) AS price_cumulative
                FROM tw_part_sales_line psl 
                LEFT JOIN product_product pp ON psl.product_id = pp.id
                LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
                WHERE psl.order_id = %d 
                GROUP BY 1, 2
            """ % (part_sales.id)
            self._cr.execute(query)
            ress = self._cr.dictfetchall()
            for res in ress:
                discount = 0
                price = 0
                qty_delivered = float(res.get('qty_spl_part',0))
                
                try:
                    discount = float(res.get('discount_cumulative', 0)) / qty_delivered if qty_delivered else 0.0
                    price = float(res.get('price_cumulative', 0)) / qty_delivered if qty_delivered else 0.0
                except Exception as exc:
                    message = 'Setup detail %s: %s' % (part_sales.name, exc)
                    log_name = 'Part Sales - Error'
                    _logger.warning('%s' % message)
                    cek_log = log_obj.search([
                        ('name','=',log_name),
                        ('description','=',message),
                        ('transaction_id','=',part_sales.id),
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
                            transaction_id=part_sales.id,
                            api_type_id=config_user.api_type_id.id,
                            method_id=False,
                            model_id=model_obj.id,
                        )
                vals = {
                    'product_code': res.get('product_code',False),
                    'qty': qty_delivered,
                    'discount': discount,
                    'price': price,
                }
                line.append(vals)
            # Hasil cek: ada potensi error
            if message:
                tw_part_sales_obj = self.env['tw.part.sales'].sudo().browse(part_sales.id)
                tw_part_sales_obj.write({
                    'status_api': 'error',
                    'is_error_ps': True,
                    'api_last_try_date': str(datetime.now())
                })
            # Hasil cek: OK => Send to DMS
            else:
                try:
                    # header untuk authentication (jika Basic 
                    # 
                    headers = {
                        'Content-Type': 'application/json',
                        'access_token': config_user.token
                    }   

                    if part_sales.partner_stnk_id:
                        customer_no_ktp = part_sales.partner_stnk_id.identification_number
                        customer_name = part_sales.partner_stnk_id.name or part_sales.partner_stnk_id.code
                        customer_street = part_sales.partner_stnk_id.street
                        customer_rt = part_sales.partner_stnk_id.rt
                        customer_rw = part_sales.partner_stnk_id.rw
                        customer_prov = part_sales.partner_stnk_id.state_id.code
                        customer_kota = part_sales.partner_stnk_id.city_id.code
                        customer_kecamatan = part_sales.partner_stnk_id.district_id.code
                        customer_kelurahan = part_sales.partner_stnk_id.sub_district_id.zip_code
                        customer_type = part_sales.partner_type
                    else:
                        customer_no_ktp = part_sales.partner_id.identification_number
                        customer_name = part_sales.partner_id.name or part_sales.partner_id.code
                        customer_street = part_sales.partner_id.street
                        customer_rt = part_sales.partner_id.rt
                        customer_rw = part_sales.partner_id.rw
                        customer_prov = part_sales.partner_id.state_id.code
                        customer_kota = part_sales.partner_id.city_id.code
                        customer_kecamatan = part_sales.partner_id.district_id.code
                        customer_kelurahan = part_sales.partner_id.sub_district_id.zip_code
                        customer_type = part_sales.partner_type

                    # buat body data (sama seperti sebelumnya)
                    vals = {
                        'dealer_code': part_sales.company_id.code,
                        'date': part_sales.date_order.strftime('%Y-%m-%d'),
                        'part_sales_name': part_sales.name,
                        'no_engine': part_sales.lot_id.name,
                        'customer_stnk_no_ktp': customer_no_ktp,
                        'customer_stnk_name': customer_name,
                        'customer_stnk_street': customer_street,
                        'customer_stnk_rt': customer_rt,
                        'customer_stnk_rw': customer_rw,
                        'customer_stnk_prov': customer_prov,
                        'customer_stnk_kota': customer_kota,
                        'customer_stnk_kecamatan': customer_kecamatan,
                        'customer_stnk_kelurahan': customer_kelurahan,
                        'customer_type': customer_type,
                        # 'is_ev': ev,
                        'detail': line
                    }

                    if part_sales.partner_stnk_id.company_id.id == part_sales.company_id.id:
                        if part_sales.partner_stnk_id.id == part_sales.partner_id.id:
                            vals.update({'customer_stnk_no_hp': part_sales.mobile})
                        else:
                            vals.update({'customer_stnk_no_hp': part_sales.partner_stnk_id.mobile})

                    if part_sales.ps_number:
                        vals.update({'ps_number': part_sales.ps_number})

                    request_timestamp = datetime.now()

                    payload = vals
                    response = requests.post(url, data=json(payload), headers=headers)
                    response.raise_for_status()  # raise error jika status bukan 2xx

                    data = response.json()

                    result = data.get('result', False)
                    if result:
                        if result['status'] == 0:
                            _logger.warning('%s' % result.get('message', False))
                            log_name = result.get('error', False)
                            cek_log = log_obj.search([
                                ('name', '=', log_name),
                                ('description', '=', result.get('remark', False)),
                                ('transaction_id', '=', part_sales.id),
                                ('api_type_id', '=', config_user.api_type_id.id),
                                ('model_id', '=', model_obj.id)], limit=1)
                            log_obj.sudo().create_api_log(
                                name=log_name,
                                url=url,
                                description=result.get('remark', False),
                                ip_address=False,
                                response=False,
                                payload=False,
                                header=False,
                                response_code=False,
                                status_code=0,
                                reference=False,
                                transaction_id=part_sales.id,
                                api_type_id=config_user.api_type_id.id,
                                method_id=False,
                                model_id=model_obj.id,
                            )
                            tw_part_sales_obj = self.env['tw.part.sales'].browse(part_sales.id)
                            tw_part_sales_obj.write({
                                'status_api': 'error',
                                'is_error_ps': True
                            })

                        elif result['status'] == 1:
                            _logger.warning('%s' % result.get('message', False))
                            tw_part_sales_obj = self.env['tw.part.sales'].browse(part_sales.id)
                            tw_part_sales_obj.write({
                                'status_api': 'done',
                                'is_error_ps': False
                            })
                            self.env['tw.api.log'].search([
                                ('model_name', '=', 'tw.part.sales'),
                                ('origin', '=', origin)
                            ], limit=1).unlink()

                except requests.exceptions.RequestException as exc:
                    _logger.warning('%s' % (exc))
                    log_name = 'Part Sales - Raise Warning'
                    cek_log = log_obj.search([
                        ('name', '=', log_name),
                        ('description', '=', str(exc)),
                        ('transaction_id', '=', part_sales.id),
                        ('api_type_id', '=', config_user.api_type_id.id),
                        ('model_id', '=', model_obj.id)], limit=1)
                    log_obj.sudo().create_api_log(
                            name=log_name,
                            url=url,
                            description=str(exc),
                            ip_address=False,
                            response=False,
                            payload=False,
                            header=False,
                            response_code=False,
                            status_code=False,
                            reference=False,
                            transaction_id=part_sales.id,
                            api_type_id=config_user.api_type_id.id,
                            method_id=False,
                            model_id=model_obj.id,
                        )
                    tw_part_sales_obj = self.env['tw.part.sales'].sudo().browse(part_sales.id)
                    tw_part_sales_obj.write({
                        'status_api': 'error',
                        'is_error_ps': True,
                        'api_last_try_date': str(datetime.now())
                    })

    def _get_tunas_id_sales(self,user_id):
        nip = False 
        emp = self.env['hr.employee'].sudo().search([('user_id','=',user_id)],limit=1)
        if emp:
            nip = emp.code_honda
        return nip   

    # TODO: Jalankan jika faktur pajak pada teto sudah bisa digunakan
    # def teds_generate_faktur_pajak_wo_current_month(self):
    #     message = []
    #     today = date.today()
    #     wo_ids = self.env['tw.part.sales'].sudo().search([
    #         ('state', 'in', ('sale','done')),
    #         ('faktur_pajak_id', '=', False),
    #         ('pajak_gabungan', '=', False),
    #         ('date', '>=', today.replace(day=1))
    #     ], limit=30)
        
    #     if not wo_ids:
    #         raise Warning('WO tanpa faktur pajak tidak ditemukan!')

    #     for wo in wo_ids:
    #         faktur = self.pool.get('wtc.faktur.pajak.out').get_no_faktur_pajak(self._cr, self._uid, wo.id, 'tw.part.sales')
    #         if faktur:
    #             message.append('Faktur pajak untuk WO %s berhasil!' % wo.name)
    #         else:
    #             message.append('Faktur pajak untuk WO %s gagal!' % wo.name)
        
    #     _logger.warning('\n\n%s' % '\n'.join(message))
    #     return '\n'.join(message)