# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.exceptions import AccessError

class MasterTargetMarginLine(models.Model):
    _name = "tw.master.target.margin.line"
    _description = "Master Target Margin Line"
    
    def _get_year(self):
        current_year = datetime.now().year
        start_year = 2000
        years_available = []

        for x in reversed(range(start_year, current_year + 1)):
            elem = ("{}".format(x), "{}".format(x))
            years_available.append(elem)

        return years_available

    name = fields.Char(compute='_compute_name', store=True)
    cash = fields.Float(string='Cash', help="")
    credit = fields.Float(string='Credit', help="")
    year = fields.Selection(selection=_get_year, string='Manufacture Year')
  
    series_id = fields.Many2one(comodel_name='product.series', string='Series', domain=[('active', '=', True)], help="")
    target_margin_id = fields.Many2one(comodel_name='tw.master.target.margin', string='Target margin')

    _sql_constraints = [
        (
            'unique_series_year_per_master',
            'unique(target_margin_id, series_id, year)',
            'A series cannot be duplicated for the same target margin and year.'
        )
    ]
    
    @api.depends('series_id', 'year', 'target_margin_id.name')
    def _compute_name(self):
        for record in self:
            if record.series_id and record.target_margin_id.name:
                series = record.series_id.name
                year = record.year
                target_margin = record.target_margin_id.name
                record.name = f'{target_margin} - {series} - {year} ({record.cash:,.2f}/{record.credit:,.2f})'
    
    def get_formview_action(self, access_uid=None):
        """ Override this method to add access control for user form view """
        user = self.env.user
        if access_uid:
            user = self.env['res.users'].browse(access_uid).sudo()
        if not user.has_group('tw_incentive.group_tw_master_target_margin_read'):
            raise AccessError(_("You do not have access to this document."))
            
        res = super().get_formview_action(access_uid=access_uid)
        return res