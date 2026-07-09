from odoo import api, fields, models
from datetime import datetime, timedelta
from odoo.exceptions import UserError as Warning

class StockInboundReport(models.TransientModel):
    _name = "tw.stock.inbound.report"
    _description = "Stock Inbound Report"

    def _get_default_date(self):
        return datetime.now()

    start_date = fields.Date('Start Date', default=_get_default_date)
    end_date = fields.Date('End Date', default=_get_default_date)
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())

    expedition_ids = fields.Many2many('res.partner', 'tw_stock_inbound_report_expedition_rel', 'stock_inbound_id', 'expedition_id', string='Expedition', domain=[('category_id.name','=','Expedition')])

    def action_export_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        query_where = ""
        if self.division:
            query_where += f" AND tsi.division = '{str(self.division)}'"
        
        if self.expedition_ids:
            expedition_ids = str(tuple([b.id for b in self.expedition_ids])).replace(',)', ')')
            query_where += f" AND tsi.expedition_id IN {expedition_ids}"

        if self.start_date:
            query_where += f" AND tsi.date >= '{str(self.start_date)}'"
        
        if self.end_date:
            query_where += f" AND tsi.date <= '{str(self.end_date)}'"

        query = f"""
            SELECT tsi.name AS "No. Expedition"
                , tsi.division AS "Division"
                , tsi.id_expedisi_ahm AS "Expedition Code"
                , rp.name AS "Expedition Name"
                , tv.plate_number AS "Plate Number"
                , driver.name AS "Driver"
                , COALESCE(to_char(tsi.date + INTERVAL '7 hours','YYYY-MM-DD HH24:MI:SS'),'') AS "Incoming Date"
                , spb.name AS "Pallet Number"
                , tsi.amount_of_load AS "Amount of Load"
                , tsi.rope_condition
                , tsi.sponge_count
                , tsi.steel_count
                , tsi.saddle_count
            FROM tw_stock_inbound tsi 
            LEFT JOIN tw_stock_inbound_line tsil on tsi.id = tsil.stock_inbound_id 
            LEFT JOIN res_partner rp on tsi.expedition_id = rp.id
            LEFT JOIN tw_vehicle tv on tsi.vehicle_id = tv.id
            LEFT JOIN res_partner driver on tsi.driver_id = driver.id
            LEFT JOIN stock_picking_batch spb on tsi.id = spb.stock_inbound_id 
            WHERE 1=1
            {query_where}
            ORDER BY tsi.date
        """
        self._cr.execute(query)
        result = self._cr.dictfetchall()
        return self.env['web.report'].sudo().generate_report('Report Stock Inbound', result)
    