from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProductSeries(models.Model):
    _name = "product.series"
    _description = "Product Series"
    _order = "name"

    name = fields.Char('Series Name', required=True, index=True, translate=True)
    active = fields.Boolean('Active', default=True)
    description = fields.Text('Description')
    product_count = fields.Integer('Products', compute='_compute_product_count')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Series name must be unique!')
    ]

    def _compute_product_count(self):
        product_data = self.env['product.template'].read_group(
            [('series_id', 'in', self.ids)], ['series_id'], ['series_id'])
        mapped_data = {item['series_id'][0]: item['series_id_count'] for item in product_data}
        for series in self:
            series.product_count = mapped_data.get(series.id, 0)

    def action_view_products(self):
        self.ensure_one()
        return {
            'name': _('Products'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'product.template',
            'type': 'ir.actions.act_window',
            'domain': [('series_id', '=', self.id)],
            'context': {'default_series_id': self.id}
        }
