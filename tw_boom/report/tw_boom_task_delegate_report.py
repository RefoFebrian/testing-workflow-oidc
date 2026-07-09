# 1: imports of python lib
from datetime import datetime, date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TWBoomTaskDelegateReport(models.TransientModel):
    _name = "tw.boom.task.delegate.report"
    _description = 'TW Boom Task Delegate Report'


    # 7: defaults methods
    def _get_default_date(self):
        return date.today()

    def _get_default_branch(self):
        company_ids = self.env.user.company_ids
        if company_ids and len(company_ids) == 1 :
            return company_ids[0].id
        return False  

    def _set_domain_branch_ids(self):
        return [('id','in',[b.id for b in self.env.user.company_ids])]

    # 8: fields
    start_date = fields.Date('Start Date', default=_get_default_date)
    end_date = fields.Date('End Date', default=_get_default_date)

    options = fields.Selection([
        ('tgl_transaksi', 'Tanggal Transaksi'),
        ('tgl_delegasi', 'Tanggal Delegasi'),
    ], string='Opsi Tanggal')

    status = fields.Selection([
        ('current_pic', 'Current PIC'),
        ('delegated', 'Delegated'),
    ], default='delegated', string='Status')

    company_ids = fields.Many2many('res.company', 'tw_boom_task_delegate_report_company_rel', 'report_id', 'company_id', string='Branch', default=_get_default_branch, domain=_set_domain_branch_ids)

    @api.constrains('start_date','end_date')
    def _constrains_date(self):
        for record in self:
            if record.start_date > record.end_date:
                raise Warning('Start date must be less than end date')

    @api.onchange('start_date','end_date')
    def _onchange_date(self):
        if self.start_date > self.end_date:
            raise Warning('Start date must be less than end date')
    
    def export_report(self):
        company_ids = self.company_ids
        start_date = self.start_date
        end_date = self.end_date
        status = self.status
        query_where = ''

        if company_ids:
            query_where += " AND tbt.company_id IN {}".format(str(tuple([b.id for b in company_ids])).replace(',)', ')'))
        else:
            query_where += " AND tbt.company_id IN {}".format(str(tuple([b.id for b in self.env.user.company_ids])).replace(',)', ')'))
            
        if self.options == 'tgl_transaksi':
            query_where += " AND (tbt.transaction_date + INTERVAL '7 hours')::DATE >= '{}'".format(start_date)
            query_where += " AND (tbt.transaction_date + INTERVAL '7 hours')::DATE <= '{}'".format(end_date)
        
        if self.options == 'tgl_delegasi':
            query_where += " AND (tbthu.assign_date + INTERVAL '7 hours')::DATE >= '{}'".format(start_date)
            query_where += " AND (tbthu.assign_date + INTERVAL '7 hours')::DATE <= '{}'".format(end_date)

        if status:
            if status == 'current_pic':
                query_where += " AND tbt.pic_status = 'current_pic'"
            if status == 'delegated':
                query_where += " AND tbt.pic_status = 'delegated'"

        query = """
            SELECT 
                tbmc.name AS "Kategori"
                , tbsc.name AS "Sub Kategori"
                , kateg.name AS "Nama Kategori"
                , rc.code AS "Kode Dealer"
                , rc.name AS "Nama Dealer"
                , COALESCE(pic_before.pic_name, he.name) AS "Nama Employee"
                , COALESCE(pic_before.job_name, pic.name->>'en_US') AS "PIC Job"
                , he.name AS "Nama Employee Delegasi"
                , pic_delegasi.name->>'en_US' AS "PIC Job Delegasi"
                , tbt.no_transaction AS "No Transaksi"
                , tbt.source_transaction AS "Source Transaksi"
                , tbt.transaction_value AS "Value Transaksi"
                , TO_CHAR(tbt.transaction_date + INTERVAL '7 hours', 'YYYY-MM-DD HH24:MI:SS') AS "Tanggal Transaksi"
                , TO_CHAR(tbt.done_date + INTERVAL '7 hours', 'YYYY-MM-DD HH24:MI:SS') AS "Tanggal Transaksi Selesai"
                , TO_CHAR(tbthu.assign_date + INTERVAL '7 hours', 'YYYY-MM-DD HH24:MI:SS') AS "Tanggal Delegasi"
                , INITCAP(tbt.pic_status) AS "Status Delegasi"
                , INITCAP(tbt.state) AS "Status Task"
            FROM tw_boom_task tbt 
            LEFT JOIN tw_boom_main_category tbmc ON tbmc.id = tbt.main_category_id 
            LEFT JOIN tw_boom_sub_category tbsc ON tbsc.id = tbt.sub_category_id 
            LEFT JOIN tw_boom_category kateg ON kateg.id = tbt.category_id 
            LEFT JOIN res_company rc ON tbt.company_id = rc.id
            LEFT JOIN hr_employee he ON tbt.employee_id = he.id
            LEFT JOIN hr_job pic ON tbt.job_id = pic.id
            LEFT JOIN hr_job pic_delegasi ON tbt.job_delegation_id = pic_delegasi.id
            LEFT JOIN tw_boom_task_history_user tbthu ON tbthu.task_id = tbt.id and tbthu.job_id = tbt.job_delegation_id 
            LEFT JOIN LATERAL (
                SELECT
                    he2.name pic_name
                    , hj2.name->>'en_US' job_name
                FROM tw_boom_task_history_user hu
                LEFT JOIN hr_employee he2 ON hu.employee_id = he2.id
                LEFT JOIN hr_job hj2 ON hu.job_id = hj2.id
                WHERE 1=1
                AND hu.task_id = tbt.id
                ORDER BY hu.id DESC
                OFFSET 1
            ) pic_before ON TRUE
            WHERE 1=1
            --AND tbt.pic_status = 'delegated'
            {query_where}
        """.format(query_where=query_where)
        
        self._cr.execute(query)
        result = self._cr.dictfetchall()

        if not result:
            raise Warning('Tidak ada data untuk di export')


        return self.env['web.report'].sudo().generate_report('Laporan Delegasi Boom Task', result, show_total_footer=False)
        

        