# 1: imports of python lib
from datetime import datetime, date, timedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwB2BeMeteraiReport(models.TransientModel):
    _name = "tw.b2b.emeterai.report"
    _description = 'Laporan Penggunaan e-Meterai'

    # 7: defaults methods
    def _get_default_branch(self):
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1 :
            return [company_ids[0].id]
        return []
    
    def _get_default_datetime(self):
        return datetime.now()
    
    def _get_default_start_date(self):
        return date.today().replace(day=1)

    wbf = {}

    # 8: fields
    name = fields.Char('Filename', readonly=True)
    state_x = fields.Selection((
        ('choose', 'choose'),
        ('get', 'get')
    ), default=lambda *a: 'choose')
    start_date = fields.Date('Start Date', default=_get_default_start_date)
    end_date = fields.Date('End Date', default=_get_default_datetime)
    data_x = fields.Binary('File', readonly=True)

    # 9: relation fields
    company_ids = fields.Many2many(comodel_name='res.company', relation='tw_b2b_emeterai_report_company_rel', column1='b2b_emeterai_report_id', column2='company_id', string='Branch', copy=False, default=_get_default_branch, domain=[('parent_id','!=',False)])

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    
    # 13: action methods
    def action_b2b_emeterai_report_tree(self):
        domain = []
        name = 'Laporan Penggunaan e-Meterai'
        path = 'laporan-penggunaan-emeterai'
        form_view_id = self.env.ref('tw_b2b_emeterai.tw_b2b_emeterai_report_wizard_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'path': path,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'tw.b2b.emeterai.report',
            'domain': domain,
            'views': [(form_view_id, 'form')],
            'context': {
                'search_default_fieldname': 1,
                'readonly_by_pass': 1
            },
        }
    
    def action_export(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        return self._print_export_b2b_emeterai_report()
        
    # 14: private methods
    def _print_export_b2b_emeterai_report(self):
        emet_config_obj = self.env['tw.b2b.emeterai'].sudo()._get_peruri_config_api()
        try:
            emet_config_obj.action_check_limit_quota_stamp_peruri()
            balance_emeterai = self.env['ir.config_parameter'].sudo().search([
                ('key','=','peruri.saldo')
            ], limit=1).value
        except Exception as e:
            balance_emeterai = 0

        filename = 'Laporan Penggunaan e-Meterai'
        summary_header = {
            'A4': 'Saldo :',
            'B4': balance_emeterai
        }

        query_where = ''
        if self.company_ids:
            query_where += f" AND branch IN ({', '.join(str(b.id) for b in self.company_ids)})"
        else:
            branch = self.env.user._get_company_ids()
            query_where += f" AND branch IN {str(tuple(branch)).replace(',)', ')')}"

        
        if self.start_date:
            query_where += f" AND tbe.date >= '{self.start_date}'"
        if self.end_date:
            query_where += f" AND tbe.date <= '{self.end_date}'"
        
        query = f"""
            SELECT
                tbe.transaction_name "Nomor Document"
                , im.name ->> 'en_US' "Type"
                , tbe.amount "Nominal Transaksi"
                , branch.name "Cabang"
                , TO_CHAR(tbe.create_date + INTERVAL '7 hours', 'YYYY-MM-DD HH24:MI:SS') "Created On"
                , COALESCE(tbe.stamped_file_id, '') "Stamp File ID"
                , COALESCE(tbe.stamped_serial_number, '') "Stamped Serial Number"
                , CASE
                    WHEN tbe.stamped_status = 'STAMP' THEN UPPER(tbe.stamped_status)
                    WHEN tbe.stamped_status = 'NOTSTAMP' THEN UPPER(tbe.stamped_status)
                    ELSE ''
                END "State E-Meterai"
            FROM tw_b2b_emeterai tbe
            LEFT JOIN res_company branch ON tbe.company_id = branch.id
            LEFT JOIN ir_model im ON tbe.model_id = im.id
            WHERE 1=1
            AND tbe.stamped_file_id IS NOT NULL
            {query_where}
        """
        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()

        return self.env['web.report'].sudo().generate_report(
            filename,
            ress,
            start_date=self.start_date,
            end_date=self.end_date,
            data_summary_header=summary_header
        )
    
    