# -*- coding: utf-8 -*-
import calendar
import logging

from datetime import date, datetime

from odoo import http
from odoo.http import request

from odoo.addons.rest_api.controllers.main import check_valid_token
from odoo.addons.rest_api.controllers.rest_exception import (
    invalid_response,
    valid_response,
)

_logger = logging.getLogger(__name__)


class PBTController(http.Controller):

    @http.route('/api/tunashonda/pbt', type='http', auth='none', methods=['GET'], csrf=False)
    @check_valid_token
    def get_pbt(self, **kw):
        today = date.today()
        
        start_date = datetime.strptime(kw['start_date'], '%Y-%m-%d') if kw.get('start_date') else today.replace(day=1)
        year = start_date.year
        month = start_date.month
        last_day = calendar.monthrange(year, month)[1]
        end_date = datetime.strptime(kw['end_date'], '%Y-%m-%d') if kw.get('end_date') else start_date.replace(day=last_day)
        
        domain = [('start_date', '=', start_date), ('end_date', '=', end_date)]
        
        branch_code = kw.get('branch_code')
        if branch_code:
            if not self.is_pilot_pbt(branch_code):
                info = f"Branch {branch_code} is excluded from Pilot Profit Before Tax!"
                return valid_response(200, [], info)
            
            domain += [('company_id.code', '=', branch_code)]

        pbt = request.env['tw.profit.before.tax'].search(domain, order="id DESC")
        if not pbt:
            info = f"No PBT Found for period {start_date} - {end_date}!"
            return invalid_response(200, 'pbt_not_found', info)
        
        if kw.get('series'):
            series_list = kw['series'].split(',')
            for series in series_list:
                prod_series = request.env['tw.product.series'].search([('name', '=', series),
                                                                ('division','=','Unit')], limit=1)
                if not prod_series:
                    info = f"Series {series} is not recognized!"
                    return invalid_response(200, 'pbt_error', info)

                for p in pbt:
                    if not self.is_pilot_pbt(p.company_id.code):
                        continue

                    unapproved = [l.series_motor.id for l in p.profit_before_tax_line_ids if l.state != 'approved']
                    invalid_ids = list(set([prod_series.id]).intersection(unapproved))
                    if invalid_ids:
                        invalid_series = ', '.join([s.name for s in request.env['tw.product.series'].browse(invalid_ids)])
                        return invalid_response(200, 'pbt_error', f"Series {invalid_series} haven't been approved in {p.name}!")
        
        message = "Success"
        result = [{
            'name': i.name,
            'branch': i.company_id.name,
            'state': i.state
        } for i in pbt]
        return valid_response(200, result, message)
    
    def is_pilot_pbt(self, branch_code):
        pilot = request.env['tw.pilot.project'].search([('name', '=', 'Pilot Profit Before Tax')], limit=1)
        if pilot:
            branch = request.env['res.company'].search([('code', '=', branch_code)])
            if branch.id in pilot.company_ids.ids:
                return True
            return False
        
        # if pilot project not exist means its already live
        return True
