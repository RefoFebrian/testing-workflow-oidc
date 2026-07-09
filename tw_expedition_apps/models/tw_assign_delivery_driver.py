# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date, datetime, time, timedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib
class TwAssignDeliveryDriver(models.TransientModel):
    _name = "tw.assign.delivery.driver.wizard"
    _description = "Assign Delivery Driver"
    
    # 7: defaults methods

    # 8: fields
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
    total_qty = fields.Integer(string='Total Qty', compute='_compute_total_qty')
    total_qty_assigned = fields.Integer(string='Total Qty Assigned', compute='_compute_total_qty')
    total_capacity = fields.Integer(string='Total Capacity')
    
    # 9: relation fields
    company_id = fields.Many2one('res.company', string="Branch", default=lambda self: self.env.company)
    delivery_driver_id = fields.Many2one('hr.employee', string='Delivery Driver')
    picking_ids = fields.Many2many('stock.picking', string='Source Picking')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('delivery_driver_id', 'picking_ids')
    def _compute_total_qty(self):
        for record in self:
            total_qty_assigned, total_qty = self._get_total_unit_delivery_for_driver(record.delivery_driver_id.id)
            record.total_qty_assigned = total_qty_assigned
            record.total_qty = total_qty
    
    @api.onchange('delivery_driver_id')
    def _onchange_total_capacity(self):
        partner = self.delivery_driver_id.user_id.partner_id
        if partner:
            self.total_capacity = partner.delivery_capacity or 0
        else:
            self.total_capacity = 0

    # 12: override methods

    # 13: action methods
    def action_view_monitoring_expedition(self, picking_ids):
        list_id = self.env.ref('tw_expedition_apps.tw_monitoring_expedition_apps_assigned_list_view').id
        return {
            'name': 'Monitoring Expedition',
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'view_type': 'list',
            'view_mode': 'list',
            'views': [(list_id, 'list')],
            'domain': [('id', 'in', picking_ids)],
            'target': 'new'
        }
        
    def action_assign_delivery_driver(self):
        try:
            if self.delivery_driver_id:
                self.picking_ids.write({
                    'delivery_driver_id': self.delivery_driver_id.id,
                    'assign_driver_date': datetime.now(),
                    'assign_driver_uid': self.env.user.id,
                })
                return self.action_view_monitoring_expedition(self.picking_ids.ids)
        except Exception as err:
            raise Warning(f"Failed to assign delivery driver because : '{str(err)}'")

    # 14: private methods
    def _get_total_unit_delivery_for_driver(self, driver_id):
        total_qty = 0
        total_qty_assigned = 0
        if driver_id:
            assigned_picking_obj = self.env['stock.picking'].sudo().search([
                    ('delivery_driver_id', '=', driver_id),
                    ('delivery_state', '!=', 'delivered')
                ])
            if assigned_picking_obj:
                total_qty_assigned += sum(assigned_picking_obj.move_ids.filtered(lambda x: x.product_id.division == 'Unit').mapped('product_uom_qty'))
        if self.picking_ids:
            total_qty += total_qty_assigned
            total_qty += sum(self.picking_ids.move_ids.filtered(lambda x: x.product_id.division == 'Unit').mapped('product_uom_qty'))

        return total_qty_assigned, total_qty
