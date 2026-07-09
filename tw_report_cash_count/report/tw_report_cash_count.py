# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, timedelta

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api

# 4: imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwReportCashCount(models.TransientModel):
    """
    Laporan Cash Count - Excel Report Wizard
    """
    _name = "tw.report.cash.count"
    _description = "Report Cash Count"

    # 7: defaults methods

    # 8: fields
    date = fields.Date(string='Tanggal', required=True)

    # 9: relation fields
    company_ids = fields.Many2many('res.company', string='Branch')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def _get_where_clause(self):
        """Build SQL WHERE clause for filtering"""
        query_where = "WHERE cc.state = 'posted'"

        # Date filter
        if self.date:
            query_where += f" AND cc.date = '{self.date}'"

        # Company filter
        if self.company_ids:
            company_ids = ', '.join(str(c.id) for c in self.company_ids)
            query_where += f" AND cc.company_id IN ({company_ids})"
        else:
            branch = self.env.user._get_company_ids()
            query_where += f" AND cc.company_id IN {str(tuple(branch)).replace(',)', ')')}"

        return query_where

    def action_print_report(self):
        """Main entry point for report generation"""
        self.ensure_one()

        query_where = self._get_where_clause()
        data = self._prepare_report_data(query_where)

        if not data:
            raise Warning("Tidak ada data Cash Count untuk tanggal dan cabang yang dipilih.")

        # Define header groups for multi-level header format
        header_groups = [
            {
                # No group name for first 2 columns
                'columns': [
                    {'key': 'KODE_CABANG', 'label': 'Kode Cabang', 'bg_color': '#FFFACD'},
                    {'key': 'NAMA_CABANG', 'label': 'Nama Cabang', 'bg_color': '#FFFACD'},
                ]
            },
            {
                'name': 'PUST',
                'bg_color': '#F0F322',  
                'columns': [
                    {'key': 'PUST_SR', 'label': 'Showroom', 'bg_color': '#F0F322'},
                    {'key': 'PUST_WS', 'label': 'Workshop', 'bg_color': '#F0F322'},
                ]
            },
            {
                'name': 'Petty Cash SR',
                'bg_color': '#8ACFAC',  
                'columns': [
                    {'key': 'PC_SR_PLAFON', 'label': 'Plafon'},
                    {'key': 'PC_SR_SALDO_FISIK', 'label': 'Saldo Fisik'},
                    {'key': 'PC_SR_SALDO_BANK_OUT', 'label': 'Saldo di Bank Out'},
                    {'key': 'PC_SR_REIMBURSE', 'label': 'Saldo Reimburse'},
                    {'key': 'PC_SR_OUTSTANDING', 'label': 'PC Outstanding'},
                    {'key': 'PC_SR_SELISIH', 'label': 'Selisih'},
                    {'key': 'PC_SR_PEMAKAIAN', 'label': 'Pemakaian (%)'},
                ]
            },
            {
                'name': 'Petty Cash WS',
                'bg_color': '#7CC6D1',  
                'columns': [
                    {'key': 'PC_WS_PLAFON', 'label': 'Plafon'},
                    {'key': 'PC_WS_SALDO_FISIK', 'label': 'Saldo Fisik'},
                    {'key': 'PC_WS_SALDO_BANK_OUT', 'label': 'Saldo di Bank Out'},
                    {'key': 'PC_WS_REIMBURSE', 'label': 'Saldo Reimburse'},
                    {'key': 'PC_WS_OUTSTANDING', 'label': 'PC Outstanding'},
                    {'key': 'PC_WS_SELISIH', 'label': 'Selisih'},
                    {'key': 'PC_WS_PEMAKAIAN', 'label': 'Pemakaian (%)'},
                ]
            },
            {
                'name': 'Petty Cash ATLBTL',
                'bg_color': '#FBB87A',  
                'columns': [
                    {'key': 'PC_ATL_PLAFON', 'label': 'Plafon'},
                    {'key': 'PC_ATL_SALDO_FISIK', 'label': 'Saldo Fisik'},
                    {'key': 'PC_ATL_SALDO_BANK_OUT', 'label': 'Saldo di Bank Out'},
                    {'key': 'PC_ATL_REIMBURSE', 'label': 'Saldo Reimburse'},
                    {'key': 'PC_ATL_OUTSTANDING', 'label': 'PC Outstanding'},
                    {'key': 'PC_ATL_SELISIH', 'label': 'Selisih'},
                    {'key': 'PC_ATL_PEMAKAIAN', 'label': 'Pemakaian (%)'},
                ]
            },
            {
                'columns': [
                    {'key': 'PENERIMAAN_LAIN', 'label': 'Penerimaan Lain', 'bg_color': '#DDDDDD'},
                    {'key': 'SALDO_BRANKAS', 'label': 'Saldo Brankas', 'bg_color': '#2ACDFF'},
                ]
            },
        ]

        return self.env['web.report'].generate_report(
            report_name='Laporan Cash Count',
            data=data,
            start_date=self.date,
            end_date=self.date,
            header_groups=header_groups,
            show_total_footer=True,
            numbering=False,
        )

    def _prepare_report_data(self, query_where):
        """Execute SQL query and prepare data as list of dictionaries"""
        query = """
            SELECT cash_count.company_id
            , cash_count.branch_code
            , cash_count.branch_name
            , cash_count.journal
            , COALESCE(plafon_petty_cash_sr,0) as plafon_petty_cash_sr
            , COALESCE(plafon_petty_cash_ws,0) as plafon_petty_cash_ws
            , COALESCE(plafon_petty_cash_atl_btl,0) as plafon_petty_cash_atl_btl
            , COALESCE(physical_petty_cash_sr,0) as physical_petty_cash_sr
            , COALESCE(physical_petty_cash_ws,0) as physical_petty_cash_ws
            , COALESCE(physical_petty_cash_atl_btl,0) as physical_petty_cash_atl_btl
            , COALESCE(balance_pc_sr,0) as balance_pc_sr
            , COALESCE(balance_pc_ws,0) as balance_pc_ws
            , COALESCE(balance_pc_atl_btl,0) as balance_pc_atl_btl
            , COALESCE(cash_sr.amount,0) as cash_sr_amount
            , COALESCE(cash_ws.amount,0) as cash_ws_amount
            , COALESCE(cash_pos_sr.amount,0) as cash_pos_sr_amount
            , COALESCE(cash_pos_ws.amount,0) as cash_pos_ws_amount
            , COALESCE(petty_cash_sr.amount,0) as petty_cash_sr_amount
            , COALESCE(petty_cash_ws.amount,0) as petty_cash_ws_amount
            , COALESCE(petty_cash_pos_sr.amount,0) as petty_cash_pos_sr_amount
            , COALESCE(petty_cash_pos_ws.amount,0) as petty_cash_pos_ws_amount
            , COALESCE(petty_cash_atl.amount,0) as petty_cash_atl_amount
            , COALESCE(reimburse_petty_cash_sr.amount,0) as reimburse_petty_cash_sr_amount
            , COALESCE(reimburse_petty_cash_ws.amount,0) as reimburse_petty_cash_ws_amount
            , COALESCE(reimburse_petty_cash_pos_sr.amount,0) as reimburse_petty_cash_pos_sr_amount
            , COALESCE(reimburse_petty_cash_pos_ws.amount,0) as reimburse_petty_cash_pos_ws_amount
            , COALESCE(reimburse_petty_cash_atl.amount,0) as reimburse_petty_cash_atl_amount
            , COALESCE(penerimaan_lain.amount,0) as penerimaan_lain_amount
            FROM (
                SELECT cc.id
                , b.id as company_id
                , b.code as branch_code
                , b.name as branch_name
                , cc.plafon_petty_cash_sr
                , cc.plafon_petty_cash_ws
                , cc.plafon_petty_cash_atl_btl
                , cc.physical_petty_cash_sr
                , cc.physical_petty_cash_ws
                , cc.physical_petty_cash_atl_btl
                , cc.balance_pc_sr
                , cc.balance_pc_ws
                , cc.balance_pc_atl_btl
                , cd.journal 
                FROM tw_cash_count cc
                INNER JOIN tw_cash_count_line cd ON cc.id = cd.cash_count_id
                INNER JOIN res_company b ON b.id = cc.company_id
                %(query_where)s
                GROUP BY cd.journal,cc.id,b.id
                ORDER BY journal ASC
            ) cash_count
            LEFT JOIN (
                SELECT cash_count_id, journal, SUM(amount) as amount
                FROM tw_cash_count cc
                INNER JOIN tw_cash_count_line cd ON cd.cash_count_id = cc.id 
                LEFT JOIN tw_cash_count_validation cv ON cv.id = cd.validation_id
                %(query_where)s 
                AND cd.type = 'cash' AND journal ilike '%%POS%%' AND journal ilike '%%SR%%'
                AND cv.name = 'Belum disetor ke bank'
                GROUP BY cash_count_id, journal
            ) cash_pos_sr ON cash_pos_sr.cash_count_id = cash_count.id AND cash_pos_sr.journal = cash_count.journal
            LEFT JOIN (
                SELECT cash_count_id, journal, SUM(amount) as amount
                FROM tw_cash_count cc
                INNER JOIN tw_cash_count_line cd ON cd.cash_count_id = cc.id
                LEFT JOIN tw_cash_count_validation cv ON cv.id = cd.validation_id
                %(query_where)s 
                AND cd.type = 'cash' AND journal ilike '%%POS%%' AND journal ilike '%%WS%%'
                AND cv.name = 'Belum disetor ke bank'
                GROUP BY cash_count_id, journal
            ) cash_pos_ws ON cash_pos_ws.cash_count_id = cash_count.id AND cash_pos_ws.journal = cash_count.journal
            LEFT JOIN (
                SELECT cash_count_id, journal, SUM(amount) as amount
                FROM tw_cash_count cc
                INNER JOIN tw_cash_count_line cd ON cd.cash_count_id = cc.id
                LEFT JOIN tw_cash_count_validation cv ON cv.id = cd.validation_id
                %(query_where)s
                AND cd.type = 'cash' AND journal not ilike '%%POS%%' AND journal ilike '%%SR%%'
                AND cv.name = 'Belum disetor ke bank'
                GROUP BY cash_count_id, journal
            ) cash_sr ON cash_sr.cash_count_id = cash_count.id AND cash_sr.journal = cash_count.journal
            LEFT JOIN (
                SELECT cash_count_id, journal, SUM(amount) as amount
                FROM tw_cash_count cc
                INNER JOIN tw_cash_count_line cd ON cd.cash_count_id = cc.id
                LEFT JOIN tw_cash_count_validation cv ON cv.id = cd.validation_id
                %(query_where)s 
                AND cd.type = 'cash' AND journal not ilike '%%POS%%' AND journal ilike '%%WS%%'
                AND cv.name = 'Belum disetor ke bank'
                GROUP BY cash_count_id, journal
            ) cash_ws ON cash_ws.cash_count_id = cash_count.id AND cash_ws.journal = cash_count.journal
            LEFT JOIN (
                SELECT cash_count_id, journal, SUM(amount) as amount
                FROM tw_cash_count cc
                INNER JOIN tw_cash_count_line cd ON cd.cash_count_id = cc.id
                %(query_where)s 
                AND cd.type = 'petty_cash' AND journal not ilike '%%POS%%' AND journal ilike '%%SR%%'
                GROUP BY cash_count_id, journal
            ) petty_cash_sr ON petty_cash_sr.cash_count_id = cash_count.id AND petty_cash_sr.journal = cash_count.journal
            LEFT JOIN (
                SELECT cash_count_id, journal, SUM(amount) as amount
                FROM tw_cash_count cc
                INNER JOIN tw_cash_count_line cd ON cd.cash_count_id = cc.id
                %(query_where)s 
                AND cd.type = 'petty_cash' AND journal not ilike '%%POS%%' AND journal ilike '%%WS%%'
                GROUP BY cash_count_id, journal
            ) petty_cash_ws ON petty_cash_ws.cash_count_id = cash_count.id AND petty_cash_ws.journal = cash_count.journal
            LEFT JOIN (
                SELECT cash_count_id, journal, SUM(amount) as amount
                FROM tw_cash_count cc
                INNER JOIN tw_cash_count_line cd ON cd.cash_count_id = cc.id 
                %(query_where)s 
                AND cd.type = 'petty_cash' AND journal ilike '%%POS%%' AND journal ilike '%%SR%%'
                GROUP BY cash_count_id, journal
            ) petty_cash_pos_sr ON petty_cash_pos_sr.cash_count_id = cash_count.id AND petty_cash_pos_sr.journal = cash_count.journal
            LEFT JOIN (
                SELECT cash_count_id, journal, SUM(amount) as amount
                FROM tw_cash_count cc
                INNER JOIN tw_cash_count_line cd ON cd.cash_count_id = cc.id
                %(query_where)s 
                AND cd.type = 'petty_cash' AND journal ilike '%%POS%%' AND journal ilike '%%WS%%'
                GROUP BY cash_count_id, journal
            ) petty_cash_pos_ws ON petty_cash_pos_ws.cash_count_id = cash_count.id AND petty_cash_pos_ws.journal = cash_count.journal
            LEFT JOIN (
                SELECT cash_count_id, journal, SUM(amount) as amount
                FROM tw_cash_count cc
                INNER JOIN tw_cash_count_line cd ON cd.cash_count_id = cc.id 
                %(query_where)s 
                AND cd.type = 'petty_cash' AND journal ilike '%%ATLBTL%%'
                GROUP BY cash_count_id, journal
            ) petty_cash_atl ON petty_cash_atl.cash_count_id = cash_count.id AND petty_cash_atl.journal = cash_count.journal
            LEFT JOIN (
                SELECT cash_count_id, journal, SUM(amount) as amount
                FROM tw_cash_count cc
                INNER JOIN tw_cash_count_line cd ON cd.cash_count_id = cc.id 
                %(query_where)s 
                AND cd.type = 'reimburse_petty_cash' AND journal not ilike '%%POS%%' AND journal ilike '%%SR%%'
                GROUP BY cash_count_id, journal
            ) reimburse_petty_cash_sr ON reimburse_petty_cash_sr.cash_count_id = cash_count.id AND reimburse_petty_cash_sr.journal = cash_count.journal
            LEFT JOIN (
                SELECT cash_count_id, journal, SUM(amount) as amount
                FROM tw_cash_count cc
                INNER JOIN tw_cash_count_line cd ON cd.cash_count_id = cc.id 
                %(query_where)s 
                AND cd.type = 'reimburse_petty_cash' AND journal not ilike '%%POS%%' AND journal ilike '%%WS%%'
                GROUP BY cash_count_id, journal
            ) reimburse_petty_cash_ws ON reimburse_petty_cash_ws.cash_count_id = cash_count.id AND reimburse_petty_cash_ws.journal = cash_count.journal
            LEFT JOIN (
                SELECT cash_count_id, journal, SUM(amount) as amount
                FROM tw_cash_count cc
                INNER JOIN tw_cash_count_line cd ON cd.cash_count_id = cc.id 
                %(query_where)s 
                AND cd.type = 'reimburse_petty_cash' AND journal ilike '%%POS%%' AND journal ilike '%%SR%%'
                GROUP BY cash_count_id, journal
            ) reimburse_petty_cash_pos_sr ON reimburse_petty_cash_pos_sr.cash_count_id = cash_count.id AND reimburse_petty_cash_pos_sr.journal = cash_count.journal
            LEFT JOIN (
                SELECT cash_count_id, journal, SUM(amount) as amount
                FROM tw_cash_count cc
                INNER JOIN tw_cash_count_line cd ON cd.cash_count_id = cc.id
                %(query_where)s 
                AND cd.type = 'reimburse_petty_cash' AND journal ilike '%%POS%%' AND journal ilike '%%WS%%'
                GROUP BY cash_count_id, journal
            ) reimburse_petty_cash_pos_ws ON reimburse_petty_cash_pos_ws.cash_count_id = cash_count.id AND reimburse_petty_cash_pos_ws.journal = cash_count.journal
            LEFT JOIN (
                SELECT cash_count_id, journal, SUM(amount) as amount
                FROM tw_cash_count cc
                INNER JOIN tw_cash_count_line cd ON cd.cash_count_id = cc.id 
                %(query_where)s 
                AND cd.type = 'reimburse_petty_cash' AND journal ilike '%%ATLBTL%%'
                GROUP BY cash_count_id, journal
            ) reimburse_petty_cash_atl ON reimburse_petty_cash_atl.cash_count_id = cash_count.id AND reimburse_petty_cash_atl.journal = cash_count.journal
            LEFT JOIN (
                SELECT COALESCE(sum(amount),0) as amount, cc.id as cash_count_id
                FROM tw_cash_count cc
                INNER JOIN tw_cash_count_other co ON co.cash_count_id = cc.id
                WHERE cc.state = 'posted' 
                GROUP BY cc.id
            ) penerimaan_lain ON penerimaan_lain.cash_count_id = cash_count.id
        ORDER BY branch_code, journal ASC    
        """ % {'query_where': query_where}

        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()

        # Process and aggregate results into flat structure for web.report
        result = {}
        for res in ress:
            branch_code = res.get('branch_code')
            branch_name = res.get('branch_name')
            journal = res.get('journal') or ''

            # Identify POS or non-POS branch type
            branch_type = branch_name
            if 'POS' in journal:
                branch_type = f"{branch_name} - POS"

            # Key for result grouping
            cabang_journal = f"{branch_code}|{branch_type}"

            if cabang_journal not in result:
                result[cabang_journal] = {
                    'branch_code': branch_code,
                    'branch_name': branch_type,
                    # PUST
                    'pust_sr': res.get('cash_pos_sr_amount') if 'POS' in journal else res.get('cash_sr_amount'),
                    'pust_ws': res.get('cash_pos_ws_amount') if 'POS' in journal else res.get('cash_ws_amount'),
                    # PETTY CASH SR
                    'pc_sr_plafon': res.get('plafon_petty_cash_sr') if 'POS' not in journal else 0,
                    'pc_sr_saldo_fisik': res.get('physical_petty_cash_sr') if 'POS' not in journal else 0,
                    'pc_sr_saldo_bank_out': res.get('balance_pc_sr') if 'POS' not in journal else 0,
                    'pc_sr_saldo_reimburse': res.get('reimburse_petty_cash_sr_amount'),
                    'pc_sr_outstanding': res.get('petty_cash_sr_amount'),
                    # PETTY CASH WS
                    'pc_ws_plafon': res.get('plafon_petty_cash_ws') if 'POS' not in journal else 0,
                    'pc_ws_saldo_fisik': res.get('physical_petty_cash_ws') if 'POS' not in journal else 0,
                    'pc_ws_saldo_bank_out': res.get('balance_pc_ws') if 'POS' not in journal else 0,
                    'pc_ws_saldo_reimburse': res.get('reimburse_petty_cash_ws_amount'),
                    'pc_ws_outstanding': res.get('petty_cash_ws_amount'),
                    # PETTY CASH ATL/BTL
                    'pc_atl_plafon': res.get('plafon_petty_cash_atl_btl') if 'POS' not in journal else 0,
                    'pc_atl_saldo_fisik': res.get('physical_petty_cash_atl_btl') if 'POS' not in journal else 0,
                    'pc_atl_saldo_bank_out': res.get('balance_pc_atl_btl') if 'POS' not in journal else 0,
                    'pc_atl_saldo_reimburse': res.get('reimburse_petty_cash_atl_amount'),
                    'pc_atl_outstanding': res.get('petty_cash_atl_amount'),
                    # Penerimaan Lain
                    'saldo_penerimaan_lain': res.get('penerimaan_lain_amount'),
                }
            else:
                # Aggregate
                result[cabang_journal]['pust_sr'] += res.get('cash_pos_sr_amount') if 'POS' in journal else res.get('cash_sr_amount')
                result[cabang_journal]['pust_ws'] += res.get('cash_pos_ws_amount') if 'POS' in journal else res.get('cash_ws_amount')
                result[cabang_journal]['pc_sr_saldo_reimburse'] += res.get('reimburse_petty_cash_sr_amount')
                result[cabang_journal]['pc_sr_outstanding'] += res.get('petty_cash_sr_amount')
                result[cabang_journal]['pc_ws_saldo_reimburse'] += res.get('reimburse_petty_cash_ws_amount')
                result[cabang_journal]['pc_ws_outstanding'] += res.get('petty_cash_ws_amount')
                result[cabang_journal]['pc_atl_saldo_reimburse'] += res.get('reimburse_petty_cash_atl_amount')
                result[cabang_journal]['pc_atl_outstanding'] += res.get('petty_cash_atl_amount')

        # Convert to list of dictionaries with calculated fields for web.report
        data = []
        for r in result.values():
            # Calculate SR
            pc_sr_plafon = r.get('pc_sr_plafon', 0)
            pc_sr_saldo_fisik = r.get('pc_sr_saldo_fisik', 0)
            pc_sr_saldo_bank_out = r.get('pc_sr_saldo_bank_out', 0)
            pc_sr_saldo_reimburse = r.get('pc_sr_saldo_reimburse', 0)
            pc_sr_outstanding = r.get('pc_sr_outstanding', 0)
            pc_sr_selisih = pc_sr_plafon - pc_sr_saldo_fisik - pc_sr_saldo_bank_out - pc_sr_saldo_reimburse - pc_sr_outstanding
            pc_sr_pemakaian = (pc_sr_saldo_reimburse + pc_sr_outstanding) / pc_sr_plafon if pc_sr_plafon > 0 else 0

            # Calculate WS
            pc_ws_plafon = r.get('pc_ws_plafon', 0)
            pc_ws_saldo_fisik = r.get('pc_ws_saldo_fisik', 0)
            pc_ws_saldo_bank_out = r.get('pc_ws_saldo_bank_out', 0)
            pc_ws_saldo_reimburse = r.get('pc_ws_saldo_reimburse', 0)
            pc_ws_outstanding = r.get('pc_ws_outstanding', 0)
            pc_ws_selisih = pc_ws_plafon - pc_ws_saldo_fisik - pc_ws_saldo_bank_out - pc_ws_saldo_reimburse - pc_ws_outstanding
            pc_ws_pemakaian = (pc_ws_saldo_reimburse + pc_ws_outstanding) / pc_ws_plafon if pc_ws_plafon > 0 else 0

            # Calculate ATL
            pc_atl_plafon = r.get('pc_atl_plafon', 0)
            pc_atl_saldo_fisik = r.get('pc_atl_saldo_fisik', 0)
            pc_atl_saldo_bank_out = r.get('pc_atl_saldo_bank_out', 0)
            pc_atl_saldo_reimburse = r.get('pc_atl_saldo_reimburse', 0)
            pc_atl_outstanding = r.get('pc_atl_outstanding', 0)
            pc_atl_selisih = pc_atl_plafon - pc_atl_saldo_fisik - pc_atl_saldo_bank_out - pc_atl_saldo_reimburse - pc_atl_outstanding
            pc_atl_pemakaian = (pc_atl_saldo_reimburse + pc_atl_outstanding) / pc_atl_plafon if pc_atl_plafon > 0 else 0

            # PUST and others
            pust_sr = r.get('pust_sr', 0)
            pust_ws = r.get('pust_ws', 0)
            saldo_penerimaan_lain = r.get('saldo_penerimaan_lain', 0)
            saldo_brankas = pust_sr + pust_ws + pc_sr_saldo_fisik + pc_ws_saldo_fisik + pc_atl_saldo_fisik + saldo_penerimaan_lain

            data.append({
                'KODE_CABANG': r.get('branch_code', ''),
                'NAMA_CABANG': r.get('branch_name', ''),
                # PUST
                'PUST_SR': pust_sr,
                'PUST_WS': pust_ws,
                # Petty Cash SR
                'PC_SR_PLAFON': pc_sr_plafon,
                'PC_SR_SALDO_FISIK': pc_sr_saldo_fisik,
                'PC_SR_SALDO_BANK_OUT': pc_sr_saldo_bank_out,
                'PC_SR_REIMBURSE': pc_sr_saldo_reimburse,
                'PC_SR_OUTSTANDING': pc_sr_outstanding,
                'PC_SR_SELISIH': pc_sr_selisih,
                'PC_SR_PEMAKAIAN': pc_sr_pemakaian,
                # Petty Cash WS
                'PC_WS_PLAFON': pc_ws_plafon,
                'PC_WS_SALDO_FISIK': pc_ws_saldo_fisik,
                'PC_WS_SALDO_BANK_OUT': pc_ws_saldo_bank_out,
                'PC_WS_REIMBURSE': pc_ws_saldo_reimburse,
                'PC_WS_OUTSTANDING': pc_ws_outstanding,
                'PC_WS_SELISIH': pc_ws_selisih,
                'PC_WS_PEMAKAIAN': pc_ws_pemakaian,
                # Petty Cash ATL/BTL
                'PC_ATL_PLAFON': pc_atl_plafon,
                'PC_ATL_SALDO_FISIK': pc_atl_saldo_fisik,
                'PC_ATL_SALDO_BANK_OUT': pc_atl_saldo_bank_out,
                'PC_ATL_REIMBURSE': pc_atl_saldo_reimburse,
                'PC_ATL_OUTSTANDING': pc_atl_outstanding,
                'PC_ATL_SELISIH': pc_atl_selisih,
                'PC_ATL_PEMAKAIAN': pc_atl_pemakaian,
                # Others
                'PENERIMAAN_LAIN': saldo_penerimaan_lain,
                'SALDO_BRANKAS': saldo_brankas,
            })

        return data

    # 14: Private Methods
