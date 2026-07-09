# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

class LeadDetailedReportWizard(models.TransientModel):
    _name = "tw.lead.detailed.report.wizard"
    _description = "Lead Detailed Report Wizard"

    def _get_default_branch(self):
        company_ids = False
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1 :
            return company_ids[0].id
        return False 
    def _get_default_date_from(self):
        return date.today() - relativedelta(months=1)
    
    def _get_default_date_to(self):
        return date.today()

    def _set_domain_company_ids(self):
        return [('id','in',[b.id for b in self.env.user.company_ids])]
    
    start_date = fields.Date('From Date', required=True, default=_get_default_date_from)
    end_date = fields.Date('To Date', required=True, default=_get_default_date_to)
    company_ids = fields.Many2many('res.company', string='Branch', required=True, default=_get_default_branch, domain=_set_domain_company_ids)
    data_source = fields.Selection([
        ('apps', 'Non Web'),
        ('all', 'All'),
        ],default='all', string='Data Source') 
    state = fields.Selection([
        ('all', 'All'),
        ('open', 'Open'),
        ('dealt', 'Dealt'),
        ('proposed','Proposed'),
        ('reciept','Reciept'),
        ('approved','Approved'),
        ('reject','Reject'),
        ('spk','SPK'),
        ],default='all', string='State')
    
    def action_generate_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        self.ensure_one()
        
        where = " WHERE 1=1"

        # Branch
        if self.company_ids:
            where += " AND lead.company_id IN %s" % str(tuple(b.id for b in self.company_ids)).replace(',)', ')')
        else:
            where += " AND lead.company_id IN %s" % str(tuple(b.id for b in self.env.user.company_ids)).replace(',)', ')')

        # Date filters
        if self.start_date:
            where += " AND lead.date >= '%s'" % str(self.start_date)

        if self.end_date:
            where += " AND lead.date <= '%s'" % str(self.end_date)

        # State
        if self.state in ['open', 'dealt', 'cancel']:
            where += " AND lead.state = '%s'" % str(self.state)

        # Data Source
        if self.data_source == 'apps':
            where += " AND lead.data_source IN ('apps','dgi')"

        #  grouping view personal data
        if not self.env.user.has_group('tw_lead_report.tw_group_pdp_laporan_buku_tamu'):
            query_no_hp = """CASE
                    WHEN regexp_replace(lead.mobile, '\\D', '', 'g') LIKE '62%' THEN
                        '0' || SUBSTRING(regexp_replace(lead.mobile, '\\D', '', 'g') FROM 3 FOR 3) ||
                        REPEAT('*',
                            LENGTH(regexp_replace(lead.mobile, '\\D', '', 'g')) - 4
                        )
                    ELSE
                        LEFT(regexp_replace(lead.mobile, '\\D', '', 'g'), 3) ||
                        REPEAT('*',
                            LENGTH(regexp_replace(lead.mobile, '\\D', '', 'g')) - 3
                        )
                END"""

            query_ktp="""
                LEFT(regexp_replace(lead.identification_number, '\\D', '', 'g'), 3) ||
                REPEAT('*',
                    GREATEST(
                        LENGTH(regexp_replace(lead.identification_number, '\\D', '', 'g')) - 3,
                    0)
                )
            """
            query_kk="""
                LEFT(regexp_replace(lead.identification_family_number, '\\D', '', 'g'), 3) ||
                REPEAT('*',
                    GREATEST(
                        LENGTH(regexp_replace(lead.identification_family_number, '\\D', '', 'g')) - 3,
                    0)
                )
            """
        else :
            query_no_hp = """lead.mobile"""
            query_ktp="""lead.identification_number"""
            query_kk="""lead.identification_family_number"""

        query = """
            SELECT 
                lead.name as no_buku_tamu,
                company_id.code as branch_code,
                company_id.name as branch_name,
                lead.date as tanggal,
                CASE 
                    WHEN sale_order.id IS NOT NULL AND sale_order.state IN ('approved','progress','done') THEN 'DO Teds'
                    WHEN lead.state = 'cancel' THEN 'Cancel'
                    WHEN lead.state = 'open' THEN INITCAP(interest.name)
                    ELSE 'Deal'
                END AS status,
                {query_ktp} as nomor_ktp,
                {query_kk} as nomor_kk,
                lead.customer_name as nama_konsumen,
                lead.street as alamat,
                kl.name as kecamatan,
                k.name as kelurahan,
                c.name as kab_kota,
                kelamin.name as jenis_kelamin,
                {query_no_hp} AS no_hp,
                empl.name as salesman,
                COALESCE(job.name->>'en_US', job.name->>'id_ID') as salesman_job_name,
                koordinator.name as salesman_koordinator,
                COALESCE(koordinator_job.name->>'en_US', koordinator_job.name->>'id_ID') as koordinator_job_name,
                CASE
                    WHEN lead.payment_type_id = '1' THEN 'Cash'
                    WHEN lead.payment_type_id = '2' THEN 'Credit'
                END AS jenis_pembelian,
                
                lead.down_payment as dp,
                partner.name as finco,
                COALESCE(prod_temp.name->>'en_US',prod_temp.name->>'id_ID') as tipe_unit,
                prod.default_code as code_unit,
                prod_temp.factur_code as code_marketing,
                COALESCE(warna_unit.name->>'en_US', warna_unit.name->>'id_ID') as warna,
                prod_type.name as segmen_unit,
                COALESCE(series_id.name->>'en_US', series_id.name->>'id_ID') as series_unit,
                lead.deal_date + INTERVAL '7 hours' as tanggal_deal,
                sale_order.name as so_number,
                sp.name AS jaringan_penjualan,
                act_type.name AS tipe_activity,
                tk.description AS titik_keramaian,
                location.name AS source_location,

                CASE 
                    WHEN lead.data_source = 'apps' THEN
                        CASE 
                            WHEN lead.version_name IS NOT NULL THEN
                                CASE WHEN lead.version_name = '1.0' THEN 'thor 1.0' ELSE lead.version_name END
                        ELSE 'Other'
                        END
                    WHEN lead.data_source = 'dgi' THEN 'DGI'
                    ELSE 'Web'
                END AS data_source,
                lead.note

            FROM tw_lead AS lead
            LEFT JOIN res_company AS company_id ON company_id.id = lead.company_id
            LEFT JOIN res_partner AS partner ON partner.id = lead.finco_id
            LEFT JOIN product_product prod ON prod.id = lead.product_id
            LEFT JOIN product_template AS prod_temp ON prod_temp.id = prod.product_tmpl_id
            LEFT JOIN product_series as series_id ON series_id.id = prod_temp.series_id
            LEFT JOIN (SELECT DISTINCT ON (product_tmpl_id) * FROM product_template_attribute_value ORDER BY product_tmpl_id, id) AS f ON f.product_tmpl_id = prod_temp.id
            LEFT JOIN product_attribute_value warna_unit ON warna_unit.id = f.product_attribute_value_id
            LEFT JOIN product_category AS prod_type ON prod_type.id = prod_temp.categ_id
            LEFT JOIN tw_selection kelamin ON lead.gender_id = kelamin.id
            LEFT JOIN res_country_state cs ON cs.id = lead.state_id
            LEFT JOIN res_city c ON c.id = lead.city_id
            LEFT JOIN res_district k ON k.id = lead.district_id
            LEFT JOIN res_sub_district kl ON kl.id = lead.sub_district_id
            LEFT JOIN hr_employee empl ON empl.id = lead.sales_id
            LEFT JOIN hr_employee koordinator ON lead.sales_coordinator_id = koordinator.id
            LEFT JOIN hr_job job ON empl.job_id = job.id
            LEFT JOIN hr_job koordinator_job ON koordinator.job_id = koordinator_job.id
            LEFT JOIN tw_selection sp ON lead.sales_channel_id = sp.id
            LEFT JOIN tw_selection interest ON interest.id = lead.interest_id
            LEFT JOIN tw_master_activity_type act_type ON act_type.id = lead.act_type_id

            left join tw_activity_atl_btl_line actl on lead.activity_plan_id = actl.id
            left join tw_mapping_titik_keramaian mapping on mapping.id = actl.mapping_activity_id
            LEFT JOIN tw_titik_keramaian tk ON mapping.activity_point_id = tk.id
            
            LEFT JOIN stock_location location ON location.id = lead.sales_source_location_id
            LEFT JOIN tw_dealer_spk spk ON spk.id = lead.spk_id
            LEFT JOIN tw_dealer_sale_order sale_order ON sale_order.id = spk.dealer_sale_order_id

        {where}
        """.format(where=where,query_no_hp=query_no_hp,query_ktp=query_ktp,query_kk=query_kk)



        
        self._cr.execute(query)
        results = self._cr.dictfetchall()
        # raise Warning(str(results))
        if not results:
            raise Warning("Tidak ada data untuk periode, status, Data Source dan cabang yang dipilih")
        report_name = f"Lead_Detailed_Report_{self.start_date.strftime('%Y%m%d')}_to_{self.end_date.strftime('%Y%m%d')}"
        return self.env['web.report'].sudo().generate_report(report_name, results,show_total_footer=False,freeze_panes_column=3)

    