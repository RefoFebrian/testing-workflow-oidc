# -*- coding: utf-8 -*-

# 1: imports of python lib
import base64
import re
import xlsxwriter
import calendar
from io import StringIO, BytesIO
from datetime import date, datetime, time, timedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwReportPerformanceExpedition(models.TransientModel):
    _name = "tw.report.performance.expedition"
    _description = "TW Report Performance Expedition"

    # 7: defaults methods
    def _get_company_domain(self):
        company_id = self.env['res.company'].get_default_main_dealer()
        if company_id:
            return [('id', '=', company_id.id)]
        else:
            parent_id = self.env.company.parent_id.id or self.env.company.id
            return [('id', 'child_of', parent_id)]

    # 8: fields
    start_date = fields.Date('Start Date', required=True, default=fields.Date.context_today)
    end_date = fields.Date('End Date', required=True, default=fields.Date.context_today)
    division = fields.Selection([
        ('Unit', 'Unit'),
        ('Sparepart', 'Sparepart')
    ], string='Division', default='Unit')

    # 9: relation fields
    company_id = fields.Many2one('res.company', string='Branch', domain=_get_company_domain)

    # 10: constraints & sql constraints
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise Warning(_('End Date harus lebih besar dari Start Date.'))

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_generate_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        return self._generate_report_performance_expedition()
    
    # 14: private methods
    def _generate_report_performance_expedition(self):
        filename = f'report_performance_expedition_{self.division.lower() if self.division else "all"}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        data_res = self._get_data_performance_expedition()

        summary_header = {
            'A1': self.company_id.name or self.env.company.name,
            'A2': f'Report Performance Expedisi {self.division or ""}',
            'A3': f"Tanggal : {self.start_date or '-'} s/d {self.end_date or '-'}"
        }

        return self.env['web.report'].sudo().generate_report(
            filename,
            data_res,
            data_summary_header=summary_header,
            data_summary_header_col_size=False,
            freeze_panes_column=3,
            return_fp=False
        )

    def _get_data_performance_expedition(self):
        branch_id = self.company_id.id
        start_date = self.start_date
        end_date = self.end_date
        division = self.division

        query_where = " WHERE 1=1 "

        if branch_id:
            query_where += " AND pick.company_id = %s " % branch_id
        if start_date:
            query_where += " AND pick.validate_date >= '%s' " % start_date
        if end_date:
            query_where += " AND pick.validate_date <= '%s' " % end_date

        if division == 'Unit':
            query_select = """
                SELECT DISTINCT
                    lot.name as engine_no,
                    lot.chassis_number as chassis_no,
                    lot.ship_list_number as no_shipping_list,
                    to_char(lot.ship_list_date, 'YYYY-MM-DD') as tgl_shipping_list,
                    batch.name as no_packing,
                    to_char(pick.validate_date, 'YYYY-MM-DD') as tgl_packing,
                    partner.name as expedisi,
                    (date(pick.validate_date) - date(lot.ship_list_date))::varchar || ' hari' as performance
            """
            query_join = """
                JOIN stock_move_line move_line ON move_line.move_id = move.id
                JOIN stock_lot lot ON move_line.lot_id = lot.id
                JOIN stock_picking_batch batch ON batch.id = pick.batch_id
            """
        else:
            query_select = """
                SELECT DISTINCT
                    pp.default_code as kode_sparepart,
                    pt.name->>'en_US' as description,
                    pick.mft_reference as no_packing_sheet,
                    to_char(to_date(ps.tanggal_ps, 'DDMMYYYY'), 'YYYY-MM-DD') as tgl_packing_sheet,
                    pick.name as no_picking,
                    to_char(pick.validate_date, 'YYYY-MM-DD') as tgl_picking,
                    partner.name as expedisi,
                    (date(pick.validate_date) - to_date(ps.tanggal_ps, 'DDMMYYYY'))::varchar || ' hari' as performance
            """
            query_join = """
                JOIN (
                    SELECT
                        c_kode.value as kode_ps,
                        MAX(c_tgl.value) as tanggal_ps
                    FROM tw_b2b_file tbf
                    JOIN tw_b2b_file_content tbfc ON tbfc.file_id = tbf.id
                    JOIN tw_b2b_file_content_line c_kode ON c_kode.file_content_id = tbfc.id AND c_kode.name = 'kode_ps'
                    JOIN tw_b2b_file_content_line c_tgl ON c_tgl.file_content_id = tbfc.id AND c_tgl.name = 'tanggal_ps'
                    WHERE tbf.ext = 'PS' AND tbf.state = 'done'
                    GROUP BY c_kode.value
                ) ps ON ps.kode_ps = pick.mft_reference
                JOIN product_product pp ON move.product_id = pp.id
                JOIN product_template pt ON pp.product_tmpl_id = pt.id
            """

        query = f"""
            {query_select}
            FROM stock_picking pick
            JOIN stock_move move ON move.picking_id = pick.id
            JOIN tw_stock_inbound inbound ON inbound.id = pick.stock_inbound_id
            JOIN res_partner partner ON partner.id = inbound.expedition_id
            {query_join}
            {query_where}
            AND pick.division = '{division}'
        """

        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()
            
        return ress
