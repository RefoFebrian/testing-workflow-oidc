from odoo import fields, models


class TwListField(models.Model):
    _inherit = "list.fields"

    measure_domain = fields.Char(string='Domain', help="Domain for filtering records in this column (e.g. [('state', '=', 'done')])")
    label_name = fields.Char(string='Label Name', help="Label name for changing column name")
    measure_color = fields.Char(string='Color', default='#000000', help="Color for the measured field column")

    value_type = fields.Selection(selection_add=[('count', 'Count')])
