import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round

_log = logging.getLogger(__name__)


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    # flake8: noqa: C901
    def explode(
        self, product, quantity, picking_type=False, never_attribute_values=False
    ):
        # Had to replace this method
        """
        Explodes the BoM and creates two lists with all the information you need:
        bom_done and line_done
        Quantity describes the number of times you need the BoM: so the quantity
        divided by the number created by the BoM
        and converted into its UoM
        """
        from collections import defaultdict

        graph = defaultdict(list)
        V = set()

        def check_cycle(v, visited, recStack, graph):
            visited[v] = True
            recStack[v] = True
            for neighbour in graph[v]:
                if visited[neighbour] is False:
                    if check_cycle(neighbour, visited, recStack, graph) is True:
                        return True
                elif recStack[neighbour] is True:
                    return True
            recStack[v] = False
            return False

        product_ids = set()
        product_boms = {}

        def update_product_boms():
            products = self.env["product.product"].browse(product_ids)
            product_boms.update(
                self._bom_find(
                    products,
                    bom_type="phantom",
                    picking_type=picking_type or self.picking_type_id,
                    company_id=self.company_id.id,
                )
            )
            # Set missing keys to default value
            for product in products:
                product_boms.setdefault(product, self.env["mrp.bom"])

        boms_done = [
            (
                self,
                {
                    "qty": quantity,
                    "product": product,
                    "original_qty": quantity,
                    "parent_line": False,
                },
            )
        ]
        lines_done = []
        V |= {product.product_tmpl_id.id}

        bom_lines = []
        for bom_line in self.bom_line_ids:
            product_id = bom_line.product_id
            V |= {product_id.product_tmpl_id.id}
            graph[product.product_tmpl_id.id].append(product_id.product_tmpl_id.id)
            bom_lines.append((bom_line, product, quantity, False))
            product_ids.add(product_id.id)
        update_product_boms()
        product_ids.clear()
        while bom_lines:
            current_line, current_product, current_qty, parent_line = bom_lines[0]
            bom_lines = bom_lines[1:]

            if current_line._skip_bom_line(current_product, never_attribute_values):
                continue

            line_quantity = current_qty * current_line.product_qty
            if current_line.product_id not in product_boms:
                update_product_boms()
                product_ids.clear()
            # upd start
            component_template_product = self._get_component_template_product(
                current_line, product, current_line.product_id
            )
            if component_template_product:
                # need to set product_id temporary
                current_line.suspend_security().product_id = component_template_product
            else:
                # component_template_id is set, but no attribute value match.
                continue
            # upd end
            bom = product_boms.get(current_line.product_id)
            if bom:
                converted_line_quantity = current_line.product_uom_id._compute_quantity(
                    line_quantity / bom.product_qty, bom.product_uom_id
                )
                bom_lines += [
                    (
                        line,
                        current_line.product_id,
                        converted_line_quantity,
                        current_line,
                    )
                    for line in bom.bom_line_ids
                ]
                for bom_line in bom.bom_line_ids:
                    graph[current_line.product_id.product_tmpl_id.id].append(
                        bom_line.product_id.product_tmpl_id.id
                    )
                    if bom_line.product_id.product_tmpl_id.id in V and check_cycle(
                        bom_line.product_id.product_tmpl_id.id,
                        {key: False for key in V},
                        {key: False for key in V},
                        graph,
                    ):
                        raise UserError(
                            _(
                                "Recursion error!  A product with a Bill of Material "
                                "should not have itself in its BoM or child BoMs!"
                            )
                        )
                    V |= {bom_line.product_id.product_tmpl_id.id}
                    if bom_line.product_id not in product_boms:
                        product_ids.add(bom_line.product_id.id)
                boms_done.append(
                    (
                        bom,
                        {
                            "qty": converted_line_quantity,
                            "product": current_product,
                            "original_qty": quantity,
                            "parent_line": current_line,
                        },
                    )
                )
            else:
                # We round up here because the user expects
                # that if he has to consume a little more, the whole UOM unit
                # should be consumed.
                rounding = current_line.product_uom_id.rounding
                line_quantity = float_round(
                    line_quantity, precision_rounding=rounding, rounding_method="UP"
                )
                lines_done.append(
                    (
                        current_line,
                        {
                            "qty": line_quantity,
                            "product": current_product,
                            "original_qty": quantity,
                            "parent_line": parent_line,
                        },
                    )
                )
        return boms_done, lines_done

    def _get_component_template_product(
        self, bom_line, bom_product_id, line_product_id
    ):
        if bom_line.component_template_id:
            comp = bom_line.component_template_id
            comp_attr_ids = (
                comp.valid_product_template_attribute_line_ids.attribute_id.ids
            )
            valid_ptal = bom_product_id.valid_product_template_attribute_line_ids
            prod_attr_ids = valid_ptal.attribute_id.ids
            # check attributes
            if not all(item in prod_attr_ids for item in comp_attr_ids):
                _log.info(
                    "Component skipped. Component attributes must be included into "
                    "product attributes to use component_template_id."
                )
                return False
            # find matching combination
            combination = self.env['product.template.attribute.value']
            for ptav in bom_product_id.product_template_attribute_value_ids:
                combination |= self.env['product.template.attribute.value'].search(
                    [
                        ("product_tmpl_id", "=", comp.id),
                        ("attribute_id", "=", ptav.attribute_id.id),
                        (
                            "product_attribute_value_id",
                            "=",
                            ptav.product_attribute_value_id.id,
                        ),
                    ]
                )
            if len(combination) == 0:
                return False
            product_id = comp._get_variant_for_combination(combination)
            if product_id and product_id.active:
                return product_id
            return False
        else:
            return line_product_id

    @api.constrains("product_tmpl_id", "product_id")
    def _check_component_attributes(self):
        return self.bom_line_ids._check_component_attributes()

    @api.constrains("product_tmpl_id", "product_id")
    def _check_variants_validity(self):
        return self.bom_line_ids._check_variants_validity()
