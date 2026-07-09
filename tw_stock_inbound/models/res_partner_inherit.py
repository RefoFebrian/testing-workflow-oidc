from odoo import models, fields, api


class ResPartnerInherit(models.Model):
    """Inherit res.partner to add expedition-specific fields."""

    _inherit = "res.partner"

    # -------------------------------------------------------------------------
    # FIELDS
    # -------------------------------------------------------------------------
    is_expedition = fields.Boolean(compute='_compute_is_expedition', store=True)
    pricelist_expedition_unit_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Pricelist Unit',
        company_dependent=True,
        domain=[('type', '=', 'expedition')],
        help="Pricelist khusus ekspedisi untuk divisi Unit.",
    )
    pricelist_expedition_sparepart_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Pricelist Sparepart',
        company_dependent=True,
        domain=[('type', '=', 'expedition')],
        help="Pricelist khusus ekspedisi untuk divisi Sparepart.",
    )

    # -------------------------------------------------------------------------
    # COMPUTE
    # -------------------------------------------------------------------------
    @api.depends('category_id')
    def _compute_is_expedition(self):
        """Compute whether this partner is categorized as an expedition."""
        expedition_category = self.env.ref('tw_stock_inbound.contact_tags_expedition', raise_if_not_found=False)
        for partner in self:
            partner.is_expedition = expedition_category in partner.category_id if expedition_category else False
