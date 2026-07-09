# 1: imports of python lib
from datetime import datetime, date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwBoomTaskReport(models.TransientModel):
    _name = "tw.boom.task.report"
    _description = "Laporan BOOM Task"


    # 7: defaults methods

    def _get_default_date(self):
        return date.today()

    # 8: fields
    status = fields.Selection([
        ('all', 'All'),
        ('open', 'Open'),
        ('done', 'Done'),
    ], string='Status', default='all')

    period = fields.Selection([
        ('daily','Daily'),
        ('weekly','Weekly'),
        ('monthly','Monthly'),
    ], string='Periode')

    classification = fields.Selection([
        ('resiko','Resiko'),
        ('report','Report'),
        ('support','Support')
    ], string='Klasifikasi')

    start_date = fields.Date(string="Start Date", default=_get_default_date)
    end_date = fields.Date(string="End Date", default=_get_default_date)

    # 9: relation fields   
    pic_job_id = fields.Many2one('hr.job', 'PIC Job')
    main_category_id = fields.Many2one('tw.boom.main.category', 'Main Kategori')

    company_ids = fields.Many2many('res.company', 'tw_boom_task_report_company_rel', 'report_id', 'company_id', string='Branch')

    
    # 10: constraints & sql constraints
    @api.constrains('start_date','end_date')
    def _constrains_date(self):
        for record in self:
            if record.start_date > record.end_date:
                raise Warning('Start date must be less than end date')
    
    # 11: compute/depends & on change methods
    @api.onchange('start_date', 'end_date')
    def _onchange_date(self):
        if self.start_date > self.end_date:
            raise Warning('Start date must be less than end date')
    
    # 12: override methods
    
    # 13: action methods
    def action_export_report(self):
        company_ids = self.company_ids
        start_date = self.start_date
        end_date = self.end_date
        status = self.status
        periode = self.period
        main_category_id = self.main_category_id
        classification = self.classification
        pic_job_id = self.pic_job_id
        
        query_where = "WHERE 1=1"

        if company_ids:
            query_where += " AND branch.id = ANY(ARRAY%s)" % str(company_ids.mapped('id'))
        else:
            query_where += " AND branch.id = ANY(ARRAY%s)" % str(self.env.user.company_ids.mapped('id'))

        if start_date:
            query_where += " AND task.transaction_date >= '%s'" % start_date

        if end_date:
            query_where += " AND task.transaction_date <= '%s'" % end_date

        if status:
            if status == 'all':
                query_where += " AND task.state IN ('open','done')" 
            else:
                query_where += " AND task.state = '%s'" % status

        if main_category_id:
            query_where += " AND tbmc.id = %s" % main_category_id

        if classification:
            query_where += " AND tbc.classification = '%s'" % classification

        if pic_job_id:
            query_where += " AND job.id = %s" % pic_job_id

        if periode:
            query_where += " AND tbc.periode = '%s'" % periode

        query = """
            SELECT 
                branch.code as "Kode Cabang"
                , branch.name as "Nama Cabang"
                , task.transaction_date as "Tgl Transaksi"
                , task.due_date as "Deadline"
                , DATE_PART(
                    'day', 
                    (task.due_date + interval '7 hours') - (task.transaction_date + interval '7 hours')
                ) as "SLA Due Date"
                , task.done_date as "Tgl Penyelesaian"
                , tbmc."name" as "Main Category"
                , tbsc.name as "Sub Category"
                , tbc.name as "Sub Category 2"
                , CASE 
                    WHEN COALESCE(task.done_date, now() - interval '7 hours')::date - task.due_date::date < -3 THEN 'Current'
                    WHEN COALESCE(task.done_date, now() - interval '7 hours')::date - task.due_date::date BETWEEN -3 and 0 THEN 'Potensi OD'
                    WHEN COALESCE(task.done_date, now() - interval '7 hours')::date - task.due_date::date = 1 THEN 'Overdue H+1'
                    WHEN COALESCE(task.done_date, now() - interval '7 hours')::date - task.due_date::date > 1 THEN 'Overdue > H+1'
                    ELSE NULL
                END as "Umur Misi"
                , task.no_transaction as "No Transaksi"
                , tbc.periode as "Periode"
                , adh."name" as "NAMA ADH"
                , adh.registry_number as "NIP ADH"
                , pic."name" as "NAMA PIC"
                , pic.registry_number as "NIP PIC"
                , job."name" ->> 'en_US' as "PIC Job"
                , job2."name" ->> 'en_US' as "PIC Last Reminder"
                , '' as "Date Last Reminder"
                , '' as "Time Last Reminder"
                , '' as "Eskalasi ke Last Reminder"
                ,CASE 
                    WHEN task.state = 'done' THEN 'Done'
                    WHEN task.state in ('open','draft') THEN 'Not Done'
                    ELSE NULL 
                END AS status
                , '' as "Target Point"
                , '' as "Pengurangan Point"
                , '' as "Point Didapat"
            FROM tw_boom_task as task
            LEFT JOIN res_company branch on branch.id = task.company_id 
            LEFT JOIN tw_boom_category tbc on task.category_id = tbc.id
            LEFT JOIN tw_boom_main_category tbmc on tbmc.id = tbc.main_category_id 
            LEFT JOIN tw_boom_sub_category tbsc on tbsc.id = tbc.sub_category_id 
            LEFT JOIN hr_job as job on job.id = task.job_id 
            LEFT JOIN hr_job as job2 on job2.id = task.job_delegation_id 
            LEFT JOIN hr_employee as adh on (branch.id = adh.company_id and adh.job_title = 'ADMINISTRATION HEAD')
            LEFT JOIN hr_employee as pic on task.employee_id = pic.id 
            {query_where}
        """.format(query_where=query_where)
        
        self._cr.execute(query)
        result = self._cr.dictfetchall()
        if not result:
            raise Warning('Tidak ada data untuk di export')

        return self.env['web.report'].sudo().generate_report('Report Boom Task', result, show_total_footer=False)
    

    # 14: private methods

