# -*- coding: utf-8 -*-

from odoo import models, fields, api


class DashboardChartStackedSegment(models.Model):
    _name = "dashboard.chart.stacked.segment"
    _description = "Dashboard Chart Stacked Progress Segment"
    _order = "sequence, id"

    chart_id = fields.Many2one(
        'dashboard.chart',
        string='Chart',
        ondelete='cascade',
        required=True
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Order of the segment in the progress bar"
    )
    name = fields.Char(
        string='Label',
        required=True,
        help="Display name for this segment (e.g. 'Overdue H+1')"
    )
    color = fields.Char(
        string='Color',
        default='#4CAF50',
        help="Hex color code for this segment"
    )
    domain = fields.Text(
        string='Segment Domain',
        help="Odoo domain filter. Example: [('task_status', '=', 'overdue_1')]"
    )
