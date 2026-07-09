import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round

_log = logging.getLogger(__name__)


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    product_id = fields.Many2one('product.product', "Component", required=False)
    product_backup_id = fields.Many2one(
        'product.product', help="Technical field to store previous value of product_id"
    )
    component_template_id = fields.Many2one(
        'product.template', "Component (product template)"
    )
    match_on_attribute_ids = fields.Many2many(
        'product.attribute',
        string="Match on Attributes",
        compute="_compute_match_on_attribute_ids",
        store=True,
    )
    product_uom_category_id = fields.Many2one(
        'uom.category',
        related=None,
        string="UOM Category",
        compute="_compute_product_uom_category_id",
    )

    @api.depends("product_id", "component_template_id")
    def _compute_product_uom_category_id(self):
        """Compute the product_uom_category_id field.

        This is the product category that will be allowed to use on the product_uom_id
        field, already covered by core module:
        https://github.com/odoo/odoo/blob/331b9435c/addons/mrp/models/mrp_bom.py#L372

        In core, though, this field is related to "product_id.uom_id.category_id".
        Here we make it computed to choose between component_template_id and
        product_id, depending on which one is set
        """
        # pylint: disable=missing-return
        # NOTE: To play nice with other modules trying to do the same:
        #   1) Set the field value as if it were a related field (core behaviour)
        #   2) Call super (if it's there)
        #   3) Update only the records we want
        for rec in self:
            rec.product_uom_category_id = rec.product_id.uom_id.category_id
        if hasattr(super(), "_compute_product_uom_category_id"):
            super()._compute_product_uom_category_id()
        for rec in self:
            if rec.component_template_id:
                rec.product_uom_category_id = (
                    rec.component_template_id.uom_id.category_id
                )

    @api.onchange("component_template_id")
    def _onchange_component_template_id(self):
        if self.component_template_id:
            if self.product_id:
                self.product_backup_id = self.product_id
                self.product_id = False
            if (
                self.product_uom_id.category_id
                != self.component_template_id.uom_id.category_id
            ):
                self.product_uom_id = self.component_template_id.uom_id
        else:
            if self.product_backup_id:
                self.product_id = self.product_backup_id
                self.product_backup_id = False
            if self.product_uom_id.category_id != self.product_id.uom_id.category_id:
                self.product_uom_id = self.product_id.uom_id

    @api.depends("component_template_id")
    def _compute_match_on_attribute_ids(self):
        for rec in self:
            if rec.component_template_id:
                rec.match_on_attribute_ids = (
                    rec.component_template_id.attribute_line_ids.attribute_id.filtered(
                        lambda x: x.create_variant != "no_variant"
                    )
                )
            else:
                rec.match_on_attribute_ids = False

    @api.constrains("component_template_id")
    def _check_component_attributes(self):
        for rec in self:
            cmp_tmpl = rec.component_template_id
            if not cmp_tmpl:
                continue
            bom_prod = rec.bom_id.product_tmpl_id
            comp_attrs = cmp_tmpl.valid_product_template_attribute_line_ids.attribute_id
            prod_attrs = bom_prod.valid_product_template_attribute_line_ids.attribute_id
            if not comp_attrs:
                raise ValidationError(
                    _(
                        "No match on attribute has been detected for Component "
                        "(Product Template) %s",
                        cmp_tmpl.display_name,
                    )
                )
            if not all(attr in prod_attrs for attr in comp_attrs):
                raise ValidationError(
                    _(
                        "Some attributes of the dynamic component are not included into"
                        " production product attributes."
                    )
                )

    @api.constrains("component_template_id", "bom_product_template_attribute_value_ids")
    def _check_variants_validity(self):
        for rec in self:
            if (
                not rec.bom_product_template_attribute_value_ids
                or not rec.component_template_id
            ):
                continue
            variant_attrs = rec.bom_product_template_attribute_value_ids.attribute_id
            same_attr_ids = set(rec.match_on_attribute_ids.ids) & set(variant_attrs.ids)
            same_attrs = self.env["product.attribute"].browse(same_attr_ids)
            if same_attrs:
                raise ValidationError(
                    _(
                        "You cannot use an attribute value for attribute(s) "
                        "%(attributes)s in the field “Apply on Variants” as it's the "
                        "same attribute used in the field “Match on Attribute” related "
                        "to the component %(component)s.",
                        attributes=", ".join(same_attrs.mapped("name")),
                        component=rec.component_template_id.name,
                    )
                )

    @api.onchange("match_on_attribute_ids")
    def _onchange_match_on_attribute_ids_check_component_attributes(self):
        if self.match_on_attribute_ids:
            self._check_component_attributes()

    @api.onchange("bom_product_template_attribute_value_ids")
    def _onchange_bom_product_template_attribute_value_ids_check_variants(self):
        if self.bom_product_template_attribute_value_ids:
            self._check_variants_validity()
