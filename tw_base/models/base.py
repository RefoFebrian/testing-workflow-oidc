# models/currency_format.py
from odoo.models import BaseModel
from odoo.tools.misc import formatLang

def currency_format(self, amount):
    return formatLang(self.env, amount, currency_obj=self.env.company.currency_id)

# Monkey-patch it onto BaseModel
BaseModel.currency_format = currency_format