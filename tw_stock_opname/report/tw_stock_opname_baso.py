from odoo import models, fields, api

class StockOpnameBasoWizard(models.TransientModel):
    _name = "tw.stock.opname.baso.wizard"
    _description = "Wizard BASO"

    note = fields.Text('Note')
    division = fields.Selection(selection=[('Unit', 'Unit'), ('Extras', 'Extras'), ('Sparepart', 'Sparepart')])
    opname_id = fields.Many2one('tw.stock.opname', ondelete="cascade") 

    def action_bakso_sparepart(self):
        query = f"""
            SELECT SUM(detail.qty_system) FILTER(WHERE detail.state != 'anomali') qty_system
                , COALESCE(SUM(detail.price * detail.qty_system) FILTER(WHERE detail.state != 'anomali'), 0) amount_system
                , COALESCE(SUM(detail.qty_count) FILTER(WHERE detail.state != 'anomali'), 0) qty_fisik
                , COALESCE(SUM(detail.price * detail.qty_count) FILTER(WHERE detail.state != 'anomali'), 0) amount_fisik
                , COALESCE(SUM(detail.qty_count) FILTER(WHERE detail.state != 'anomali'), 0) fisik_baik
                , '0' fisik_rusak
                , COALESCE(SUM(detail.selisih) FILTER(WHERE detail.state != 'anomali'), 0) selisih
                , COALESCE(SUM(detail.price * detail.selisih) FILTER(WHERE detail.state != 'anomali'), 0) amount_selisih
                , COALESCE(SUM(detail.qty_count) FILTER(WHERE detail.state = 'anomali'), 0) qty_anomali
                , COALESCE(SUM(detail.qty_count) FILTER(WHERE detail.state = 'anomali'), 0) anomali_baik
                , '0' anomali_rusak		
                , COALESCE(SUM(detail.qty_count), 0) total
            FROM tw_stock_opname opname
            LEFT JOIN tw_stock_opname_detail detail ON detail.opname_id = opname.id
            LEFT JOIN product_product part ON part.id = detail.product_id
            LEFT JOIN product_template pt ON pt.id = part.product_tmpl_id 
            LEFT JOIN product_category prod_cat ON prod_cat.id = pt.categ_id
            WHERE opname.id = {self.opname_id.id}
        """
        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()

        datas = {
             'id': self.opname_id.id,
             'model': 'tw.stock.opname.baso.wizard',
             'data': ress[0],
             'note': self.note
        }
        return self.env.ref('tw_stock_opname.action_berita_acara_so').report_action(self, data=datas)
    
    def action_bakso_unit(self):
        query = f"""
            SELECT COALESCE(pc3.name, 'Other') type_prod
                , SUM(detail.qty_system) total_system
                , COALESCE(SUM(detail.qty_count), 0) total_fisik
            FROM tw_stock_opname opname
            LEFT JOIN tw_stock_opname_detail detail ON detail.opname_id = opname.id
            LEFT JOIN product_product part ON part.id = detail.product_id
            LEFT JOIN product_template pt ON pt.id = part.product_tmpl_id 
            LEFT JOIN product_category pc ON pc.id = pt.categ_id
            LEFT JOIN product_category pc2 ON pc2.parent_id  = pc.id
            LEFT JOIN product_category pc3 ON pc3.parent_id  = pc2.id
            WHERE opname.id = {self.opname_id.id}
            AND opname.division = 'Unit'
            GROUP BY pc3.name
        """
        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()

        cols = 3  # number of table columns
        # Calculate totals per column position (0, 1, 2)
        chunks = []
        col_totals = []
        for col_idx in range(cols):
            col_items = [ress[i] for i in range(col_idx, len(ress), cols)]
            chunks.append(col_items)
            col_totals.append({
                'total_system': sum(item['total_system'] for item in col_items),
                'total_fisik': sum(item['total_fisik']  for item in col_items),
            })

        datas = {
             'id': self.opname_id.id,
             'model': 'tw.stock.opname.baso.wizard',
             'data': ress,
             'rows': chunks,
             'cols': cols,
             'col_totals': col_totals,
             'note': self.note,
             'division': 'Unit'
        }
        return self.env.ref('tw_stock_opname.action_berita_acara_stock_opname').report_action(self, data=datas)

    def action_bakso_extras(self):
        where = ''
        select = ", 0 AS ng_prev , 0 AS selisih_prev"
        prev_so = self.env['tw.stock.opname'].search([
                                ('id', '!=', self.opname_id.id),
                                ('company_id', '=', self.opname_id.company_id.id),
                                ('state', '=', 'done')],
                                order='id DESC', limit=1)
        if prev_so:
            select = """
                , coalesce(curr.qty_not_good - prev.qty_not_good, 0) AS ng_prev
                , coalesce(prev.selisih, 0) AS selisih_prev
            """
            where += f" AND prev.id = {prev_so.id}"
            
        query_accessories = f"""
            WITH stock_opname AS (
                select so.id
                    , pc."name" as categ
                    , acc.qty_good AS qty_good
                    , acc.qty_not_good AS qty_not_good
                    , acc.qty_good + qty_not_good AS total_fisik
                    , acc.qty_system AS total_sistem
                    , case
                        when acc.state = 'selisih'
                        then qty_system - (acc.qty_good + acc.qty_not_good)
                        else 0
                    end AS selisih
                FROM tw_stock_opname so
                LEFT JOIN tw_stock_opname_accessories acc ON acc.opname_id = so.id
                LEFT JOIN product_product pp ON pp.id = acc.product_id 
                LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
                LEFT JOIN product_category pc ON pc.id = pt.categ_id
            ) SELECT curr.categ
                , curr.qty_good
                , curr.qty_not_good
                , curr.total_fisik 
                , curr.total_sistem 
                , curr.selisih 
                {select}
            FROM stock_opname curr
            LEFT JOIN stock_opname prev ON prev.categ = curr.categ  
            WHERE curr.id = {self.opname_id.id}
            {where}
        """
        self.env.cr.execute(query_accessories)
        ress = self.env.cr.dictfetchall()

        datas = {
             'id': self.opname_id.id,
             'model': 'tw.stock.opname.baso.wizard',
             'data': ress,
             'note': self.note,
             'division': 'Extras'
        }

        return self.env.ref('tw_stock_opname.action_berita_acara_stock_opname').report_action(self, data=datas)

    def action_submit_baso(self):
        if self.division == 'Sparepart':
            return self.action_bakso_sparepart()
        elif self.division == 'Unit':
            return self.action_bakso_unit()
        elif self.division == 'Extras':
            return self.action_bakso_extras()
        else:
            pass

class BasoUnitPdf(models.AbstractModel):
    _name = "report.tw_stock_opname.berita_acara_stock_opname"
    _description = "Berita Acara Stock Opname PDF"

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        opname_id = data.get('id') or (docids and docids[0]) or False
        opname_obj = self.env['tw.stock.opname'].sudo().search([('id','=',opname_id)])
        employee_obj = self.env['hr.employee'].sudo().search([('user_id','=',self._uid)])
        adh = self.env['hr.employee'].sudo().search([('user_id','=',opname_obj.employee_id.id)])

        return {
            'opname_obj': opname_obj,
            'employee_obj': employee_obj,
            'note': data.get('note'),
            'results': data.get('data'),
            'adh': adh.name if adh else '',
            'date': fields.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'rows': data.get('rows'),
            'cols': data.get('cols'),
            'col_totals': data.get('col_totals'),
            'division': data.get('division'),
            'data': data.get('data'),
        }
    
class BasoSparepartPdf(models.AbstractModel):
    _name = "report.tw_stock_opname.baso_sparepart_pdf"
    _description = "Berita Acara Stock Opname Sparepart PDF"

    @api.model
    def _get_report_values(self, docids, data=None):
        opname_obj = self.env['tw.stock.opname'].sudo().search([('id','=',data['id'])])
        employee_obj = self.env['hr.employee'].sudo().search([('user_id','=',self._uid)])
        adh = self.env['hr.employee'].sudo().search([('user_id','=',opname_obj.employee_id.id)])

        return {
            'data': data['data'],
            'opname_obj': opname_obj,
            'employee_obj': employee_obj,
            'note': data['note'],
            'adh': adh.name,
            'date': fields.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }