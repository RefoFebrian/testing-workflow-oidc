from datetime import datetime
import pytz
from pytz import timezone
import time
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError, RedirectWarning

import logging
_logger = logging.getLogger(__name__)

# API
from json import dumps as json
import requests
from pprint import pprint as pp

class WorkOrder(models.Model):
    _inherit = "tw.work.order"

    def api_work_order_bundling(self):
        # NOTE: menggunakan pytz karena datetime.now() memberi nilai waktu UTC
        now = pytz.UTC.localize(datetime.now()).astimezone(timezone('Asia/Jakarta'))
        # NOTE: mencegah SerializationError a.k.a. scheduler bertabrakan maka waktu jalannya dibedakan
        if now.hour >= 19 or now.hour < 8:
            _logger.warning("Kirim WO Bundling ke DMS: Exiting cause its not the right time...")
            return

        # company_id diambil dari master partner bundling
        company_ids = self.env['tw.api.master.partner.bundling'].search([])
        company_ids_list = [b.company_id.id for b in company_ids]
        
        # WO Bundling hanya pakai servis [JASA BUNDLING 1] 
        # bundling_product_id = self.env['product.product'].search([('default_code', '=', 'JASA BUNDLING 1')]).id
        
        # customer_id diambil dari master partner bundling
        customer_ids = self.env['tw.api.master.partner.bundling.line'].search([])
        customer_ids_list = [
            cust.partner_id.id for cust in customer_ids if cust.partner_id
        ]
        if not customer_ids_list:
            _logger.error("API Work Order Bundling - Belum ada data partner bundling di configuration.")
            return

        # search WO cabang bundling yang
        #   state: open atau done, 
        #   tipe WO Claim,
        #   status API draft
        #   partner: bundling
        wo_bundling_query = """
            SELECT
                wo.*, 
                b.code AS wo_dealer_code 
            FROM tw_work_order wo
            JOIN res_company b ON wo.company_id = b.id
            LEFT JOIN tw_selection type ON type.id = wo.type_id
            WHERE wo.company_id IN %s
            AND wo.partner_id IN %s
            AND type.value = 'CLA'
            AND wo.state IN ('sale', 'done')
            AND wo.status_api = 'draft'
            LIMIT 1
        """ % (str(tuple(company_ids_list)).replace(",)", ")"), str(tuple(customer_ids_list)).replace(",)", ")"))
        self._cr.execute(wo_bundling_query)
        wo_bundling_id = self._cr.dictfetchone()

        # jika WO didapatkan
        if wo_bundling_id:
            # write to logger
            _logger.warning('Data found Work Order %s' %(wo_bundling_id.get('name')))
            # variabel untuk menampung message error
            message = False
            # search konfigurasi API cabang
            config_user = self.env['tw.api.configuration'].search([('company_id','=',wo_bundling_id.get('company_id'))])
            # jika konfigurasi tidak ada
            if not config_user:
                # write to logger
                message = 'Silahkan buat configuration terlebih dahulu.'
                _logger.warning('%s' %message) 
                # create log di teto
                log_obj = self.env['tw.api.log']
                cek_log =  log_obj.search([
                    ('name','=','data_not_found'),
                    ('description','=',message),
                    ('module_name','=','TW API WORK ORDER (BUNDLING)'),
                    ('model_name','=','tw.work.order'),
                    ('transaction_id','=',wo_bundling_id.get('id')),
                    ('origin','=',wo_bundling_id.get('name'))],limit=1)
                if not cek_log:
                    log_obj.sudo().create({
                        'name':'data_not_found',
                        'description':message,
                        'module_name':'TW API WORK ORDER (BUNDLING)',
                        'status':0,
                        'model_name':'tw.work.order',
                        'transaction_id':wo_bundling_id.get('id'),
                    })

            # cek kondisi bensin
            kondisi_bensin = int(wo_bundling_id.get('fuel') or 0)
            if kondisi_bensin == 0 or kondisi_bensin == 25:
                kondisi_bensin = 1
            elif kondisi_bensin == 50:
                kondisi_bensin = 2
            elif kondisi_bensin == 75:
                kondisi_bensin = 3
            elif kondisi_bensin == 100:
                kondisi_bensin = 4
            else: # kondisi bensin tidak dikenal
                # write to logger
                message = 'Bensin %s tidak dikenal' %(kondisi_bensin)
                _logger.warning('%s' %message)
                # create log di teto
                log_obj = self.env['tw.api.log']
                cek_log =  log_obj.search([
                    ('name','=','data_not_found'),
                    ('description','=',message),
                    ('module_name','=','TW API WORK ORDER (BUNDLING)'),
                    ('model_name','=','tw.work.order'),
                    ('transaction_id','=',wo_bundling_id.get('id')),
                    ('origin','=',wo_bundling_id.get('name'))],limit=1)
                if not cek_log:
                    log_obj.sudo().create({
                        'name':'data_not_found',
                        'description':message,
                        'module_name':'TW API WORK ORDER (BUNDLING)',
                        'status':0,
                        'model_name':'tw.work.order',
                        'transaction_id':wo_bundling_id.get('id'),
                        'origin':wo_bundling_id.get('name'),    
                    })

            # jika ada error
            if message:
                _logger.warning("Error kirim API: %s" %message)
                pass
                # TODO: Uncomment after development
                # # set status API WO: error
                # self.env['tw.work.order'].browse(wo_bundling_id.get('id')).write({'status_api': 'error'})
            else:
                try:
                    # connect to DMS
                    url = config_user.base_url + '/api/workshop/v1/create_service_order_bundling'
                    line = []
                    # search product specification
                    product_spec_query = """
                    SELECT pp.default_code AS product_code, pav.code AS color_code
                    FROM product_product pp
                    JOIN product_template pt ON pp.product_tmpl_id = pt.id
                    LEFT JOIN product_variant_combination pvc ON pvc.product_product_id = pp.id
                    LEFT JOIN product_template_attribute_value ptav ON ptav.id = pvc.product_template_attribute_value_id
                    LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
                    WHERE pp.id = %s
                    """ % (wo_bundling_id.get('product_id'))
                    self._cr.execute(product_spec_query)
                    product_spec = self._cr.dictfetchone()
                    # search lot and then create array to store the data
                    lot_id = self.env['stock.lot'].suspend_security().browse(wo_bundling_id.get('lot_id'))
                    product_code = product_spec.get('product_code') if product_spec else False
                    if isinstance(product_code, dict):
                        product_code = product_code.get(self.env.context.get('lang') or 'en_US') or (list(product_code.values())[0] if product_code.values() else False)
                    color_code = product_spec.get('color_code') if product_spec else False
                    lot = {
                    'name': lot_id.name or False,
                    'chassis_no': lot_id.chassis_number or False,
                    'tahun_pembuatan': lot_id.production_year or False,
                    'product_code': product_code,
                    'color_code': color_code,
                    'hpp': lot_id.cogs or 0.0
                    }
                    # search customer
                    customer_id = self.env['res.partner'].suspend_security().browse(wo_bundling_id.get('partner_id'))
                    customer = {
                    'name': customer_id.name or False,
                    'branch_id': wo_bundling_id.get('company_id'),
                    'street': customer_id.street or False,
                    'rt': customer_id.rt or False,
                    'rw': customer_id.rw or False,
                    'state_code': customer_id.state_id.code if customer_id.state_id else False,
                    'kabupaten_code': customer_id.city_id.code if customer_id.city_id else False,
                    'kecamatan_code': customer_id.district_id.code if customer_id.district_id else False,
                    'kecamatan_name': customer_id.district_id.name if customer_id.district_id else False,
                    'zip_code': customer_id.sub_district_id.zip_code if customer_id.sub_district_id else False,
                    'kelurahan_name': customer_id.sub_district_id.name if customer_id.sub_district_id else False,
                    'contact': wo_bundling_id.get('mobile')
                    }
                    # search order line dari WO
                    wol_query = """ 
                    SELECT 
                    wol.division AS category,
                    pp.default_code AS product_code,
                    st.name AS location_name,
                    SUM(CASE WHEN wol.division = 'Sparepart' THEN wol.qty_delivered ELSE 0 END) AS supply_qty_part,
                    SUM(CASE WHEN wol.division = 'Service' THEN wol.product_uom_qty ELSE 0 END) AS supply_qty_service,
                    wol.discount AS discount,
                    wol.price_unit AS price
                    FROM tw_work_order_line wol 
                    LEFT JOIN product_product AS pp ON wol.product_id = pp.id
                    LEFT JOIN stock_location st ON wol.location_id = st.id
                    WHERE order_id = %s 
                    GROUP BY wol.division, pp.default_code, st.name, wol.discount, wol.price_unit 
                    """%(wo_bundling_id.get('id'))
                    self._cr.execute(wol_query)
                    ress = self._cr.dictfetchall()
                    supply_qty = 0
                    for res in ress:
                        if res.get('category', False) == 'Service':
                            supply_qty = res.get('supply_qty_service', False)
                        else:
                            supply_qty = res.get('supply_qty_part', False)
                        line.append({
                            'category': res.get('category', False),
                            'product_code': res.get('product_code', False),
                            'qty': supply_qty,
                            'qty_spl': supply_qty,
                            'diskon': res.get('discount', False),
                            'price': res.get('price', False),
                        })
                    alasan_ke_ahass = self.env["tw.work.order"].browse(wo_bundling_id.get('id')).reason_to_ahass_id.value
                    date_val = wo_bundling_id.get('date')
                    date_str = date_val.strftime('%Y-%m-%d') if date_val and hasattr(date_val, 'strftime') else ''

                    start_val = wo_bundling_id.get('start_date')
                    start_str = start_val.strftime('%Y-%m-%d %H:%M:%S') if start_val and hasattr(start_val, 'strftime') else ''

                    finish_val = wo_bundling_id.get('finish_date')
                    finish_str = finish_val.strftime('%Y-%m-%d %H:%M:%S') if finish_val and hasattr(finish_val, 'strftime') else ''

                    service_type = wo_bundling_id.get('type_id')
                    service_type_value = self.env['tw.selection'].browse(service_type).value

                    payload = {
                        'stock_dealer_code': 'MML',
                        'wo_dealer_code': wo_bundling_id.get('wo_dealer_code'),
                        'service_type': service_type_value,
                        'date': date_str,
                        'km': wo_bundling_id.get('km'),
                        'kondisi_bensin': kondisi_bensin,
                        'alasan_ke_ahass': alasan_ke_ahass,
                        'kebutuhan_konsumen': wo_bundling_id.get('kebutuhan_konsumen','Tidak Ada Kebutuhan'),
                        'mekanik_id_tunas': self._get_tunas_id_sales(wo_bundling_id.get('mechanic_id')),
                        'mekanik_id_name': self.env['hr.employee'].suspend_security().browse(wo_bundling_id.get('mechanic_id')).user_id.name if wo_bundling_id.get('mechanic_id') else False,
                        'start': start_str,
                        'finish': finish_str,
                        'wo_line_ids': line,
                        'lot': lot,
                        'customer': customer
                    }
                    headers = {
                        'Content-Type': 'application/json',
                        'access_token': config_user.token
                    }
                    response = requests.post(url, data=json(payload), headers=headers)
                    result = response.json().get('result', False)
                    
                    if result:
                        # 0 ?
                        if result.get('status') == 0:
                            # write to logger
                            _logger.warning('%s' % result.get('message', False))
                            # create log di tw.api.log
                            log_obj = self.env['tw.api.log']
                            cek_log = log_obj.search([
                                ('name', '=', result.get('error', False)),
                                ('description', '=', result.get('remark', False)),
                                ('module_name', '=', 'DMS API SERVICE ORDER (BUNDLING)'),
                                ('model_name', '=', 'tw.work.order'),
                                ('transaction_id', '=', wo_bundling_id.get('id')),
                                ('origin', '=', wo_bundling_id.get('name'))
                            ], limit=1)
                            if not cek_log:
                                log_obj.sudo().create({
                                     'name': result.get('error', False),
                                     'description': result.get('remark', False),
                                     'module_name': 'DMS API SERVICE ORDER (BUNDLING)',
                                     'status': result.get('status', False),
                                     'model_name': 'tw.work.order',
                                     'transaction_id': wo_bundling_id.get('id'),
                                     'origin': wo_bundling_id.get('name')
                                })
                            # set status API WO: error
                            self.env['tw.work.order'].browse(wo_bundling_id.get('id')).write({'status_api': 'error'})
                        # 1 ?
                        elif result.get('status') == 1:
                            # write to logger
                            _logger.warning('%s' %result.get('message',False))
                             # set status API WO: done
                            self.env['tw.work.order'].browse(wo_bundling_id.get('id')).write({'status_api': 'done'})

                except requests.exceptions.RequestException as exc:  # cannot connect
                    # write to logger
                    _logger.warning('%s' %(exc))
                    # create log di teto
                    log_obj = self.env['tw.api.log']
                    cek_log =  log_obj.search([
                        ('name','=','raise_warning'),
                        ('description','=',exc),
                        ('module_name','=','DMS API SERVICE ORDER (BUNDLING)'),
                        ('model_name','=','tw.work.order'),
                        ('transaction_id','=',wo_bundling_id.get('id')),
                        ('origin','=',wo_bundling_id.get('name'))],limit=1)
                    if not cek_log:
                        log_obj.sudo().create({
                            'name':'raise_warning',
                            'description':exc,
                            'module_name':'DMS API SERVICE ORDER (BUNDLING)',
                            'status':0,
                            'model_name':'tw.work.order',
                            'transaction_id':wo_bundling_id.get('id'),
                            'origin':wo_bundling_id.get('name'),
                        })
                    # set status API WO: error
                    self.env['tw.work.order'].browse(wo_bundling_id.get('id')).write({'status_api': 'error'})
    # UPDATE WO ERROR DI 1 METHOD SAJA
