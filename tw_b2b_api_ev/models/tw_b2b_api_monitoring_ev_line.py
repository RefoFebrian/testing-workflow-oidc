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

class TWB2BApiMonitoringEvLine(models.TransientModel):
    _name = "tw.b2b.api.monitoring.ev.line"
    _description = "TW B2B API Monitoring EV Line"
    _rec_name = 'ship_list_number'
    
    # 7: defaults methods
    def _get_default_date(self):
        return date.today().strftime("%Y-%m-%d")
    
    def _get_default_datetime(self):
        return datetime.now()

    # 8: fields
    ship_list_date = fields.Char('SL Date')
    ship_list_number = fields.Char('SL Number')
    total_unit = fields.Integer('Total Unit')
    outstanding_unit = fields.Integer('Outstanding Unit')
    done_unit = fields.Integer('Done Unit')
    total_baterai = fields.Integer('Total Baterai')
    outstanding_baterai = fields.Integer('Outstanding Baterai')
    done_baterai = fields.Integer('Done Baterai')
    state = fields.Selection([
        ('outstanding', 'Outstanding'),
        ('done', 'Done')
    ], string='Status')

    # 9: relation fields
    monitoring_ev_id = fields.Many2one('tw.b2b.api.monitoring.ev', string='Monitoring EV')
    company_id = fields.Many2one('res.company', string='Branch')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_detail(self):
        picking_obj = self.env['stock.picking'].suspend_security().search([('mft_reference', '=', self.ship_list_number)])
        if not picking_obj:
            raise Warning('Data Not Found.')
        
        list_id = self.env.ref('tw_stock.tw_stock_picking_inherit_list_view').id
        form_id = self.env.ref('tw_stock.tw_stock_picking_inherit_form_view').id
        response = {
            'name': 'Stock Packing MD',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
        }
        if len(picking_obj) > 1:
            response['view_mode'] = 'list,form'
            response['domain'] = [('id','in',[picking.id for picking in picking_obj])]
            response['views'] = [(list_id, 'list'), (form_id, 'form')]
        else:
            response['view_mode'] = 'form'
            response['res_id'] = picking_obj.id

        return response

    # 14: private methods