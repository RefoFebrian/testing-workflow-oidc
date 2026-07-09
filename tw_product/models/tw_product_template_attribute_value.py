# Part of Odoo. See LICENSE file for full copyright and licensing details.

from random import randint

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command


class TWProductTemplateAttributeValue(models.Model):
    _inherit = "product.template.attribute.value"

    def _get_default_color(self):
        return randint(1, 11)

    code = fields.Char(string="Code", related="product_attribute_value_id.code")

    @api.depends('attribute_id')
    def _compute_display_name(self):
        """Override because in general the name of the value is confusing if it
        is displayed without the name of the corresponding attribute.
        Eg. on exclusion rules form
        """
        for value in self:
            value.display_name = f"{value.attribute_id.name}: [{value.code}] {value.name}"

    def _get_combination_code(self):
        """Exclude values from single value lines or from no_variant attributes."""
        ptavs = self._without_no_variant_attributes().with_prefetch(self._prefetch_ids)
        ptavs = ptavs._filter_single_value_lines().with_prefetch(self._prefetch_ids)
        return ", ".join([ptav.code +'-'+ ptav.name for ptav in ptavs])