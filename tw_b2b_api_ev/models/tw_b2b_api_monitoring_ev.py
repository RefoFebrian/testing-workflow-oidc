# -*- coding: utf-8 -*-

# 1: imports of python lib
import time
import requests
import json

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
import logging
_logger = logging.getLogger(__name__)

# 5: local imports

# 6: Import of unknown third party lib

class TWB2BApiMonitoringEv(models.TransientModel):
    _name = "tw.b2b.api.monitoring.ev"
    _description = "TW B2B API Monitoring EV"
    
    # 7: defaults methods
    def _get_default_date(self):
        return date.today().strftime("%Y-%m-%d")
    
    def _get_default_datetime(self):
        return datetime.now()

    # 8: fields
    name = fields.Char(string='Name', compute='_compute_name')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    state = fields.Selection([
        ('all', 'All'),
        ('outstanding', 'Outstanding'),
        ('done', 'Done')
    ], string='Status', default='all')

    # 9: relation fields
    line_ids = fields.One2many('tw.b2b.api.monitoring.ev.line', 'monitoring_ev_id', string='Monitoring EV Line')
    company_id = fields.Many2one('res.company', string='Branch')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('company_id')
    def _compute_name(self):
        for record in self:
            record.name = 'Monitoring EV'
            if record.company_id:
                record.name = self.env['ir.sequence'].get_sequence_code('EV', str(record.company_id.code))

    # 12: override methods

    # 13: action methods
    def action_search(self):
        self.line_ids = False
        if self.end_date < self.start_date:
            raise Warning('Date must be greater than start date.')

        categ_ids = self.env['product.category'].suspend_security().search([('parent_id','child_of','EV')]).ids
        if not categ_ids:
            raise Warning("Category EV not found.")
        
        query_where = "WHERE 1=1"
        if self.state == 'outstanding':
            query_where += " AND (COALESCE(unit.outstanding_unit, 0) > 0 OR COALESCE(baterai.outstanding_baterai, 0) > 0)"
        elif self.state == 'done':
            query_where += " AND (COALESCE(unit.outstanding_unit, 0) = 0 AND COALESCE(baterai.outstanding_baterai, 0) = 0)"

        query = f"""
            WITH unit_data AS (
                SELECT 
                    lot.company_id,
                    lot.ship_list_number,
                    lot.ship_list_date,
                    COUNT(lot.id) AS total_unit,
                    COUNT(lot.id) FILTER (WHERE lot.state = 'intransit') AS outstanding_unit,
                    COUNT(lot.id) FILTER (WHERE lot.state = 'stock') AS done_unit
                FROM stock_lot lot
                JOIN product_product pp ON lot.product_id = pp.id
                JOIN product_template pt ON pp.product_tmpl_id = pt.id
                WHERE pt.division = 'Unit'
                AND pt.categ_id IN {tuple(categ_ids)}
                AND lot.state IN ('intransit', 'stock')
                AND lot.ship_list_date BETWEEN '{self.start_date}' AND '{self.end_date}'
                AND lot.company_id = {self.company_id.id}
                GROUP BY lot.company_id, lot.ship_list_number, lot.ship_list_date
            ),
            baterai_data AS (
                SELECT 
                    lot.company_id,
                    lot.ship_list_number,
                    lot.ship_list_date,
                    COUNT(lot.id) AS total_baterai,
                    COUNT(lot.id) FILTER (WHERE lot.state = 'intransit') AS outstanding_baterai,
                    COUNT(lot.id) FILTER (WHERE lot.state = 'stock') AS done_baterai
                FROM stock_lot lot
                JOIN tw_b2b_api_ev_line ev_line ON ev_line.serial_number = lot.name
                JOIN tw_b2b_api_ev api_ev ON api_ev.id = ev_line.b2b_api_ev_id
                JOIN product_product pp ON lot.product_id = pp.id
                JOIN product_template pt ON pp.product_tmpl_id = pt.id
                WHERE api_ev.ship_list_number = lot.ship_list_number
                AND api_ev.jenis_acc = 'OEM'
                AND lot.state IN ('intransit', 'stock')
                AND lot.ship_list_date BETWEEN '{self.start_date}' AND '{self.end_date}'
                AND lot.company_id = {self.company_id.id}
                GROUP BY lot.company_id, lot.ship_list_number, lot.ship_list_date
            )
            SELECT 
                COALESCE(unit.company_id, baterai.company_id) AS company_id,
                COALESCE(unit.ship_list_number, baterai.ship_list_number) AS ship_list_number,
                COALESCE(unit.ship_list_date, baterai.ship_list_date) AS ship_list_date,
                COALESCE(unit.total_unit, 0) AS total_unit,
                COALESCE(unit.outstanding_unit, 0) AS outstanding_unit,
                COALESCE(unit.done_unit, 0) AS done_unit,
                COALESCE(baterai.total_baterai, 0) AS total_baterai,
                COALESCE(baterai.outstanding_baterai, 0) AS outstanding_baterai,
                COALESCE(baterai.done_baterai, 0) AS done_baterai,
                CASE
                    WHEN COALESCE(unit.outstanding_unit, 0) > 0 
                    OR COALESCE(baterai.outstanding_baterai, 0) > 0 
                THEN 'outstanding'
                ELSE 'done' END AS state
            FROM unit_data unit
            FULL OUTER JOIN baterai_data baterai
                ON unit.company_id = baterai.company_id
                AND unit.ship_list_number = baterai.ship_list_number
                AND unit.ship_list_date = baterai.ship_list_date
            {query_where}
            ORDER BY ship_list_number, ship_list_date
        """
        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()
        
        if not ress:
            raise Warning('Data Not Found.')
            
        processed_results = [[0, 0, res] for res in ress]
        if processed_results:
            self.line_ids = processed_results

    # 14: private methods

