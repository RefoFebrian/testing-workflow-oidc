from odoo import models, fields, api
from datetime import datetime, timedelta

import requests

class InheritCompany(models.Model):
    _inherit = "res.company"

    koprol_code = fields.Char('Koprol Code')