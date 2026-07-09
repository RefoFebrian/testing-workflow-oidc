from odoo import models, fields, api, _

    
class ExpeditionPriceLine(models.Model):
    _name = "tw.expedition.price.line"
    _description = "Expedition Price Line"

    cost = fields.Float("Cost")
    expedition_price_id = fields.Many2one("tw.expedition.price", string="Expedition Price", ondelete="cascade")
    product_tmpl_id = fields.Many2one('product.template', "Product")

    _sql_constraints = [
        (
            "unique_product",
            "unique(expedition_price_id, product_tmpl_id)",
            "Duplicate Products, please check again!",
        ),
    ]

    @api.onchange("product_tmpl_id")
    def _onchange_product_tmpl_id(self):
        domain = {}

        category_model = self.env["product.category"]
        categ_unit = category_model.search([("name", "=", "Unit")]).ids
        categ_sparepart = category_model.search([("name", "=", "Sparepart")]).ids
        categ_umum = category_model.search([("name", "=", "Umum")]).ids

        categ_ids = categ_unit + categ_sparepart + categ_umum

        if categ_ids:
            domain["product_tmpl_id"] = [("categ_id", "in", categ_ids)]
        return {"domain": domain}