# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwWorkOrderClaimLine(models.Model):
    _name = "tw.work.order.claim.line"
    _description = "TW Work Order Claim Line"
    _order = "id desc"
    
    # 7: defaults methods

    # 8: fields
    claim_to = fields.Selection([
        ('customer', 'Customer'),
        ('atpm', 'AHM'),
        ('main_dealer', 'Main Dealer'),
        ('dealer', 'Dealer'),
    ], string='Claim To')
    claim_description = fields.Text(string='Claim Description')

    # 9: relation fields
    claim_id = fields.Many2one('tw.work.order.claim', string='Claim')
    product_id = fields.Many2one('product.product', string='Sparepart', domain=[('categ_id', 'child_of', 'Claim')])
    partner_id = fields.Many2one('res.partner', string='Partner')
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('claim_to')
    def _onchange_claim_to(self):
        self.partner_id = False
        partner_id = False
        for record in self:
            main_dealer_obj = self.env['res.company'].get_default_main_dealer()
            if record.claim_to == 'customer':
                # Partner will be taken from work order header when used
                # Set to False in master configuration
                partner_id = False
            elif record.claim_to == 'atpm':
                partner_id = main_dealer_obj.default_supplier_id or main_dealer_obj.partner_id.id
            elif record.claim_to == 'main_dealer':
                partner_id = main_dealer_obj.partner_id.id
                if not partner_id:
                    raise ValidationError(_("Main Dealer Partner not found for company %s") % record.claim_id.company_id.name)
            elif record.claim_to == 'dealer':
                partner_id = record.claim_id.company_id.partner_id.id
                if not partner_id:
                    raise ValidationError(_("Partner not found for company %s") % record.claim_id.company_id.name)
            
            record.partner_id = partner_id

    # 12: override methods

    # 13: actions

    # 14: menu