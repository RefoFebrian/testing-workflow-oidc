import calendar
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError as Warning

from odoo import models, fields, api

class TwActivityAtlBtlInherit(models.Model):
    _inherit = "tw.activity.atl.btl.line"

    qty_customer_last = fields.Float('Total Customer Last Month',compute='compute_customer_last_month')

    spk_ids = fields.One2many('tw.dealer.spk', inverse_name='activity_plan_id', string='SPK',domain=[('state','!=','draft')])    
    dso_ids = fields.One2many(comodel_name='tw.dealer.sale.order', inverse_name='activity_plan_id', string='DSO', domain=[('state','in',('progress','done'))])

    @api.depends('dso_ids')
    def compute_actual_unit(self):
        total = 0
        for so in self.dso_ids:
            for line in so.dealer_sale_order_line:
                total += line.product_qty
        self.actual_unit = total

    @api.depends('spk_ids')
    def compute_actual_customer(self):
        total = len(self.spk_ids)
        self.actual_customer = total

    @api.depends('sales_channel_id','act_type_id','mapping_activity_id','submission_type','location_id')
    def compute_customer_last_month(self):
        for record in self:
            ctx_act_id = self._context.get('default_activity_id')
            if ctx_act_id and isinstance(ctx_act_id, int):
                activity_obj = self.env['tw.activity.atl.btl'].browse(ctx_act_id)
            elif record.activity_id and record.activity_id._origin and isinstance(record.activity_id._origin.id, int):
                activity_obj = record.activity_id._origin
            else:
                activity_obj = record.activity_id

            if not activity_obj or not activity_obj.company_id or not activity_obj.month or not activity_obj.year:
                raise Warning('Silahkan isi data header terlebih dahulu !')
            now = date(int(activity_obj.year), int(activity_obj.month), 1)  
            start_month = now - relativedelta(months=1)
            qty = 0
            if record.sales_channel_id and record.act_type_id and record.mapping_activity_id.activity_point_id:
                query_loc = ""
                if record.location_id:
                    query_loc = "AND spl.location_id = %d" %(record.location_id.id)
                query = """
                    SELECT spl.id
                    FROM tw_activity_atl_btl sp
                    INNER JOIN tw_activity_atl_btl_line spl ON spl.activity_id = sp.id
                    WHERE sp.company_id = %d
                    AND sp.month = '%s'
                    AND sp.year = '%s'
                    AND spl.sales_channel_id = '%d'
                    AND spl.act_type_id = %d
                    AND spl.mapping_activity_id = %d
                    %s
                """ %(record.company_id.id, start_month.month, start_month.year, record.sales_channel_id.id, record.act_type_id.id, record.mapping_activity_id.id, query_loc)
                self._cr.execute(query)
                ress = self._cr.fetchall()
                for res in ress:
                    activity_line_id = self.browse(res[0])
                    qty += len(activity_line_id.spk_ids)
                
            record.qty_customer_last = qty

    @api.onchange('sales_channel_id','act_type_id','mapping_activity_id','submission_type','location_id')
    def onchange_history_location(self):
        self.lat = False
        self.long = False
        
        ctx_act_id = self._context.get('default_activity_id')
        if ctx_act_id and isinstance(ctx_act_id, int):
            activity_obj = self.env['tw.activity.atl.btl'].browse(ctx_act_id)
        elif self.activity_id and self.activity_id._origin and isinstance(self.activity_id._origin.id, int):
            activity_obj = self.activity_id._origin
        else:
            activity_obj = self.activity_id

        if not activity_obj or not activity_obj.company_id or not activity_obj.month or not activity_obj.year:
            raise Warning('Silahkan isi data header terlebih dahulu !')
        self.history_location_ids = False
        history_ids = []
        now = date(int(activity_obj.year), int(activity_obj.month), 1)  
        start_month = now - relativedelta(months=3)
        if self.sales_channel_id and self.act_type_id and self.mapping_activity_id.activity_point_id:
            query_loc = ""
            if self.location_id:
                query_loc += "AND pal.location_id = %d" %(self.location_id)
            query = """
                SELECT EXTRACT(MONTH FROM date_order) as month
                , pp.id as prod_id
                , pt.categ_id as categ_id
                FROM tw_activity_atl_btl pa
                INNER JOIN tw_activity_atl_btl_line pal ON pal.activity_id = pa.id
                INNER JOIN tw_dealer_sale_order so ON so.activity_plan_id = pal.id
                INNER JOIN tw_dealer_sale_order_line sol on so.id = sol.order_id
                INNER JOIN product_product pp ON pp.id = sol.product_id
                INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id                
                WHERE so.sales_channel_id = '%d'
                AND so.sales_source_location_id = %d
                AND so.activity_point_id = %d
                AND date_order BETWEEN '%s' AND '%s'
                %s
                ORDER BY month ASC
            """ %(self.sales_channel_id.id, self.act_type_id.id, self.mapping_activity_id.activity_point_id.id, start_month, now, query_loc)
            self._cr.execute(query)
            ress = self._cr.dictfetchall()
            ids = {}
            if len(ress) > 0:
                for res in ress:
                    month = (calendar.month_name[int(res['month'])])
                    if not ids.get(month):
                        ids[month] = {
                            'name': month,
                            'qty': 0,
                            'detail_ids': []
                        }
                    ids[month]['qty'] += 1
                    ids[month]['detail_ids'].append([0, False, {
                        'product_id': res['prod_id'],
                        'categ_id': res['categ_id']
                    }])
            for x in ids.values():
                history_ids.append([0, False, x])
        self.history_location_ids = history_ids
