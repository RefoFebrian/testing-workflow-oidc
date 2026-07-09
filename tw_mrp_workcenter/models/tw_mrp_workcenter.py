from odoo import api, fields, models, _
from odoo.exceptions import UserError

class MrpWorkcenter(models.Model):
    _inherit = "mrp.workcenter"

    cost_calculation_type = fields.Selection(
        [('time', 'Based on Time Spent'),
         ('qty', 'Based on Work Order Quantity')],
        string='Cost Calculation',
        default='time',
        required=True,
        help="""
            - Based on Time Spent: Cost is calculated based on the time spent on the work order
            - Based on Work Order Quantity: Cost is calculated based on the quantity produced in the work order
        """
    )
    cost_per_unit = fields.Float(
        string='Cost per Unit',
        default=0.0,
        help="Cost per unit when using 'Based on Work Order Quantity' calculation type"
    )
