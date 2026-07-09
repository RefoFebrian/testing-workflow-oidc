# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from datetime import datetime, timedelta
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwLeadCrmReport(models.TransientModel):
    _name = "tw.lead.crm.report"
    _description = 'Leads CRM Report'

    # 7: defaults methods
    def _get_default_date(self): 
        return self.env['res.company'].get_default_date()
    
    def _get_default_company(self):
        company_ids = False
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1:
            return company_ids[0].id
        return False
    
    def _set_domain_employee_ids(self):
        return [('company_id','in',[b.id for b in self.env.user.company_ids])]

    # 8: fields
    file = fields.Char('File Name')
    data_x = fields.Binary('File', readonly=True)
    state_x =  fields.Selection([
        ('choose','choose'),
        ('get','get')
    ], default='choose')
    status = fields.Selection([
        ('all','All'),
        ('open','Open'),
        ('assigment','Assigment')
    ], string='Status')
    periode_by = fields.Selection([
        ('generate_date','CRM Generate Date'),
        ('assign_date','CRM Assign Date'),
    ], string='Periode By')
    start_date = fields.Date('Start Date', default=_get_default_date)
    end_date = fields.Date('End Date', default=_get_default_date)
    # division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())

    # 9: relation fields
    company_ids = fields.Many2many('res.company', 'tw_lead_crm_report_company_rel', 'tw_lead_crm_report_id', 'company_id', "Branch", domain="[('parent_id','!=',False)]", default=_get_default_company)
    employee_ids = fields.Many2many('hr.employee', 'tw_lead_crm_report_employee_rel', 'tw_lead_crm_report_id', 'employee_id', 'Sales', copy=False, domain=_set_domain_employee_ids)

    # 10: constraints & sql constraints

    # 11: compute/depends & ON change methods

    # 12: override methods

    # 13: action methods
    def action_lead_crm_report_tree(self):
        domain = []
        form_view_id = self.env.ref('tw_lead_crm.tw_lead_crm_report_wizard_form_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Laporan Lead CRM',
            'path': 'lead-crm-report',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tw.lead.crm.report',
            'target': 'new',
            'domain': domain,
            'views': [(form_view_id, 'form')],
            'context': {'search_default_fieldname': 1},
        }
    
    def excel_laporan(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        return self._download_laporan()
    
    # 14: private methods
    def _download_laporan(self):
        company = self.company_ids
        additional_where = ''
        if self.employee_ids:
            employee_list = str(tuple([e.id for e in self.employee_ids])).replace(',)', ')')
            additional_where += f' AND emp.id IN {employee_list}'
        if company:
            company_list = str(tuple([b.id for b in company])).replace(',)', ')')
            additional_where += f' AND branch.id IN {company_list}'
        if self.status == 'open':
            additional_where += " AND dlc.state = 'open' "
        elif self.status == 'assigment':
            additional_where += " AND dlc.state = 'done' "

        if self.periode_by == 'generate_date':
            additional_where += f" AND SPLIT_PART(dlc.source_document, '_', 1)::DATE BETWEEN '{str(self.start_date)}' AND '{str(self.end_date)}'"
        elif self.periode_by == 'assign_date':
            additional_where += f" AND (lead.create_date +  INTERVAL '7 hours')::DATE BETWEEN '{str(self.start_date)}' AND '{str(self.end_date)}'"

        query = f"""
            SELECT 
                branch.kode_dealer kode_branch
                , branch.name as branch
                , TO_CHAR(SPLIT_PART(dlc.source_document, '_', 1)::DATE, 'YYYY-MM-DD') AS periode
                , dlc.name nomor_crm
                , lead.name no_buku_tamu
                , md.name sumber_main_dealer
                , rb.name sumber_cabang
                , employee.name nama_sales
                , hj.name job_title
                , TO_CHAR((lead.create_date +  INTERVAL '7 hours')::DATE, 'YYYY-MM-DD') assign_date
                , ROW_NUMBER() OVER(PARTITION BY lead.id ORDER BY lead_activity.id ASC) follow_ke
                , CASE
                    WHEN (lead_activity.state_followup = 'completed' OR lead_activity.activity_result_id IS NOT NULL ) THEN 'Done'
                    WHEN (lead_activity.date + INTERVAL '7 hours')::date < now()::date THEN 'Overdue'
                    ELSE 'Bellum Follow Up'
                END AS status_activity
                , TO_CHAR((lead_activity.date + INTERVAL '7 hours'), 'YYYY-MM-DD') AS tgl_janji_follow_up
                , TO_CHAR((lead_activity.done_date + INTERVAL '7 hours')::TIMESTAMP(0), 'YYYY-MM-DD') AS activity_date
                , stage.name AS stage
                , dlar.name AS hasil_activity
                , lead.state status_buku_tamu
                , dlc.purchase_frequency repeat_order
                , TO_CHAR(dlc.last_date_order, 'YYYY-MM-DD') tanggal_terakhir_beli
                , TO_CHAR(dlc.next_date_purchase, 'YYYY-MM-DD') tanggal_pembelian_selanjutnya
                , COALESCE(lead.customer_name, dlc.customer_name) nama_konsumen
                , COALESCE(lead.no_ktp, dlc.no_ktp) no_ktp
                , COALESCE(lead.no_kk, dlc.no_kk) no_kk
                , COALESCE(lead.no_hp, dlc.no_hp) no_hp
                , COALESCE(lead.no_wa, dlc.no_wa) no_wa
                , '' status_nomor
                , rc.name kota
                , rcs.name provinsi
                , COALESCE(lead_activity.minat, lead.minat) minat
                , dlar.keterangan
                , dlc.product_type history_unit
                , '' no_sale_order
                , CASE
                    WHEN lead.finco_id NOTNULL THEN rp.name
                    ELSE 'Cash'
                END tipe_pembelian
                , dps.name produk_series
                , CASE
                    WHEN dlc.data_source = 's3_aws' THEN 'S3 AWS'
                    ELSE ''
                END AS sumber_data
            FROM tw_lead_crm dlc
            LEFT JOIN tw_lead lead ON dlc.lead_id = lead.id
            LEFT JOIN tw_lead_activity lead_activity ON lead.id = lead_activity.lead_id
            LEFT JOIN tw_master_act_type act_type ON lead.act_type_id = act_type.id
            LEFT JOIN tw_lead_log dll ON lead.id = dll.lead_id
            LEFT JOIN tw_lead_activity_result dlar ON lead_activity.activity_result_id = dlar.id
            LEFT JOIN tw_lead_stages stage ON lead_activity.stage_id = stage.id
            LEFT JOIN res_company branch ON lead.company_id = branch.id
            LEFT JOIN res_company md ON md.id = dlc.md_id 
            LEFT JOIN res_company rb ON rb.id = dlc.branch_resource_id 
            LEFT JOIN res_city rc ON rc.id = dlc.city_id
            LEFT JOIN res_country_state rcs ON rcs.id = dlc.state_id
            LEFT JOIN res_partner rp ON rp.id = lead.finco_id
            --LEFT JOIN tw_dealer_sale_order dso ON dso.teds_lead_name = lead.remark_api_tdm
            LEFT JOIN product_product pp ON pp.id = lead.product_id
            LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
            LEFT JOIN product_series dps ON dps.id = pt.series_id
            LEFT JOIN LATERAL (
                SELECT
                    CASE 
                        WHEN ru.id NOTNULL AND pic_fu.name != 'OdooBot' THEN he.id
                        ELSE lead.employee_id
                    END employee_id
                FROM res_users ru
                LEFT JOIN resource_resource rr ON rr.user_id = ru.id 
                LEFT JOIN hr_employee he ON he.resource_id = rr.id
                LEFT JOIN res_partner pic_fu ON pic_fu.id = ru.partner_id
                WHERE 1=1
                AND ru.id = lead_activity.write_uid
            ) sales ON TRUE
            LEFT JOIN hr_employee employee ON sales.employee_id = employee.id
            LEFT JOIN hr_job hj ON hj.id = employee.job_id 
            WHERE 1=1
            AND dlc.state IN ('open', 'outstanding', 'done', 'unused')
            {additional_where}
            GROUP BY branch.id, employee.id,dlc.id, rb.id, hj.id, lead.id, lead_activity.id, stage.id, dlar.id, act_type.id, md.id, rc.id, rcs.id, rp.id, dps.id
        """
        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()
        if not ress:
            raise Warning('Tidak ada data.')
        
        query_summary = f"""
            WITH ranked_data AS (
                SELECT 
                    branch.kode_dealer AS kode_branch
                    , branch.name AS branch
                    , TO_CHAR(SPLIT_PART(dlc.source_document, '_', 1)::DATE, 'YYYY-MM-DD') AS periode
                    , dlc.name AS nomor_crm
                    , lead.name AS no_buku_tamu
                    , md.name AS sumber_main_dealer
                    , rb.name AS sumber_cabang
                    , employee.name AS nama_sales
                    , hj.name AS job_title
                    , TO_CHAR((lead.create_date + INTERVAL '7 hours')::DATE, 'YYYY-MM-DD') AS assign_date
                    , ROW_NUMBER() OVER (PARTITION BY lead.id ORDER BY lead_activity.id ASC) AS follow_ke
                    , CASE 
                        WHEN (lead_activity.state_followup = 'completed' OR lead_activity.activity_result_id IS NOT NULL) THEN 'Done'
                        WHEN (lead_activity.date + INTERVAL '7 hours')::DATE < NOW()::DATE THEN 'Overdue'
                        ELSE 'Bellum Follow Up'
                    END AS status_activity
                    , TO_CHAR((lead_activity.date + INTERVAL '7 hours'), 'YYYY-MM-DD') AS tgl_janji_follow_up
                    , TO_CHAR((lead_activity.done_date + INTERVAL '7 hours')::TIMESTAMP(0), 'YYYY-MM-DD') AS activity_date
                    , stage.name AS stage
                    , dlar.name AS hasil_activity
                    , lead.state AS status_buku_tamu
                    , dlc.purchase_frequency AS repeat_order
                    , TO_CHAR(dlc.last_date_order, 'YYYY-MM-DD') AS tanggal_terakhir_beli
                    , TO_CHAR(dlc.next_date_purchase, 'YYYY-MM-DD') AS tanggal_pembelian_selanjutnya
                    , COALESCE(lead.customer_name, dlc.customer_name) AS nama_konsumen
                    , COALESCE(lead.no_ktp, dlc.no_ktp) AS no_ktp
                    , COALESCE(lead.no_kk, dlc.no_kk) AS no_kk
                    , COALESCE(lead.no_hp, dlc.no_hp) AS no_hp
                    , COALESCE(lead.no_wa, dlc.no_wa) AS no_wa
                    , '' AS status_nomor
                    , rc.name AS kota
                    , rcs.name AS provinsi
                    , COALESCE(lead_activity.minat, lead.minat) minat
                    , dlar.keterangan
                    , dlc.product_type AS history_unit
                    , '' AS no_sale_order
                    , CASE
                        WHEN lead.finco_id IS NOT NULL THEN rp.name
                        ELSE 'Cash'
                    END AS tipe_pembelian
                    , dps.name AS produk_series
                    , CASE
                        WHEN dlc.data_source = 's3_aws' THEN 'S3 AWS'
                        ELSE ''
                    END AS sumber_data
                    , ROW_NUMBER() OVER (PARTITION BY lead.name ORDER BY lead_activity.id DESC) AS rnk
                FROM tw_lead_crm dlc
                LEFT JOIN tw_lead lead ON dlc.lead_id = lead.id
                LEFT JOIN tw_lead_activity lead_activity ON lead.id = lead_activity.lead_id
                LEFT JOIN res_company branch ON lead.company_id = branch.id
                LEFT JOIN res_company md ON md.id = dlc.md_id
                LEFT JOIN res_company rb ON rb.id = dlc.branch_resource_id
                LEFT JOIN hr_employee employee ON lead.employee_id = employee.id
                LEFT JOIN hr_job hj ON hj.id = employee.job_id
                LEFT JOIN tw_lead_stages stage ON lead_activity.stage_id = stage.id
                LEFT JOIN tw_lead_activity_result dlar ON lead_activity.activity_result_id = dlar.id
                LEFT JOIN res_city rc ON rc.id = dlc.city_id
                LEFT JOIN res_country_state rcs ON rcs.id = dlc.state_id
                --LEFT JOIN tw_dealer_sale_order dso ON dso.teds_lead_name = lead.remark_api_tdm
                LEFT JOIN product_template pt ON pt.id = lead.product_id
                LEFT JOIN product_series dps ON dps.id = pt.series_id
                LEFT JOIN res_partner rp ON rp.id = lead.finco_id
                WHERE 1=1
                AND dlc.state IN ('open', 'outstanding', 'done', 'unused')
                {additional_where}
            )
            SELECT
                ranked_data.kode_branch
                , ranked_data.branch
                , ranked_data.periode
                , ranked_data.nomor_crm
                , ranked_data.no_buku_tamu
                , ranked_data.sumber_main_dealer
                , ranked_data.sumber_cabang
                , ranked_data.nama_sales
                , ranked_data.job_title
                , ranked_data.assign_date
                , ranked_data.follow_ke
                , ranked_data.status_activity
                , ranked_data.tgl_janji_follow_up
                , ranked_data.activity_date
                , ranked_data.stage
                , ranked_data.hasil_activity
                , ranked_data.status_buku_tamu
                , ranked_data.repeat_order
                , ranked_data.tanggal_terakhir_beli
                , ranked_data.tanggal_pembelian_selanjutnya
                , ranked_data.nama_konsumen
                , ranked_data.no_ktp
                , ranked_data.no_kk
                , ranked_data.no_hp
                , ranked_data.no_wa
                , ranked_data.status_nomor
                , ranked_data.kota
                , ranked_data.provinsi
                , ranked_data.minat
                , ranked_data.keterangan
                , ranked_data.history_unit
                , ranked_data.no_sale_order
                , ranked_data.tipe_pembelian
                , ranked_data.produk_series
                , ranked_data.sumber_data
            FROM ranked_data
            WHERE rnk = 1
        """
        self.env.cr.execute(query_summary)
        new_ress = self.env.cr.dictfetchall()
        if not new_ress:
            raise Warning('Tidak ada data.')
        
        data_sheet = {'Laporan Lead CRM': ress, 'Summary Lead CRM': new_ress}
        return self.env['web.report'].generate_report('Laporan Lead CRM', ress, data_sheet=data_sheet)
    
    