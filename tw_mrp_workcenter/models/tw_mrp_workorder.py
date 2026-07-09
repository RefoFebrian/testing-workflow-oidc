from odoo import api, fields, models, _

class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"
    
    def _cal_cost(self, date=False):
        """
        Override to support different cost calculation types:
        - 'time': Based on time spent (default Odoo behavior)
        - 'qty': Based on work order quantity produced
        """
        total = 0
        for wo in self:
            if wo.workcenter_id.cost_calculation_type == 'qty':
                # Calculate cost based on quantity produced
                qty_produced = wo.qty_produced or 0
                cost_per_unit = wo.workcenter_id.cost_per_unit or 0
                total += qty_produced * cost_per_unit
            else:
                # Default time-based calculation
                if date:
                    duration = sum(wo.time_ids.filtered(
                        lambda t: t.date_end and t.date_end <= date
                    ).mapped('duration'))
                else:
                    duration = sum(wo.time_ids.mapped('duration'))
                total += (duration / 60.0) * wo.workcenter_id.costs_hour
        return total
