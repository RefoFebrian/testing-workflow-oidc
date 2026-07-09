# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwWorkOrderLine(models.Model):
    _inherit = "tw.work.order.line"

    # 8: fields
    
    # 9: relation fields
    claim_partner_id = fields.Many2one('res.partner', string='Claim Partner', 
                                       help='Partner for claim invoice based on claim line configuration')

    # 11: compute/depends & on change methods
    @api.onchange('product_id', 'location_id', 'product_uom_qty')
    def _onchange_product_id_warning(self):
        """
        Override to auto-populate claim_partner_id when product is selected
        in a claim type work order. Exact branch first, then parent company.
        """
        product_warning = super(TwWorkOrderLine, self)._onchange_product_id_warning()
        if product_warning:
            return product_warning

        self.claim_partner_id = False
        if not (self.order_id.claim_type_id and self.product_id):
            return

        order = self.order_id
        base_domain = order._build_claim_base_domain(order.claim_type_id.id)
        claim_obj = order._search_claim(base_domain, [('unit_apply_on', '!=', False)])
        if not claim_obj:
            return

        # Find matching claim line for this sparepart product
        claim_line = claim_obj.claim_line_ids.filtered(
            lambda l: l.product_id.id == self.product_id.id
        )
        if not claim_line:
            return

        # Set claim_partner_id based on claim_to
        if claim_line[0].claim_to == 'customer':
            self.claim_partner_id = order.partner_id.id
        else:
            self.claim_partner_id = claim_line[0].partner_id.id

    # 12: override methods
    # No override needed for _prepare_invoice_line
    # claim_partner_id is only used for grouping, not stored in invoice line
