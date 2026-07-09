# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwWorkOrder(models.Model):
    _inherit = "tw.work.order"

    # 7: defaults methods

    # 8: fields
    warranty = fields.Float(string='Warranty', compute='_compute_warranty', digits='Account', store=True, default=0.0, help="Warranty in days, (i.e. 2.5 = 2.5 Days)")

    # 9: relation fields
    previous_work_order_id = fields.Many2one('tw.work.order', string='WO Sebelumnya')
    available_previous_work_order_ids = fields.Many2many('tw.work.order', string='Domain WO Sebelumnya', compute='_compute_available_previous_work_order_ids')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('order_line.warranty')
    def _compute_warranty(self):
        for order in self:
            order.warranty = max(order.order_line.mapped('warranty'), default=0.0)

    @api.depends('previous_work_order_id')
    def _compute_available_previous_work_order_ids(self):
        for order in self:
            item_ids = []
            if order.type_id.value and order.company_id:
                if order.type_id.value == 'WAR':
                    query = f"""
                        SELECT  id as work_order
                        FROM tw_work_order 
                        LEFT JOIN (
                            SELECT order_id, max(warranty) as warranty
                        FROM tw_work_order_line
                        GROUP BY order_id
                        ) as twol ON twol.order_id = tw_work_order.id
                        WHERE now() <= date + INTERVAL '7 hours' + (twol.warranty * INTERVAL '1 day')
                        AND company_id = {order.company_id.id}
                        AND state = 'done'
                    """
                    order._cr.execute (query)
                    ress =  order._cr.fetchall()
                    item_ids = [res[0] for res in ress]
            order.available_previous_work_order_ids = item_ids

    @api.onchange('type_id','company_id')
    def onchange_type_new(self):
        self.mechanic_id = False
        self.previous_work_order_id = False

    def _prepare_previous_work_order(self):
        prepare_previous_work_order = super()._prepare_previous_work_order()
        self.lot_id = self.previous_work_order_id.lot_id.id
        self.chassis_number = self.previous_work_order_id.chassis_number
        self.product_id = self.previous_work_order_id.product_id.id
        self.plate_number = self.previous_work_order_id.plate_number
        self.km = self.previous_work_order_id.km
        self.payment_type = self.previous_work_order_id.payment_type if self.previous_work_order_id.payment_type else 'cash'
        self.purchase_date = self.previous_work_order_id.purchase_date
        self.fuel = self.previous_work_order_id.fuel
        self.production_year = self.previous_work_order_id.production_year
        self.is_washing_the_motorbike = self.previous_work_order_id.is_washing_the_motorbike if self.previous_work_order_id.is_washing_the_motorbike else 'tidak'
        return prepare_previous_work_order


    @api.onchange('previous_work_order_id')
    def _onchange_previous_work_order_id(self):
        self._prepare_previous_work_order()

    # 12: override methods