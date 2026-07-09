from odoo import models, fields, api
from datetime import datetime, timedelta

import requests

class Product(models.Model):
    _inherit = "product.template"

    koprol_code = fields.Char('Koprol Code')
    last_modified_date = fields.Datetime('Last Modified Date Koprol')
