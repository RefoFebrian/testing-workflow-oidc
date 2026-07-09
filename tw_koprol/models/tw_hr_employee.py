from odoo import models, fields, api
from datetime import datetime, timedelta

import requests

class InheritEmployee(models.Model):
    _inherit = "hr.employee"

    last_modified_date = fields.Datetime('Last Modified Date Koprol')