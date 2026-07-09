import base64
import calendar
import logging
import json
import pandas as pd
import requests
import xlsxwriter

from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from io import BytesIO

from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning
from odoo.tools import SQL

_logger = logging.getLogger(__name__)


class DownloadProfitBeforeTax(models.TransientModel):
    _name = "tw.download.profit.before.tax"
    _rec_name = "file"
    _description = "Download Profit Before Tax"
    
    @api.model
    def _get_first_date_of_the_month(self):
        return date.today().replace(day=1)

    @api.model
    def _get_last_date_of_the_month(self):
        now = date.today()
        month = now.month
        year = now.year
        last_date = calendar.monthrange(year, month)[1]
        return date(year, month, last_date)

    def _get_default_branch(self):
        return self.env.user.company_ids.ids if self.env.user.company_ids else False
    
    file = fields.Char('File Name')
    data_x = fields.Binary('File', readonly=True)
    state_x = fields.Selection([('choose','choose'),('get','get')], default='choose')
    company_id = fields.Many2one('res.company', "Branch", default=_get_default_branch, domain=[('parent_id', '!=', False)])
    start_date = fields.Date('Start Date', default=_get_first_date_of_the_month)
    end_date = fields.Date('End Date', default=_get_last_date_of_the_month)

    wbf = {}

    def return_error(self, arg=None, detail=None, url=None, method=None, headers=None, data=None, content=None, status_code=None):
        error = 'Unspecified error.'
        if arg == 'no_config':
            error = 'Belum ada konfigurasi image. Silahkan buat atau ubah export_locally = False'
        elif arg == 'no_path':
            error = 'Folder Path Local konfigurasi image kosong.'
        elif arg == 'no_api_config':
            error = f'ERROR {detail}: Silakan buat API Configuration terlebih dahulu!'
        elif arg == '_generate_unit_sales_data':
            error = str(detail)
            self.env['tw.api.log'].sudo().create({
                'name': f'Input Net Margin - {arg}',
                'status': 'FAILED',
                'api_type': 'teds',
                'model_name': self._name,
                'description': detail,
                'end_point': url,
                'method': method,
                'header': headers,
                'request': data,
                'response': content,
                'htttp_response_code': status_code
            })
        _logger.error(error)
        return (False, error)
    
    def _get_pricelist_version(self, product_pricelist):
        today = date.today()
        version_id = product_pricelist.version_ids.filtered(lambda x: 
            x.state == 'confirmed'
            and x.date_end >= today
            and x.date_start <= today
        )
        if not version_id:
            raise Warning(_(f"Pricelist {product_pricelist.name} for {product_pricelist.type} unit is not configured or not active for the current date range.\n" +
                            "Please check the configuration."))
            
        if len(version_id) > 1:
            singletons = '\n'.join([f'- {pl.name}' for pl in version_id])
            raise Warning(_(f"Multiple active pricelist versions found for {product_pricelist.type} unit.\n" + 
                            "Please ensure only one active version exists for the current date range.\n" +
                            singletons))
            
        return version_id

    def _generate_unit_sales_data(self, start_date, end_date):
        branch = self.company_id
        if not branch.city_id:
            raise Warning(_("City of selected branch must not be empty!"))
        
        branch_conf = self.company_id.branch_setting_id
        select = []
        join = []
        where = ''
        
        def get_pl_info(pricelist_record):
            version = self._get_pricelist_version(pricelist_record)
            base_item = version.item_ids.filtered(lambda x: x.base == 'pricelist' and x.base_pricelist_id)
            if base_item:
                base_version = self._get_pricelist_version(base_item[0].base_pricelist_id)
                return {
                    'version_id': base_version.id,
                    'discount': base_item[0].percent_price or base_item[0].price_discount,
                    'surcharge': base_item[0].price_surcharge
                }
            return {
                'version_id': version.id,
                'discount': 0.0,
                'surcharge': 0.0
            }

        pricelist_sale_unit_id = branch_conf.pricelist_sale_unit_id
        if not pricelist_sale_unit_id:
            raise Warning(_("Pricelist sale unit must be configured!"))
        pl_sale_info = get_pl_info(pricelist_sale_unit_id)

        version_expedition = False
        if branch.state_id.code == '1800':
            main_dealer_partner = branch.default_supplier_id
            main_dealer = self.env['res.company'].sudo().search([('partner_id', '=', main_dealer_partner.id)], limit=1)
            if not main_dealer:
                raise Warning(_("Main Dealer not found!"))

            main_dealer_conf = main_dealer.branch_setting_id
            if not main_dealer_conf.pricelist_purchase_unit_id:
                raise Warning(_("Pricelist purchase unit must be configured!"))

            pl_purchase_info = get_pl_info(main_dealer_conf.pricelist_purchase_unit_id)

            if not main_dealer_conf.expedition_id:
                raise Warning(_("Default Expedition is not set for branch %s" %main_dealer.code))
            pricelist_expedition = main_dealer_conf.expedition_id.with_company(main_dealer).property_product_pricelist
            if not pricelist_expedition:
                raise Warning(_("Pricelist expedition must be configured in %s!" %main_dealer_conf.expedition_id.code))

            version_expedition = self._get_pricelist_version(pricelist_expedition)
            if not version_expedition:
                raise Warning(_("Pricelist expedition %s dont have active pricelist version!" %pricelist_expedition.name))
            
            select.append(SQL("""
                AVG(
                    CASE
                    WHEN (COALESCE(plsale.fixed_price, 0) > 1 OR %s != 0)
                         AND (COALESCE(plpurchase.fixed_price, 0) > 1 OR %s != 0) 
                    THEN (
                        (
                            (COALESCE(plsale.fixed_price, 0) * (1 - %s / 100.0) + %s)
                            - (COALESCE(plpurchase.fixed_price, 0) * (1 - %s / 100.0) + %s)
                        ) / (1 + (COALESCE(at.amount, 0) / 100)) + COALESCE(expedisi.fixed_price, 0)
                    )
                    END
                ) AS gp_unit,""",
                pl_sale_info['discount'],
                pl_purchase_info['discount'],
                pl_sale_info['discount'],
                pl_sale_info['surcharge'],
                pl_purchase_info['discount'],
                pl_purchase_info['surcharge']
            ))
            join.append(SQL("""LEFT JOIN LATERAL(
                    SELECT pt.id as product_template_id,COALESCE(COALESCE(COALESCE(piex_prod.fixed_price,piex_categ.fixed_price),piex_all.fixed_price),0) as fixed_price
                    FROM tw_product_pricelist_version pvex
                    LEFT JOIN product_pricelist_item AS piex_prod ON piex_prod.product_tmpl_id = pt.id
                    LEFT JOIN product_pricelist_item AS piex_categ ON piex_prod.categ_id = pt.categ_id
                    LEFT JOIN product_pricelist_item AS piex_all ON piex_prod.categ_id is null and piex_prod.applied_on in ('3_global','2_product_category')
                    WHERE pvex.id = %s
                ) expedisi ON expedisi.product_template_id = pt.id
                """, version_expedition.id))
        else:
            pl_purchase_info = get_pl_info(branch_conf.pricelist_purchase_unit_id)
            select.append(SQL("""
                AVG(
                    CASE
                    WHEN (COALESCE(plsale.fixed_price, 0) > 1 OR %s != 0)
                         AND (COALESCE(plpurchase.fixed_price, 0) > 1 OR %s != 0) 
                    THEN (
                        (COALESCE(plsale.fixed_price, 0) * (1 - %s / 100.0) + %s)
                        - (COALESCE(plpurchase.fixed_price, 0) * (1 - %s / 100.0) + %s)
                    ) / (1 + (COALESCE(at.amount, 0) / 100))
                    END
                ) AS gp_unit,""",
                pl_sale_info['discount'],
                pl_purchase_info['discount'],
                pl_sale_info['discount'],
                pl_sale_info['surcharge'],
                pl_purchase_info['discount'],
                pl_purchase_info['surcharge']
            ))

        pricelist_sale_bbn = branch_conf.pricelist_sale_bbn_hitam_id or branch_conf.pricelist_sale_bbn_putih_id
        if not pricelist_sale_bbn:
            raise Warning(_("Pricelist sale bbn on branch %s must be configured!"%self.company_id.name))
        pl_sale_bbn_info = get_pl_info(pricelist_sale_bbn)

        default_biro_jasa = branch_conf.birojasa_setting_ids.filtered(lambda x: x.default)
        default_pl_purchase_bbn = default_biro_jasa.pricelist_ids.filtered(lambda x: x.active)
        if not default_pl_purchase_bbn:
            raise Warning(_("Pricelist purchase bbn on branch %s must be configured!"%self.company_id.name))
        pl_purchase_bbn_info = get_pl_info(default_pl_purchase_bbn)

        query = SQL("""
            WITH dsol_disc AS (
                SELECT order_line_id,
                    SUM(amount_finco) AS ps_finco,
                    SUM(amount_ahm) AS ps_ahm,
                    SUM(amount_md) AS ps_md,
                    SUM(amount_dealer) AS ps_dealer,
                    SUM(amount_others) AS ps_others,
                    SUM(amount_diff_md) AS ps_md_diff,
                    SUM(amount_diff_finco) AS ps_finco_diff,
                    SUM(discount_amount) AS discount,
                    SUM(discount_customer) AS discount_pelanggan
                FROM tw_dealer_sale_order_line_program
                GROUP BY order_line_id
            ), 
            dsol_voucher AS (
                SELECT order_line_id,
                    SUM(amount) AS diskon_voucher
                FROM tw_dealer_sale_order_line_voucher
                GROUP BY order_line_id
            ),
            dsol_bb AS (
                SELECT order_line_id,
                    SUM(direct_gift_dealer) AS price_barang
                FROM tw_dealer_sale_order_line_direct_gift
                GROUP BY order_line_id
            ), plprice AS (
                SELECT pt.id AS product_tmpl_id
                    , plbbn_purchase.city_id AS city_id
                    , AVG(
                        (
                            (COALESCE(plsale.fixed_price, 0) * (1 - %(pl_sale_discount)s / 100.0) + %(pl_sale_surcharge)s)
                            / (1 + (COALESCE(at.amount, 0) / 100))
                        )
                        - (COALESCE(plpurchase.fixed_price, 0) * (1 - %(pl_purchase_discount)s / 100.0) + %(pl_purchase_surcharge)s)
                    ) AS gp_unit
                    , AVG(
                        (COALESCE(plbbn_sale.fixed_price, 0) * (1 - %(pl_sale_bbn_discount)s / 100.0) + %(pl_sale_bbn_surcharge)s)
                        - (COALESCE(plbbn_purchase.fixed_price, 0) * (1 - %(pl_purchase_bbn_discount)s / 100.0) + %(pl_purchase_bbn_surcharge)s)
                    ) AS gp_bbn
                from product_template pt
                left join product_taxes_rel ptr ON ptr.prod_id = pt.id
                left join account_tax at ON at.id = ptr.tax_id 
                LEFT JOIN product_pricelist_item AS plsale ON plsale.product_tmpl_id = pt.id AND plsale.pricelist_version_id = %(pl_sale)s
                LEFT JOIN product_pricelist_item AS plpurchase ON plpurchase.product_tmpl_id = pt.id AND plpurchase.pricelist_version_id = %(pl_purchase)s
                LEFT JOIN product_pricelist_item AS plbbn_sale ON plbbn_sale.product_tmpl_id = pt.id AND plbbn_sale.pricelist_version_id = %(pl_sale_bbn)s
                LEFT JOIN product_pricelist_item AS plbbn_purchase ON plbbn_purchase.product_tmpl_id = pt.id AND plbbn_purchase.pricelist_version_id = %(pl_purchase_bbn)s
                LEFT JOIN product_series prod_series ON pt.series_id = prod_series.id
                GROUP BY pt.id, plbbn_purchase.city_id
            )
            SELECT COALESCE(prod_series.name->>'en_US', '') AS series_name,
                COALESCE(lot.production_year, TO_CHAR(CURRENT_DATE, 'YYYY')) AS year,
                SUM(COALESCE(dsol.product_uom_qty, 0)) AS product_qty,
                -- TODO: activate these if commission and extra reward are developed
                -- AVG(COALESCE(dsol.amount_hutang_komisi, 0)) AS amount_hutang_komisi,
                -- AVG(COALESCE(dsol.amount_extra_reward, 0)) AS extra_reward,
                0 AS amount_hutang_komisi,
                0 AS extra_reward,
                AVG(COALESCE(dsol_bb.price_barang, 0)) AS barang_bonus,
                AVG(
                    COALESCE(dsol.bbn_amount) - (COALESCE(dsol.bbn_notice_amount, 0) + COALESCE(dsol.bbn_process_amount, 0) + COALESCE(dsol.bbn_serv_amount, 0))
                        - ((COALESCE(dsol.bbn_amount, 0) - COALESCE(dsol.bbn_notice_amount, 0) - COALESCE(dsol.bbn_process_amount, 0)) / ((COALESCE(at.amount, 0) / 100) + 1) * (COALESCE(at.amount, 0) / 100))
                        - COALESCE(dsol.accrue_bbn_process, 0)
                ) AS report_gp_bbn,
                AVG(
                    COALESCE(dsol.price_subtotal, 0) - COALESCE(dsol.price_unit_purchase, 0) + COALESCE(dsol_disc.ps_ahm, 0) + COALESCE(dsol_disc.ps_md, 0) + COALESCE(dsol_disc.ps_finco, 0)
                ) AS report_gp_unit,
                AVG(CASE WHEN sales_force.value IN ('salesman', 'sales_partner') THEN dsol.net_margin END) AS salesman_margin,
                AVG(CASE WHEN sales_force.value = 'sales_counter' THEN dsol.net_margin END) AS sales_counter_margin,
                AVG(CASE WHEN sales_force.value = 'sales_coordinator' THEN dsol.net_margin END) AS sco_margin,
                AVG(dsol.net_margin) AS sisa_margin_all,
                SUM(CASE WHEN dso.finco_id IS NULL THEN 1 ELSE 0 END) AS ttl_sales_lm_cash,
                SUM(CASE WHEN dso.finco_id IS NOT NULL THEN 1 ELSE 0 END) AS ttl_sales_lm_credit,
                SUM(plprice.gp_unit) AS gp_unit,
                SUM(plprice.gp_bbn) AS gp_bbn
            FROM tw_dealer_sale_order dso
                LEFT JOIN tw_dealer_sale_order_line dsol ON dsol.order_id = dso.id and dsol.item_type = 'main'
                LEFT JOIN account_tax_tw_dealer_sale_order_line_rel dsot ON dsot.tw_dealer_sale_order_line_id = dsol.id
                LEFT JOIN account_tax at ON at.id = dsot.account_tax_id
                LEFT JOIN dsol_disc ON dsol_disc.order_line_id = dsol.id
                LEFT JOIN stock_lot lot ON lot.id = dsol.lot_id
                LEFT JOIN res_company branch ON dso.company_id = branch.id
                LEFT JOIN hr_employee hr_sales ON dso.sales_id = hr_sales.id
                LEFT JOIN hr_job job ON hr_sales.job_id = job.id
                LEFT JOIN tw_selection sales_force ON sales_force.id = job.sales_force_id
                LEFT JOIN res_partner finco ON dso.finco_id = finco.id
                LEFT JOIN res_partner customer_stnk ON dsol.partner_stnk_id = customer_stnk.id
                LEFT JOIN product_product product ON dsol.product_id = product.id
                LEFT JOIN product_template prod_template ON product.product_tmpl_id = prod_template.id
                LEFT JOIN product_series prod_series ON prod_template.series_id = prod_series.id
                LEFT JOIN dsol_bb ON dsol_bb.order_line_id = dsol.id
                LEFT JOIN plprice ON plprice.product_tmpl_id = prod_template.id AND plprice.city_id = customer_stnk.city_id
                -- TODO: activate this if dealer sale order voucher is developed
                -- LEFT JOIN dsol_voucher ON dsol_voucher.order_line_id = dsol.id
            WHERE 1 = 1
                AND dso.company_id = %(company_id)s
                AND dso.date_order BETWEEN %(start_date)s AND %(end_date)s
                AND dso.state IN ('sale', 'done')
                AND dsol.item_type = 'main'
            GROUP BY series_name, year
        """, 
            company_id=branch.id,
            start_date=start_date,
            end_date=end_date,
            pl_sale=pl_sale_info['version_id'],
            pl_sale_discount=pl_sale_info['discount'],
            pl_sale_surcharge=pl_sale_info['surcharge'],
            pl_purchase=pl_purchase_info['version_id'],
            pl_purchase_discount=pl_purchase_info['discount'],
            pl_purchase_surcharge=pl_purchase_info['surcharge'],
            pl_sale_bbn=pl_sale_bbn_info['version_id'],
            pl_sale_bbn_discount=pl_sale_bbn_info['discount'],
            pl_sale_bbn_surcharge=pl_sale_bbn_info['surcharge'],
            pl_purchase_bbn=pl_purchase_bbn_info['version_id'],
            pl_purchase_bbn_discount=pl_purchase_bbn_info['discount'],
            pl_purchase_bbn_surcharge=pl_purchase_bbn_info['surcharge']
        )
        
        self.env.cr.execute(query)
        orders = self.env.cr.dictfetchall()

        segments = self.env['product.category'].search([('name', '=', 'Unit')])
        categories = self.env['product.category'].search([('id', 'child_of', segments.ids)])
        
        select_sql = SQL("").join(select)
        join_sql = SQL("").join(join)
        
        query = SQL("""
            SELECT ps.name->>'en_US' AS series_name,
                %(select)s
                AVG(
                    CASE
                    WHEN COALESCE(plbbn_sale.fixed_price, 0) > 1 AND COALESCE(plbbn_purchase.fixed_price, 0) > 1
                    THEN (COALESCE(plbbn_sale.fixed_price, 0) * (1 - %(pl_sale_bbn_discount)s / 100.0) + %(pl_sale_bbn_surcharge)s) 
                         - (COALESCE(plbbn_purchase.fixed_price, 0) * (1 - %(pl_purchase_bbn_discount)s / 100.0) + %(pl_purchase_bbn_surcharge)s)
                    END
                ) AS gp_bbn
            FROM product_template pt
                LEFT JOIN product_series ps ON ps.id = pt.series_id
                LEFT JOIN product_taxes_rel ptr ON ptr.prod_id = pt.id
                LEFT JOIN account_tax at ON at.id = ptr.tax_id
                LEFT JOIN product_pricelist_item AS plsale ON plsale.product_tmpl_id = pt.id AND plsale.pricelist_version_id = %(pl_sale)s
                LEFT JOIN product_pricelist_item AS plpurchase ON plpurchase.product_tmpl_id = pt.id AND plpurchase.pricelist_version_id = %(pl_purchase)s
                LEFT JOIN product_pricelist_item AS plbbn_sale ON plbbn_sale.product_tmpl_id = pt.id AND plbbn_sale.pricelist_version_id = %(pl_sale_bbn)s
                LEFT JOIN product_pricelist_item AS plbbn_purchase ON plbbn_purchase.product_tmpl_id = pt.id AND plbbn_purchase.pricelist_version_id = %(pl_purchase_bbn)s AND plbbn_purchase.city_id = %(city_id)s
                %(join)s
            WHERE plsale.id IS NOT NULL AND plpurchase.id IS NOT NULL
            GROUP BY ps.id
        """, select=select_sql, city_id=branch.city_id.id, join=join_sql,
            version_expedition=version_expedition.id if version_expedition else False,
            pl_sale=pl_sale_info['version_id'],
            pl_sale_discount=pl_sale_info['discount'],
            pl_sale_surcharge=pl_sale_info['surcharge'],
            pl_purchase=pl_purchase_info['version_id'],
            pl_purchase_discount=pl_purchase_info['discount'],
            pl_purchase_surcharge=pl_purchase_info['surcharge'],
            pl_sale_bbn=pl_sale_bbn_info['version_id'],
            pl_sale_bbn_discount=pl_sale_bbn_info['discount'],
            pl_sale_bbn_surcharge=pl_sale_bbn_info['surcharge'],
            pl_purchase_bbn=pl_purchase_bbn_info['version_id'],
            pl_purchase_bbn_discount=pl_purchase_bbn_info['discount'],
            pl_purchase_bbn_surcharge=pl_purchase_bbn_info['surcharge'])
        
        self.env.cr.execute(query)
        master = self.env.cr.dictfetchall()

        return {'orders': orders, 'master': master}
    
    def excel_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        return self._download_report()

    def _download_report(self):
        # hit endpoint TEDS to get penjualan data
        res_margin = self.env['tw.profit.before.tax']
        start_date = self.start_date - relativedelta(months=1) 
        mon = calendar.monthrange(start_date.year, start_date.month)
        folmonth = start_date.replace(day=1)
        lomonth = start_date.replace(day=mon[1])

        results = self._generate_unit_sales_data(folmonth, lomonth)
        if 'orders' in results and not results.get('orders'):
            raise Warning(f"No data sales found for period between {folmonth} and {lomonth}")
        if 'master' in results and not results.get('master'):
            raise Warning(f"No data master found for period between {folmonth} and {lomonth}")
        
        # convert response result into dataframe
        orders = pd.DataFrame(results.get('orders'))
        master = pd.DataFrame(results.get('master'))
        if orders.empty:
            raise Warning("Tidak Ada Data Penjualan Unit!")
        if master.empty:
            raise Warning("Tidak Ada Data Master Unit!")

        # combine previous dataframe with sales order df
        # remove unused field, and replace NaN value with 0
        combined = master.merge(orders, on='series_name', how='left')
        combined['gp_unit'] = combined['gp_unit_x']
        combined['gp_bbn'] = combined['gp_bbn_y'].fillna(combined['gp_bbn_x'])
        combined.fillna(0, inplace=True)
        combined.drop(['gp_unit_x', 'gp_unit_y', 'gp_bbn_x', 'gp_bbn_y'], axis=1, inplace=True)

        prev_res_margin = res_margin.search([('start_date', '=', self.start_date),
                                             ('end_date', '=', self.end_date),
                                             ('company_id', '=', self.company_id.id)],
                                             limit=1, order='id DESC')
        if prev_res_margin:
            prev_res_margin = prev_res_margin.profit_before_tax_line_ids.read([
                'series_id', 'year', 'state',
                'unit_cash_salesman', 'unit_cash_scounter', 'unit_cash_sco',
                'unit_credit_salesman', 'unit_credit_scounter', 'unit_credit_sco',
                'discount_cash_salesman', 'discount_cash_counter', 'discount_cash_sco',
                'discount_credit_salesman', 'discount_credit_counter', 'discount_credit_sco'
            ])
            
            for rm in prev_res_margin:
                rm['series_name'] = rm['series_id'][1]

            prm = pd.DataFrame(prev_res_margin)
            combined = combined.merge(prm, left_on=['series_name', 'year'], right_on=['series_name', 'year'])
            
        # proses dokumen excel
        records = combined.to_dict('records')
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)       
        workbook = self.add_workbook_format(workbook)
        wbf = self.wbf
        worksheet = workbook.add_worksheet('Menu Input Net Margin')

        worksheet.set_column('A1:A1', 5)
        worksheet.set_column('B1:B1', 25)
        worksheet.set_column('C1:C1', 20)
        worksheet.set_column('D1:D1', 25)
        worksheet.set_column('E1:E1', 25)

        worksheet.set_column('F1:F1', 25)
        worksheet.set_column('G1:G1', 25)

        # worksheet.set_column('G1:G1', 20)
        worksheet.set_column('H1:H1', 20)
        worksheet.set_column('I1:I1', 20)

        worksheet.set_column('J1:J1', 20)
        worksheet.set_column('K1:K1', 20)

        worksheet.set_column('L1:L1', 20)
        worksheet.set_column('M1:M1', 20)

        worksheet.set_column('N1:N1', 20)
        worksheet.set_column('O1:O1', 20)

        worksheet.set_column('P1:P1', 20)
        worksheet.set_column('Q1:Q1', 10)
        
        worksheet.set_column('R1:R1', 10)
        worksheet.set_column('S1:S1', 10)
        worksheet.set_column('T1:T1', 13)
        worksheet.set_column('U1:U1', 10)
        worksheet.set_column('V1:V1', 10)

        worksheet.set_column('W1:W1', 10)
        worksheet.set_column('X1:X1', 10)
        worksheet.set_column('Y1:Y1', 13)
        worksheet.set_column('Z1:Z1', 10)
        worksheet.set_column('AA1:AA1', 10)

        worksheet.set_column('AB1:AB1', 10)
        worksheet.set_column('AC1:AC1', 10)
        worksheet.set_column('AD1:AD1', 13)
        worksheet.set_column('AE1:AE1', 10)
        worksheet.set_column('AF1:AF1', 20)

        worksheet.set_column('AG1:AG1', 10)
        worksheet.set_column('AH1:AH1', 10)
        worksheet.set_column('AI1:AI1', 13)
        worksheet.set_column('AJ1:AJ1', 10)
        worksheet.set_column('AK1:AK1', 20)

        worksheet.set_column('AL1:AL1', 10)
        worksheet.set_column('AM1:AM1', 10)
        worksheet.set_column('AN1:AN1', 10)
        worksheet.set_column('AO1:AO1', 10)

        worksheet.set_column('AP1:AP1', 10)
        worksheet.set_column('AQ1:AQ1', 10)
        worksheet.set_column('AR1:AR1', 10)

        worksheet.set_column('AS1:AS1', 10)
        worksheet.set_column('AT1:AT1', 10)
        worksheet.set_column('AU1:AU1', 10)

        worksheet.set_column('AV1:AV1', 10)
        worksheet.set_column('AW1:AW1', 10)
        worksheet.set_column('AX1:AX1', 10)

        worksheet.set_column('AY1:AY1', 10)
        worksheet.set_column('AZ1:AZ1', 10)
        worksheet.set_column('BA1:BA1', 10)

        worksheet.set_column('BB1:BB1', 10)
        worksheet.set_column('BC1:BC1', 10)
        worksheet.set_column('BD1:BD1', 10)

        worksheet.set_column('BE1:BE1', 20)

        worksheet.protect()
        
        filename = f'Input Net Margin {self.company_id.code} {self.start_date.strftime("%B %Y")}.xlsx'
        
        branch = self.company_id.code
        periode = f'{self.start_date.strftime("%d %b %Y")} - {self.end_date.strftime("%d %b %Y")}'
        area_manager = self.company_id.branch_setting_id.sudo().area_manager_id.name
        
        master_periode = self.env['tw.period.profit.before.tax'].suspend_security().search([
            ('start_date', '=', self.start_date),
            ('end_date', '=', self.end_date),
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        if not master_periode:
            raise Warning(f'Master periode {self.start_date} - {self.end_date} for branch {branch} is not available!')

        worksheet.write('B1', 'KODE CABANG', wbf['company'])
        worksheet.write('B2', 'PERIODE', wbf['company'])
        worksheet.write('B3', 'OPEX AVG', wbf['company'])
        worksheet.write('B4', 'TRANSFER MARGIN', wbf['company'])
        worksheet.write('C1', branch, wbf['top_header_light_yellow'])
        worksheet.write('C2', periode, wbf['top_header_light_yellow'])
        worksheet.write('C3', master_periode.opex_avg or 0, wbf['top_header_light_yellow_float'])
        if self.company_id.state_id.code == '1800':
            worksheet.write('C4', '=1500000*C7', wbf['top_header_light_yellow_float'])
        else:
            worksheet.write('C4', '0', wbf['top_header_light_yellow_float'])
        
        worksheet.write('C6', 'M' , wbf['company_header'])
        worksheet.write('D6', 'LM' , wbf['company_header'])

        worksheet.write('B7', 'TOTAL UNIT' , wbf['company'])
        worksheet.write('B8', 'TOTAL CASH' , wbf['company'])
        worksheet.write('B9', 'TOTAL CREDIT' , wbf['company'])
        worksheet.write('B10', 'TOTAL SISA MARGIN' , wbf['company'])
        worksheet.write('B11', 'TOTAL REFUND' , wbf['company'])
        worksheet.write('B12', 'PBT PROPOSE' , wbf['company'])
        
        worksheet.write('D7', master_periode.total_unit_lm , wbf['last_month_agg'])        
        worksheet.write('D10', master_periode.total_net_margin_lm , wbf['last_month_agg'])
        worksheet.write('D11', master_periode.refund_lm , wbf['last_month_agg'])
        worksheet.write('D12', master_periode.pbt_propose_lm , wbf['last_month_agg'])
        
        row = 13

        worksheet.set_row(row+1, 50)
        worksheet.merge_range(f'B{row+1}:B{row+2}', 'SERIES' , wbf['header_blue'])
        worksheet.merge_range(f'C{row+1}:C{row+2}', 'TAHUN' , wbf['header_blue'])
        worksheet.merge_range(f'D{row+1}:E{row+1}', 'CEK ALL JABATAN' , wbf['header'])
        worksheet.write(f'D{row+2}', 'SISA MARGIN/unit pengajuan (exc Refund)' , wbf['header'])
        worksheet.write(f'E{row+2}', 'SISA MARGIN/unit Actual (LM) (exc Refund)' , wbf['header'])
        worksheet.merge_range(f'F{row+1}:G{row+1}', 'CEK SALESMAN (PARTNER, PAYROLL, SC PARTNER)' , wbf['header'])
        worksheet.write(f'F{row+2}', 'SISA MARGIN/unit pengajuan (exc Refund)' , wbf['header'])
        worksheet.write(f'G{row+2}', 'SISA MARGIN/unit Actual (LM) (exc Refund)' , wbf['header'])
        worksheet.merge_range(f'H{row+1}:I{row+1}', 'CEK SALES COUNTER' , wbf['header'])
        worksheet.write(f'H{row+2}', 'SISA MARGIN/unit pengajuan (exc Refund)' , wbf['header'])
        worksheet.write(f'I{row+2}', 'SISA MARGIN/unit Actual (LM) (exc Refund)' , wbf['header'])
        worksheet.merge_range(f'J{row+1}:K{row+1}', 'CEK SCO/TL' , wbf['header'])
        worksheet.write(f'J{row+2}', 'SISA MARGIN/unit pengajuan (exc Refund)' , wbf['header'])
        worksheet.write(f'K{row+2}', 'SISA MARGIN/unit Actual (LM) (exc Refund)' , wbf['header'])
        worksheet.merge_range(f'L{row+1}:L{row+2}', 'KETERANGAN (apabila Statusnya CEK maka soh cek kembali angka yg diajukan' , wbf['header'])
        worksheet.merge_range(f'M{row+1}:M{row+2}', 'TTL SALES LM' , wbf['header'])
        worksheet.merge_range(f'N{row+1}:O{row+1}', 'LAST MONTH' , wbf['header'])
        worksheet.write(f'N{row+2}', 'CASH' , wbf['header'])
        worksheet.write(f'O{row+2}', 'CREDIT' , wbf['header'])
        worksheet.merge_range(f'P{row+1}:P{row+2}', 'TTL SALES (M)' , wbf['header'])        
        worksheet.merge_range(f'Q{row+1}:S{row+1}', '(UNIT CASH)' , wbf['header'])
        worksheet.write(f'Q{row+2}', 'SALESMAN' , wbf['header'])
        worksheet.write(f'R{row+2}', 'S.COUNTER' , wbf['header'])
        worksheet.write(f'S{row+2}', 'SCO / TL' , wbf['header'])
        worksheet.merge_range(f'T{row+1}:T{row+2}', 'TTL UNIT (CASH)' , wbf['header'])
        worksheet.merge_range(f'U{row+1}:W{row+1}', '(UNIT CREDIT)' , wbf['header'])
        worksheet.write(f'U{row+2}', 'SALESMAN' , wbf['header'])
        worksheet.write(f'V{row+2}', 'S.COUNTER' , wbf['header'])
        worksheet.write(f'W{row+2}', 'SCO / TL' , wbf['header'])
        worksheet.merge_range(f'X{row+1}:X{row+2}', 'TTL UNIT (CREDIT)' , wbf['header'])
        worksheet.merge_range(f'Y{row+1}:AA{row+1}', 'DISKON (CASH) (beban dealer+HC)' , wbf['header'])
        worksheet.write(f'Y{row+2}', 'SALESMAN' , wbf['header'])
        worksheet.write(f'Z{row+2}', 'S.COUNTER' , wbf['header'])
        worksheet.write(f'AA{row+2}', 'SCO / TL' , wbf['header'])
        worksheet.merge_range(f'AB{row+1}:AB{row+2}', 'TTL DISKON (CASH)' , wbf['header'])
        worksheet.merge_range(f'AC{row+1}:AE{row+1}', 'DISKON (CREDIT) (Beban dealer +HC)' , wbf['header'])
        worksheet.write(f'AC{row+2}', 'SALESMAN' , wbf['header'])
        worksheet.write(f'AD{row+2}', 'S.COUNTER' , wbf['header'])
        worksheet.write(f'AE{row+2}', 'SCO / TL' , wbf['header'])
        worksheet.merge_range(f'AF{row+1}:AF{row+2}', 'TTL DISKON (CREDIT)' , wbf['header'])
        worksheet.merge_range(f'AG{row+1}:AG{row+2}', 'GROSS PROFIT BBN' , wbf['header'])
        worksheet.merge_range(f'AH{row+1}:AH{row+2}', 'GROSS PROFIT UNIT' , wbf['header'])
        worksheet.merge_range(f'AI{row+1}:AI{row+2}', 'TTL GP' , wbf['header'])
        # worksheet.merge_range(f'AN{row+1}:AN{row+2}', 'REFUND' , wbf['header'])
        worksheet.merge_range(f'AJ{row+1}:AL{row+1}', 'SISA MARGIN SALESMAN (exc Refund)' , wbf['header'])
        worksheet.write(f'AJ{row+2}', 'CASH' , wbf['header'])
        worksheet.write(f'AK{row+2}', 'CREDIT' , wbf['header'])
        worksheet.write(f'AL{row+2}', 'TOTAL' , wbf['header'])
        worksheet.merge_range(f'AM{row+1}:AO{row+1}', 'SISA MARGIN SC (exc Refund)' , wbf['header'])
        worksheet.write(f'AM{row+2}', 'CASH' , wbf['header'])
        worksheet.write(f'AN{row+2}', 'CREDIT' , wbf['header'])
        worksheet.write(f'AO{row+2}', 'TOTAL' , wbf['header'])
        worksheet.merge_range(f'AP{row+1}:AR{row+1}', 'SISA MARGIN SCO / TL (exc Refund)' , wbf['header'])
        worksheet.write(f'AP{row+2}', 'CASH' , wbf['header'])
        worksheet.write(f'AQ{row+2}', 'CREDIT' , wbf['header'])
        worksheet.write(f'AR{row+2}', 'TOTAL' , wbf['header'])
        worksheet.merge_range(f'AS{row+1}:AU{row+1}', 'SISA MARGIN ALL (exc Refund)' , wbf['header'])
        worksheet.write(f'AS{row+2}', 'CASH' , wbf['header'])
        worksheet.write(f'AT{row+2}', 'CREDIT' , wbf['header'])
        worksheet.write(f'AU{row+2}', 'TOTAL' , wbf['header'])
        worksheet.merge_range(f'AV{row+1}:AV{row+2}', 'APPROVAL AM' , wbf['header_white'])
        worksheet.merge_range(f'AW{row+1}:AX{row+1}', 'Sisa Margin Salesman' , wbf['header_white'])
        
        worksheet.merge_range(f'AW10:AZ12', 'INI TARGET SISA MARGIN YANG AKAN MENJADI ACUAN UNTUK TARGET SISA MARGIN' , wbf['content_reference_note'])
        worksheet.write(f'AW{row+2}', 'CASH' , wbf['header'])
        worksheet.write(f'AX{row+2}', 'CREDIT' , wbf['header'])
        worksheet.merge_range(f'AY{row+1}:AZ{row+1}', 'Sisa Margin SC' , wbf['header_white'])
        worksheet.write(f'AY{row+2}', 'CASH' , wbf['header'])
        worksheet.write(f'AZ{row+2}', 'CREDIT' , wbf['header'])

        row += 3
        row_awal = row
        for row_data in records:
            series = row_data.get('series_name')
            year = str(date.today().year) if row_data.get('year') == 0 else row_data['year']
            gp_bbn = row_data.get('gp_bbn')
            gp_unit = row_data.get('gp_unit')
            
            ttl_sales_lm_cash = row_data.get('ttl_sales_lm_cash')
            ttl_sales_lm_credit = row_data.get('ttl_sales_lm_credit')
            salesman_margin = row_data.get('salesman_margin', 0)
            sales_counter_margin = row_data.get('sales_counter_margin', 0)
            sales_coordinator_margin = row_data.get('sco_margin', 0)
            
            qty = 1 if salesman_margin > 0 else 0
            qty += 1 if sales_counter_margin > 0 else 0
            qty += 1 if sales_coordinator_margin > 0 else 0

            lm_res_margin = (salesman_margin + sales_counter_margin + sales_coordinator_margin) / qty if qty > 0 else 0
            
            unit_cash_salesman = row_data.get('unit_cash_salesman', 0)
            unit_cash_scounter = row_data.get('unit_cash_scounter', 0)
            unit_cash_sco = row_data.get('unit_cash_sco', 0)
            unit_credit_salesman = row_data.get('unit_credit_salesman', 0)
            unit_credit_scounter = row_data.get('unit_credit_scounter', 0)
            unit_credit_sco = row_data.get('unit_credit_sco', 0)
            discount_cash_salesman = row_data.get('discount_cash_salesman', 0)
            discount_cash_counter = row_data.get('discount_cash_counter', 0)
            discount_cash_sco = row_data.get('discount_cash_sco', 0)
            discount_credit_salesman = row_data.get('discount_credit_salesman', 0)
            discount_credit_counter = row_data.get('discount_credit_counter', 0)
            discount_credit_sco = row_data.get('discount_credit_sco', 0)
            state = row_data.get('state', '')
            
            worksheet.write(f'B{row}', series , wbf['content'])
            worksheet.write(f'C{row}', year , wbf['content'])
            # CEK ALL JABATAN
            worksheet.write(f'D{row}', f'=IFERROR(AU{row}/P{row}, 0)', wbf['content_float'])
            worksheet.write(f'E{row}', lm_res_margin, wbf['content_float'])

            # CEK SALESMAN (PARTNER, PAYROLL, SC PARTNER)
            worksheet.write(f'F{row}', f'=IFERROR(AL{row}/(Q{row}+U{row}), 0)', wbf['content_float'])
            worksheet.write(f'G{row}', salesman_margin, wbf['content_float'])

            # CEK SALES COUNTER
            worksheet.write(f'H{row}', f'=IFERROR(AO{row}/(R{row}+V{row}), 0)', wbf['content_float'])
            worksheet.write(f'I{row}', sales_counter_margin, wbf['content_float'])

            # CEK SCO / TL
            worksheet.write(f'J{row}', f'=IFERROR(AR{row}/(S{row}+W{row}), 0)', wbf['content_float'])
            worksheet.write(f'K{row}', sales_coordinator_margin, wbf['content_float'])

            worksheet.write(f'L{row}', f'=IF(D{row}<E{row}, "CEK", "OK")', wbf['content_float'])
            worksheet.write(f'M{row}', f'=SUM(N{row}:O{row})', wbf['content_float'])
            worksheet.write(f'N{row}', ttl_sales_lm_cash, wbf['content_float'])
            worksheet.write(f'O{row}', ttl_sales_lm_credit, wbf['content_float'])
            worksheet.write(f'P{row}', f'=T{row}+X{row}', wbf['content_float'])
            
            worksheet.write(f'Q{row}', unit_cash_salesman , wbf['content_blue'])
            worksheet.write(f'R{row}', unit_cash_scounter , wbf['content_blue'])
            worksheet.write(f'S{row}', unit_cash_sco , wbf['content_locked'])
            worksheet.write(f'T{row}', f'=SUM(Q{row}:S{row})', wbf['content_float'])
            
            worksheet.write(f'U{row}', unit_credit_salesman , wbf['content_blue'])
            worksheet.write(f'V{row}', unit_credit_scounter , wbf['content_blue'])
            worksheet.write(f'W{row}', unit_credit_sco , wbf['content_locked'])
            worksheet.write(f'X{row}', f'=SUM(U{row}:W{row})', wbf['content_float'])

            worksheet.write(f'Y{row}', discount_cash_salesman , wbf['content_blue'])
            worksheet.write(f'Z{row}', discount_cash_counter , wbf['content_blue'])
            worksheet.write(f'AA{row}', discount_cash_sco , wbf['content_locked'])
            worksheet.write(f'AB{row}', f'=(Q{row}*Y{row})+(R{row}*Z{row})+(S{row}*AA{row})', wbf['content_float'])

            worksheet.write(f'AC{row}', discount_credit_salesman , wbf['content_blue'])
            worksheet.write(f'AD{row}', discount_credit_counter , wbf['content_blue'])
            worksheet.write(f'AE{row}', discount_credit_sco , wbf['content_locked'])
            worksheet.write(f'AF{row}', f'=(U{row}*AC{row})+(V{row}*AD{row})+(W{row}*AE{row})', wbf['content_float'])

            worksheet.write(f'AG{row}', gp_bbn , wbf['content_float'])
            worksheet.write(f'AH{row}', gp_unit , wbf['content_float'])
            worksheet.write(f'AI{row}', f'=SUM(AG{row}:AH{row})', wbf['content_float'])
            # worksheet.write(f'AN{row}', 765000 , wbf['content_float'])

            # SISA MARGIN SALESMAN
            worksheet.write(f'AJ{row}', f'=((AG{row}+AH{row})*Q{row})-(Q{row}*T{row})', wbf['content_float'])
            worksheet.write(f'AK{row}', f'=((AG{row}+AH{row})*U{row})-(U{row}*AC{row})', wbf['content_float'])
            worksheet.write(f'AL{row}', f'=SUM(AJ{row}:AK{row})', wbf['content_float'])
            
            # SISA MARGIN SC
            worksheet.write(f'AM{row}', f'=((AG{row}+AH{row})*R{row})-(S{row}*Z{row})', wbf['content_float'])
            worksheet.write(f'AN{row}', f'=((AG{row}+AH{row})*V{row})-(V{row}*AD{row})', wbf['content_float'])
            worksheet.write(f'AO{row}', f'=SUM(AM{row}:AN{row})', wbf['content_float'])            
            
            # SISA MARGIN SCO
            worksheet.write(f'AP{row}', f'=((AG{row}+AH{row})*S{row})-(S{row}*AA{row})', wbf['content_locked'])
            worksheet.write(f'AQ{row}', f'=((AG{row}+AH{row})*W{row})-(W{row}*AE{row})', wbf['content_locked'])
            worksheet.write(f'AR{row}', f'=SUM(AP{row}:AQ{row})', wbf['content_locked'])
            
            # SISA MARGIN ALL
            worksheet.write(f'AS{row}', f'=((AG{row}+AH{row})*T{row})-AB{row}', wbf['content_float'])
            worksheet.write(f'AT{row}', f'=((AG{row}+AH{row})*X{row})-AF{row}', wbf['content_float'])
            worksheet.write(f'AU{row}', f'=SUM(AS{row}:AT{row})', wbf['content_float'])
            worksheet.write(f'AV{row}', state , wbf['content_float'])
            worksheet.write(f'AW{row}', f'=IFERROR(AJ{row}/Q{row}, 0)', wbf['content_reference'])
            worksheet.write(f'AX{row}', f'=IFERROR(AK{row}/U{row}, 0)', wbf['content_reference'])
            worksheet.write(f'AY{row}', f'=IFERROR(AM{row}/R{row}, 0)', wbf['content_reference'])
            worksheet.write(f'AZ{row}', f'=IFERROR(AN{row}/V{row}, 0)', wbf['content_reference'])

            row += 1

        row_akhir = row - 1
        worksheet.write('C7', f'=SUM(P{row_awal}:P{row_akhir})', wbf['month_agg'])
        worksheet.write('C8', f'=SUM(T{row_awal}:T{row_akhir})' , wbf['month_agg'])
        worksheet.write('C9', f'=SUM(X{row_awal}:X{row_akhir})' , wbf['month_agg'])
        worksheet.write('C10', f'=SUM(AU{row_awal}:AU{row_akhir})' , wbf['month_agg'])
        worksheet.write('C11', f'=756000*SUM(X{row_awal}:X{row_akhir})' , wbf['month_agg'])
        if self.company_id.state_id.code == '1800':
            worksheet.write('C12', '=C10+C11-C3-C4' , wbf['month_agg'])
        else:
            worksheet.write('C12', '=C10+C11-C3' , wbf['month_agg'])

        worksheet.write('D8', f'=SUM(N{row_awal}:N{row_akhir})', wbf['last_month_agg'])
        worksheet.write('D9', f'=SUM(O{row_awal}:O{row_akhir})', wbf['last_month_agg'])

        worksheet.write(f'AH{row+1}', 'TOTAL SISA MARGIN' , wbf['footer_total_margin'])
        # SISA MARGIN SALESMAN
        worksheet.write(f'AJ{row+1}', f'=SUM(AJ{row_awal}:AJ{row_akhir})', wbf['content_float'])
        worksheet.write(f'AK{row+1}', f'=SUM(AK{row_awal}:AK{row_akhir})', wbf['content_float'])
        worksheet.write(f'AL{row+1}', f'=SUM(AL{row_awal}:AL{row_akhir})', wbf['content_float'])        
        
        # SISA MARGIN SC
        worksheet.write(f'AM{row+1}', f'=SUM(AM{row_awal}:AM{row_akhir})', wbf['content_float'])
        worksheet.write(f'AN{row+1}', f'=SUM(AN{row_awal}:AN{row_akhir})', wbf['content_float'])
        worksheet.write(f'AO{row+1}', f'=SUM(AO{row_awal}:AO{row_akhir})', wbf['content_float'])
        
        # SISA MARGIN SCO
        worksheet.write(f'AP{row+1}', f'=SUM(AP{row_awal}:AP{row_akhir})', wbf['content_float'])
        worksheet.write(f'AQ{row+1}', f'=SUM(AQ{row_awal}:AQ{row_akhir})', wbf['content_float'])
        worksheet.write(f'AR{row+1}', f'=SUM(AR{row_awal}:AR{row_akhir})', wbf['content_float'])
        
        # SISA MARGIN ALL
        worksheet.write(f'AS{row+1}', f'=SUM(AS{row_awal}:AS{row_akhir})', wbf['content_float'])
        worksheet.write(f'AT{row+1}', f'=SUM(AT{row_awal}:AT{row_akhir})', wbf['content_float'])
        worksheet.write(f'AU{row+1}', f'=SUM(AU{row_awal}:AU{row_akhir})', wbf['content_float'])
        
        worksheet.write(f'B{row+1}', 'AREA MANAGER' , wbf['footer_total_margin'])
        worksheet.write(f'C{row+1}', area_manager , wbf['footer_total_margin'])

        worksheet.freeze_panes(14, 4) # 38

        workbook.close()
        out = base64.b64encode(fp.getvalue())
        self.data_x = out
        self.file = filename
        
        fp.close()
        return {
            'type': 'ir.actions.act_url',
            'name': 'contract',
            'url': '/web/content/tw.download.profit.before.tax/%s/data_x/%s?download=true' % (self.id, filename)
        }
    

    
    
    def add_workbook_format(self, workbook):
        self.wbf['company'] = workbook.add_format({'align': 'left','font_color':'#000000','num_format': 'dd-mm-yyyy'})
        self.wbf['company'].set_font_size(10)

        self.wbf['company_header'] = workbook.add_format({'bg_color':'#FFFFFF','align': 'center','font_color': '#000000'})
        self.wbf['company_header'].set_top()
        self.wbf['company_header'].set_bottom()
        self.wbf['company_header'].set_left()
        self.wbf['company_header'].set_right()
        self.wbf['company_header'].set_font_size(11)
        self.wbf['company_header'].set_align('vcenter')

        self.wbf['month_agg'] = workbook.add_format({'bg_color':'#FFFF00','align': 'right','font_color': '#000000', 'num_format': '#,##0.00'})
        self.wbf['month_agg'].set_top()
        self.wbf['month_agg'].set_bottom()
        self.wbf['month_agg'].set_left()
        self.wbf['month_agg'].set_right()
        self.wbf['month_agg'].set_font_size(11)
        self.wbf['month_agg'].set_align('vcenter')
        
        self.wbf['last_month_agg'] = workbook.add_format({'bg_color':'#FFFFFF','align': 'right','font_color': '#000000', 'num_format': '#,##0.00'})
        self.wbf['last_month_agg'].set_top()
        self.wbf['last_month_agg'].set_bottom()
        self.wbf['last_month_agg'].set_left()
        self.wbf['last_month_agg'].set_right()
        self.wbf['last_month_agg'].set_font_size(11)
        self.wbf['last_month_agg'].set_align('vcenter')

        self.wbf['footer_total_margin'] = workbook.add_format({'bold': 1,'align': 'right','font_color':'#000000','num_format': 'dd-mm-yyyy'})
        self.wbf['footer_total_margin'].set_font_size(10)

        self.wbf['footer'] = workbook.add_format({'align':'left'})

        self.wbf['top_header'] = workbook.add_format({'bg_color':'#FFFF00','align': 'center','font_color': '#000000'})
        self.wbf['top_header'].set_top()
        self.wbf['top_header'].set_bottom()
        self.wbf['top_header'].set_left()
        self.wbf['top_header'].set_right()
        self.wbf['top_header'].set_font_size(11)
        self.wbf['top_header'].set_align('vcenter')

        self.wbf['top_header_light_yellow'] = workbook.add_format({'bg_color':'#fefac9','align': 'center','font_color': '#000000'})
        self.wbf['top_header_light_yellow'].set_top()
        self.wbf['top_header_light_yellow'].set_bottom()
        self.wbf['top_header_light_yellow'].set_left()
        self.wbf['top_header_light_yellow'].set_right()
        self.wbf['top_header_light_yellow'].set_font_size(11)
        self.wbf['top_header_light_yellow'].set_align('vcenter')

        self.wbf['top_header_light_yellow_float'] = workbook.add_format({'bg_color':'#fefac9','align': 'center','font_color': '#000000','num_format': '#,##0'})
        self.wbf['top_header_light_yellow_float'].set_top()
        self.wbf['top_header_light_yellow_float'].set_bottom()
        self.wbf['top_header_light_yellow_float'].set_left()
        self.wbf['top_header_light_yellow_float'].set_right()
        self.wbf['top_header_light_yellow_float'].set_font_size(11)
        self.wbf['top_header_light_yellow_float'].set_align('vcenter')

        self.wbf['header'] = workbook.add_format({'bg_color':'#FFFF00','bold': 1,'align': 'center','font_color': '#000000'})
        self.wbf['header'].set_top()
        self.wbf['header'].set_bottom()
        self.wbf['header'].set_left()
        self.wbf['header'].set_right()
        self.wbf['header'].set_font_size(11)
        self.wbf['header'].set_text_wrap()
        self.wbf['header'].set_align('vcenter')

        self.wbf['header_blue'] = workbook.add_format({'bg_color':'#39639d','bold': 1,'align': 'center','font_color': '#FFFFFF'})
        self.wbf['header_blue'].set_top()
        self.wbf['header_blue'].set_bottom()
        self.wbf['header_blue'].set_left()
        self.wbf['header_blue'].set_right()
        self.wbf['header_blue'].set_font_size(11)
        self.wbf['header_blue'].set_text_wrap()
        self.wbf['header_blue'].set_align('vcenter')

        self.wbf['header_white'] = workbook.add_format({'bg_color':'#FFFFFF','bold': 1,'align': 'center','font_color': '#000000'})
        self.wbf['header_white'].set_top()
        self.wbf['header_white'].set_bottom()
        self.wbf['header_white'].set_left()
        self.wbf['header_white'].set_right()
        self.wbf['header_white'].set_font_size(11)
        self.wbf['header_white'].set_text_wrap()
        self.wbf['header_white'].set_align('vcenter')

        self.wbf['header_left'] = workbook.add_format({'bg_color':'#FFFF00','bold': 1,'align': 'center','font_color': '#000000'})
        self.wbf['header_left'].set_top(2)
        self.wbf['header_left'].set_bottom()
        self.wbf['header_left'].set_left(2)
        self.wbf['header_left'].set_right()
        self.wbf['header_left'].set_font_size(11)
        self.wbf['header_left'].set_align('vcenter')
        
        self.wbf['header_right'] = workbook.add_format({'bg_color':'#FFFF00','bold': 1,'align': 'center','font_color': '#000000'})
        self.wbf['header_right'].set_top(2)
        self.wbf['header_right'].set_bottom()
        self.wbf['header_right'].set_left()
        self.wbf['header_right'].set_right(2)
        self.wbf['header_right'].set_font_size(11)
        self.wbf['header_right'].set_align('vcenter')

        self.wbf['content'] = workbook.add_format({'align': 'left','font_color': '#000000'})
        self.wbf['content'].set_left()
        self.wbf['content'].set_right()
        self.wbf['content'].set_top()
        self.wbf['content'].set_bottom()
        self.wbf['content'].set_font_size(10)

        self.wbf['content_blue'] = workbook.add_format({'bg_color':'#d6ecff','align': 'right','font_color': '#000000', 'num_format': '#,##0', 'locked': False})
        self.wbf['content_blue'].set_left()
        self.wbf['content_blue'].set_right()
        self.wbf['content_blue'].set_top()
        self.wbf['content_blue'].set_bottom()
        self.wbf['content_blue'].set_font_size(10)
        
        self.wbf['content_locked'] = workbook.add_format({'align': 'right','font_color': '#000000', 'num_format': '#,##0'})
        self.wbf['content_locked'].set_left()
        self.wbf['content_locked'].set_right()
        self.wbf['content_locked'].set_top()
        self.wbf['content_locked'].set_bottom()
        self.wbf['content_locked'].set_font_size(10)

        self.wbf['content_float'] = workbook.add_format({'align': 'right','num_format': '#,##0'})
        self.wbf['content_float'].set_right() 
        self.wbf['content_float'].set_left()
        self.wbf['content_float'].set_top()
        self.wbf['content_float'].set_bottom()
        self.wbf['content_float'].set_font_size(10)     

        self.wbf['content_bg'] = workbook.add_format({'bg_color': '#81DAF5','align': 'center','font_color': '#000000'})
        self.wbf['content_bg'].set_left()
        self.wbf['content_bg'].set_right()
        self.wbf['content_bg'].set_top()
        self.wbf['content_bg'].set_bottom()
        self.wbf['content_bg'].set_font_size(10)                
      
        self.wbf['content_center'] = workbook.add_format({'align': 'center','font_color': '#000000'})
        self.wbf['content_center'].set_left()
        self.wbf['content_center'].set_right()
        self.wbf['content_center'].set_top()
        self.wbf['content_center'].set_bottom()
        self.wbf['content_center'].set_font_size(10)
        
        self.wbf['content_left'] = workbook.add_format({'align': 'center','font_color': '#000000'})
        self.wbf['content_left'].set_left(2)
        self.wbf['content_left'].set_right()
        self.wbf['content_left'].set_top()
        self.wbf['content_left'].set_bottom()
        self.wbf['content_left'].set_font_size(10)
        
        self.wbf['content_right'] = workbook.add_format({'align': 'center','font_color': '#000000'})
        self.wbf['content_right'].set_left()
        self.wbf['content_right'].set_right(2)
        self.wbf['content_right'].set_top()
        self.wbf['content_right'].set_bottom()
        self.wbf['content_right'].set_font_size(10)

        self.wbf['content_bottom'] = workbook.add_format({'align': 'center','font_color': '#000000'})
        self.wbf['content_bottom'].set_left()
        self.wbf['content_bottom'].set_right()
        self.wbf['content_bottom'].set_top()
        self.wbf['content_bottom'].set_bottom(2)
        self.wbf['content_bottom'].set_font_size(10)

        self.wbf['content_left_bottom'] = workbook.add_format({'align': 'center','font_color': '#000000'})
        self.wbf['content_left_bottom'].set_left(2)
        self.wbf['content_left_bottom'].set_right()
        self.wbf['content_left_bottom'].set_top()
        self.wbf['content_left_bottom'].set_bottom(2)
        self.wbf['content_left_bottom'].set_font_size(10)
        
        self.wbf['content_right_bottom'] = workbook.add_format({'align': 'center','font_color': '#000000'})
        self.wbf['content_right_bottom'].set_left()
        self.wbf['content_right_bottom'].set_right(2)
        self.wbf['content_right_bottom'].set_top()
        self.wbf['content_right_bottom'].set_bottom(2)
        self.wbf['content_right_bottom'].set_font_size(10)

        self.wbf['content_center_bg'] = workbook.add_format({'bg_color':'#85C1E9', 'align': 'center','font_color': '#000000'})
        self.wbf['content_center_bg'].set_left()
        self.wbf['content_center_bg'].set_right()
        self.wbf['content_center_bg'].set_top()
        self.wbf['content_center_bg'].set_bottom()
        self.wbf['content_center_bg'].set_font_size(10)                
        
        self.wbf['content_center_bg_bottom'] = workbook.add_format({'bg_color':'#85C1E9', 'align': 'center','font_color': '#000000'})
        self.wbf['content_center_bg_bottom'].set_left()
        self.wbf['content_center_bg_bottom'].set_right()
        self.wbf['content_center_bg_bottom'].set_top()
        self.wbf['content_center_bg_bottom'].set_bottom(2)
        self.wbf['content_center_bg_bottom'].set_font_size(10)
        
        self.wbf['content_reference_note'] = workbook.add_format({'bg_color':"#FFC4FA", 'align': 'center'})
        self.wbf['content_reference_note'].set_left()
        self.wbf['content_reference_note'].set_right()
        self.wbf['content_reference_note'].set_top()
        self.wbf['content_reference_note'].set_bottom()
        self.wbf['content_reference_note'].set_text_wrap()
        self.wbf['content_reference_note'].set_align('vcenter')
        self.wbf['content_reference_note'].set_font_size(10)
        
        self.wbf['content_reference'] = workbook.add_format({'bg_color':"#FFC4FA", 'align': 'right','num_format': '#,##0'})
        self.wbf['content_reference'].set_left()
        self.wbf['content_reference'].set_right()
        self.wbf['content_reference'].set_top()
        self.wbf['content_reference'].set_bottom()
        self.wbf['content_reference'].set_font_size(10)                
        
        return workbook