# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TWActivitySaleOrder(models.Model):
    _inherit = "tw.dealer.sale.order"
    
    # 8: fields
    is_btl = fields.Boolean(string='BTL?', compute='_compute_is_btl', store=True)
    is_requires_act_type = fields.Boolean(compute='_compute_channel_configuration')
    is_pos = fields.Boolean(compute='_compute_channel_configuration')
    sales_channel = fields.Char(compute='_compute_sales_channel')

    # 9: relation fields
    activity_plan_id = fields.Many2one('tw.activity.atl.btl.line','Activity',domain=[('id','=',0)])
    activity_point_id = fields.Many2one('tw.titik.keramaian','Titik Keramaian', compute='_compute_activity_point',store=True)
    sales_channel_id = fields.Many2one('tw.selection', "Jaringan Penjualan", domain=[('type', '=', 'SalesChannel')])
    sales_source_location_id = fields.Many2one('stock.location', 'Sales Source Location')
    act_type_id = fields.Many2one('tw.master.activity.type','Activity Type')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('act_type_id')
    def _compute_is_btl(self):
        for record in self:
            if record.act_type_id:
                record.is_btl = record.act_type_id.is_btl
            else:
                record.is_btl = False

    @api.depends('sales_channel_id', 'sales_channel_id.context')
    def _compute_channel_configuration(self):
        for record in self:
            if record.sales_channel_id:
                record.is_requires_act_type = record.sales_channel_id.context_get('requires_act_type', False)
                record.is_pos = record.sales_channel_id.context_get('is_pos', False)
            else:
                record.is_requires_act_type = False
                record.is_pos = False

    @api.depends('activity_plan_id')
    def _compute_activity_point(self):
        for record in self:
            if record.activity_plan_id:
                record.activity_point_id = record.activity_plan_id.mapping_activity_id.activity_point_id

    @api.depends('sales_channel_id')
    def _compute_sales_channel(self):
        for record in self:
            record.sales_channel = record.sales_channel_id.value.lower() if record.sales_channel_id.value else ''

    @api.onchange('sales_channel_id','act_type_id','company_id')
    def onchange_activity_plan(self):
        ids = []
        if self.sales_channel_id and self.act_type_id and self.company_id:
            now_date = date.today()
            now_month = now_date.month
            now_year = now_date.year
            query = """
                SELECT spl.id
                FROM tw_activity_atl_btl sp
                INNER JOIN tw_activity_atl_btl_line spl ON spl.activity_id = sp.id
                WHERE sp.company_id = %s
                AND sp.month = '%s'
                AND sp.year = '%s'
                AND spl.sales_channel_id = '%d'
                AND spl.act_type_id = %d
                AND spl.state = 'done'
            """ %(self.company_id.id, now_month, now_year, self.sales_channel_id.id, self.act_type_id.id)
            self._cr.execute(query)
            ress = self._cr.fetchall()
            ids = [res[0] for res in ress]
        domain = {'activity_plan_id': [('id', 'in', ids)]}
        return {'domain': domain}

    @api.onchange('sales_channel_id')
    def onchange_jaringan_penjualan(self):
        self.act_type_id = False

    @api.onchange('act_type_id')
    def onchange_sumber_penjualan(self):
        self.activity_plan_id = False
        self.sales_source_location_id = False

    # 12: override methods

    # 13: action methods

    # 14: private methods

