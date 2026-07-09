# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date, timedelta
from math import e 

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError, UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class ServiceRateReport(models.TransientModel):
    _name = "tw.service.rate.report"
    _description = "Service Rate Report"

    def _get_default_date(self):
        return datetime.now()

    start_date = fields.Date('Start Date', default=_get_default_date)
    end_date = fields.Date('End Date', default=_get_default_date)


    @api.onchange('start_date', 'end_date')
    def onchange_date(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise Warning('Start Date must be less than End Date')


    def action_export_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        result = self.get_data_result()

        # Check if all values in result are empty lists
        if all(not value for value in result.values()):
            raise Warning("No data available to export.")

        # Filter out empty data sheets
        result = {k: v for k, v in result.items() if v}

        params = {
            'PO x MO': 'AVERAGE',
            'PO x SJ': 'AVERAGE',
        }

        return self.env['web.report'].sudo().generate_report(
            'Report Service Rate', 
            data=result,
            data_sheet=result,
            data_custom_footer=params
        )


    def get_data_result(self):
        """
        Base implementation of get_data_result that returns an empty dictionary.
        Child classes should override this method and call super().get_data_result()
        to extend the result.
        """

        result = {}
        return result
