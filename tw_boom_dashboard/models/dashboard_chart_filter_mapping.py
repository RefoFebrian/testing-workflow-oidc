# -*- coding: utf-8 -*-

from odoo import models, fields


class DashboardChartFilterMapping(models.Model):
    _name = "dashboard.chart.filter.mapping"
    _description = "Dashboard Chart Filter Mapping"

    chart_id = fields.Many2one(
        "dashboard.chart",
        string="Chart",
        required=True,
        ondelete="cascade",
    )
    filter_type = fields.Selection([
        ('employee', 'Employee'),
        ('date_range', 'Date Range'),
        ('many2one', 'Many2One Field'),
        ('selection', 'Selection Field'),
        ('manual', 'Manual Input'),
    ], string="Filter Type", required=True, default="employee")
    target_field_id = fields.Many2one(
        "ir.model.fields",
        string="Target Field",
        required=True,
        ondelete="cascade",
        domain="[('model_id', '=', parent.model_id)]",
        help="Field on the chart's model to apply the filter to",
    )
    filter_technical_name = fields.Char(
        string="Filter Technical Name",
        help="Technical name to match the filter widget's key (e.g. area_manager, spv). "
             "If empty, falls back to matching by filter_type."
    )
