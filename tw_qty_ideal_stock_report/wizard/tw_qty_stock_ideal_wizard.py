# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
import logging
_logger = logging.getLogger(__name__)

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api
from odoo.exceptions import UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TWQtyIdealStockWizard(models.TransientModel):
    _name = "tw.qty.ideal.stock.wizard"
    _description = "Qty Ideal Stock Wizard"

    # 7: defaults methods
    def _get_default_date(self): 
        return datetime.now()

    def _get_year(self):
        current_year = datetime.now().year
        start_year = 2020
        years_available = []

        for x in reversed(range(start_year, current_year + 1)):
            elem = ("{}".format(x), "{}".format(x))
            years_available.append(elem)

        return years_available

    # 8: fields
    month = fields.Selection([
		('1','Januari'),
		('2','Februari'),
		('3','Maret'),
		('4','April'),
		('5','Mei'),
		('6','Juni'),
		('7','Juli'),
		('8','Agustus'),
		('9','September'),
		('10','Oktober'),
		('11','November'),
		('12','Desember')
	],'Bulan')
    year = fields.Selection(_get_year,'Tahun')

    # 9: relation fields
    data_ids = fields.One2many('tw.qty.ideal.stock.wizard.line','wizard_id')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_export(self):
        return self.excel_report(self._read_source()[1])

    def action_open_view(self):
        data_ids = self._read_source()[0]
        form_id = self.env.ref('tw_qty_ideal_stock_report.tw_qty_stock_ideal_view_wizard').id
        return {
            'name': 'Laporan Qty Ideal Stock',
            'view_mode': 'form',
            'res_model': 'tw.qty.ideal.stock.wizard',
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_data_ids': data_ids}
        }

    def action_generate_data(self):
        # ****************** INPUT CHECK ******************
        if not self.month or not self.year:
            raise Warning ('Untuk generate data, kolom Bulan dan Tahun HARUS terisi !')
        if not self.year.isdigit():
            raise Warning ('Tahun harus berupa angka !')
        now = self._get_default_date()
        min_date = (now - relativedelta(months=6)).replace(day=1,hour=0,minute=0,second=0,microsecond=0)
        max_date = now.replace(day=1,hour=0,minute=0,second=0,microsecond=0)
        target_date = datetime(int(self.year),int(self.month),1)
        if target_date < min_date or target_date >= max_date:
            raise Warning ('Hanya dapat mengambil data 6 bulan terakhir !')

        # ****************** FETCH DATA ******************
        config = self._config_check()
        query = """
            SELECT
                COALESCE(branch_code,'')
                ||'_'|| COALESCE(branch_name,'')
                ||'_'|| COALESCE(prod_code,'')
                ||'_'|| COALESCE(prod_name,'')
                ||'_'|| COALESCE(prod_categ_name,'')
                AS key
            ,   SUM(COALESCE(qty,0))
            FROM (
                SELECT
                    b.code AS branch_code
                ,   b.name AS branch_name
                ,   prod_template.name->>'en_US' AS prod_code
                ,   product.default_code AS prod_name
                ,   prod_category.name AS prod_categ_name
                ,   SUM(wol.qty_delivered) AS qty
                FROM tw_work_order wo
                INNER JOIN account_move ai ON wo.name = ai.invoice_origin 
                LEFT JOIN tw_work_order_line wol ON wo.id = wol.order_id
                LEFT JOIN res_company b ON wo.company_id = b.id
                LEFT JOIN product_product product ON wol.product_id = product.id
                LEFT JOIN product_template prod_template ON product.product_tmpl_id = prod_template.id
                LEFT JOIN product_category prod_category ON prod_template.categ_id = prod_category.id 
                WHERE wol.division = 'Sparepart'
                AND EXTRACT(MONTH FROM wo.open_date) = {month}
                AND EXTRACT(YEAR FROM wo.open_date) = {year}
                AND wo.state IN ('sale','done')
                GROUP BY b.id,product.id,prod_category.id,prod_template.name
                UNION
                SELECT
                    b.code AS branch_code
                ,   b.name AS branch_name
                ,   prod_template.name->>'en_US' AS prod_code
                ,   product.default_code AS prod_name
                ,   prod_category.name AS prod_categ_name
                ,   -1 * SUM(wol.qty_delivered) AS qty
                FROM tw_work_order_cancel woc
                INNER JOIN tw_work_order wo ON woc.work_order_id = wo.id 
                INNER JOIN account_move ai ON wo.name = ai.invoice_origin
                INNER JOIN tw_cancellation tc ON tc.id = woc.cancellation_id
                LEFT JOIN tw_work_order_line wol ON wo.id = wol.order_id
                LEFT JOIN res_company b ON wo.company_id = b.id
                LEFT JOIN product_product product ON wol.product_id = product.id
                LEFT JOIN product_template prod_template ON product.product_tmpl_id = prod_template.id
                LEFT JOIN product_category prod_category ON prod_template.categ_id = prod_category.id
                WHERE wol.division = 'Sparepart'
                AND EXTRACT(MONTH FROM tc.date) = {month}
                AND EXTRACT(YEAR FROM tc.date) = {year}
                AND tc.state = 'confirmed'
                GROUP BY b.id,product.id,prod_category.id,prod_code
                ORDER BY branch_code,prod_code
            ) data
            GROUP BY branch_code,branch_name,prod_code,prod_categ_name,prod_name
        """.format(
            month=self.month,
            year=self.year,
        )
        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        if not ress:
            raise Warning ('Tidak ada data !')

        all_datas = ''.join('%s:%s\n' % (res['key'],int(res['sum'])) for res in ress)

        # ****************** WRITE TO SOURCE FILE ******************
        source_file = "%s/QTY_IDEAL %s.qis" % (config.local_path,self.month+'_'+self.year)
        with open(source_file, 'w') as f:
            f.write(all_datas)
        _logger.info('Data QTY IDEAL STOCK %s %s exported successfully !' % (self.month,self.year))

        new_data_ids = self._read_source()[0]

        return {
            'name': 'Laporan Qty Ideal Stock',
            'view_mode': 'form',
            'res_model': 'tw.qty.ideal.stock.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_data_ids': new_data_ids}
        }  

    # 14: private methods
    def _query_stock_sparepart(self,**kwargs):
        """
        This function takes params for requesting query string.
        And it intends to be modular, so that can be called by
        another modules such as restapi and generating excel report
        """
        
        categ_ids = kwargs['categ_ids'] if 'categ_ids' in kwargs else None
        year = kwargs['year'] if 'year' in kwargs else None
        tz = '7 hours'
        
        query_where = ""
        remark = ''

        year = str(year)
        
        if categ_ids :
            query_where += " AND pc.id in %s" % str(tuple(categ_ids)).replace(',)', ')')

        query = """
            SELECT
            series.series
            , branch.code AS branch
            , pt.name->>'en_US' AS kode_part
            , product.default_code AS nama_part
            , pc.name AS kat
            , count(wol.id)::int AS total_per_bulan
            , CASE 
                WHEN count(wol.id) >= 12 THEN 'A'
                WHEN count(wol.id) >= 9 THEN 'B'
                WHEN count(wol.id) >= 5 THEN 'C'
                WHEN count(wol.id) >= 1 THEN 'D'
                ELSE 'E'
                END AS rank
            FROM 
                generate_series(1,12,1) AS series
            LEFT JOIN tw_work_order AS wo on EXTRACT(MONTH FROM (wo.confirm_date + interval '7 hours')) = series
            LEFT JOIN tw_work_order_line wol ON wo.id = wol.order_id
            LEFT JOIN product_product product ON product.id = wol.product_id
            LEFT JOIN product_template pt ON pt.id = product.product_tmpl_id
            LEFT JOIN res_company branch ON branch.id = wo.company_id
            LEFT JOIN product_category pc ON pc.id = pt.categ_id
            WHERE 1=1 %s
            AND wo.date BETWEEN date_trunc('month', current_date - interval '12 month') AND date_trunc('month', current_date) - interval '1 days'
            GROUP BY series.series, branch.id, product.id, pt.id, pc.id
            ORDER BY series.series
            """ % (query_where)
        
        return query

    def _get_ranks(self):
        categ_query = """
            select
            coalesce(pc3.id,coalesce(pc2.id,coalesce(pc1.id,null))) AS id
            from product_category pc1
            left join product_category pc2 on pc2.parent_id = pc1.id
            left join product_category pc3 on pc3.parent_id = pc2.id
            where pc1.name = 'Sparepart'
        """
        self._cr.execute(categ_query)
        categ_ids = self._cr.fetchall()
        query = self._query_stock_sparepart(
            categ_ids = categ_ids
        )
        self._cr.execute(query)
        return self._cr.dictfetchall()

    def _get_last_6_months(self):
        """
        selected_month: int (1-12)
        return: list bulan (int) 6 bulan ke belakang
        """
        this_month = datetime.now().month
        lst = list(reversed([
            ((this_month - i - 1) % 12) + 1
            for i in range(1, 7)
        ]))
        return lst

    def excel_report(self, source):
        # ****************** EXPORT TO WORKBOOK ******************
        now = datetime.now()
        title = 'Laporan Qty Ideal Stock ' + now.strftime("%B %Y")
        result = dict()
        files = [i for i in source]
        for file in files:
            datas = source[file].split('\n')
            for data in datas:
                if data:
                    j = data.split(':')
                    item = j[0]
                    qty = int(j[1])
                    if item not in result:
                        result[item] = {file:qty}
                    else:
                        result[item].update({file:qty})

        ranks = self._get_ranks()
        ress = []

        MONTH_MAP = {
            1: 'Jan',
            2: 'Feb',
            3: 'Mar',
            4: 'Apr',
            5: 'May',
            6: 'Jun',
            7: 'Jul',
            8: 'Aug',
            9: 'Sep',
            10: 'Oct',
            11: 'Nov',
            12: 'Dec',
        }
        row_month = {}

        list_of_active_months = self._get_last_6_months()
        for month in list_of_active_months:
            row_month[MONTH_MAP[month]] = 0

        for foo, month_values in result.items():
            row = {}
            bar = foo.split('_')

            branch_code = bar[0]              # DDS
            branch_name = bar[1]              # Cabang Saharjo
            kode_part = bar[2]                # SPX2 10W30 SLMB 0,65L REP
            nama_part = bar[3]
            kategori_part = bar[-1]           # Sparepart

            # Inisialisasi row
            row.update({
                'kode_cabang': branch_code,
                'nama_cabang': branch_name,
                'kode_part': nama_part,
                'nama_part': kode_part,
                'kategori_part': kategori_part
            })
            # Tambah Periode ditengah-tengah
            row.update({
                **row_month
            })
            row.update({
                'total': 0,
                'Avg/Ideal Stock': 0
            })

            total = 0

            for key, qty in month_values.items():
                month, year = key.split('_')
                month = int(month)

                if month in MONTH_MAP:
                    col_name = MONTH_MAP[month]
                    row[col_name] = qty
                    total += qty

            row['total'] = total
            row['Avg/Ideal Stock'] = round(total/6,2) # 2 desimal di belakang koma

            for ra in ranks:
                if ra.get('branch') == branch_code and ra.get('kode_part') == kode_part:
                    rank_count += 1

            rank_count = 0
            if rank_count >= 12:
                rank = 'A'
            elif rank_count >= 9:
                rank = 'B'
            elif rank_count >= 5:
                rank = 'C'
            elif rank_count >= 1:
                rank = 'D'
            else:
                rank = 'E'
            row['rank'] = rank

            ress.append(row)

        return self.env['web.report'].sudo().generate_report(title,ress, data_summary_header=False)

    # ****************** CONFIG CHECK ******************
    def _config_check(self):
        config = self.env['tw.config.files'].sudo().search([('name','=','QTY_IDEAL')],limit=1)
        if not config:
            raise Warning('Belum ada konfigurasi untuk QTY_IDEAL !\nMohon hubungi Helpdesk.')
        return config

    def _read_source(self):
        config = self._config_check()
        data_ids = list()
        datas_to_export = dict()
        # ****************** READ SOURCE FILE ******************
        now = self._get_default_date()
        for i in range(now.month-6,now.month):
            if i < 0:
                that_month = (now - relativedelta(months=abs(i)+now.month)).replace(day=1,hour=0,minute=0,second=0,microsecond=0)
            else:
                that_month = (now - relativedelta(months=now.month-abs(i))).replace(day=1,hour=0,minute=0,second=0,microsecond=0)
            try:
                that_month_str = that_month.strftime('%-m_%Y')
            except ValueError:
                that_month_str = that_month.strftime('%#m_%Y')

            ready = False
            source_file = "%s/QTY_IDEAL %s.qis" % (config.local_path,that_month_str)
            already_exists = os.path.exists(source_file)
            if already_exists:
                data = False
                with open(source_file, 'r') as f:
                    data = f.read()
                if data:
                    datas_to_export[that_month_str] = data
                    ready = True if data else False
            data_ids.append([0,False,{
                'month_text': that_month.strftime("%B %Y"),
                'ready_to_export': ready
            }])
        return (data_ids,datas_to_export)

class TWQtyIdealStockWizardLine(models.TransientModel):
    _name = "tw.qty.ideal.stock.wizard.line"
    _description = "Qty Ideal Stock Wizard Data"

    # 7: defaults methods

    # 8: fields
    month_text = fields.Char('Bulan')
    ready_to_export = fields.Boolean('Data Siap di-Export')

    # 9: relation fields
    wizard_id = fields.Many2one('tw.qty.ideal.stock.wizard')
