# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command
from odoo.tools import SQL

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning, ValidationError

# 5: local imports

# 6: Import of unknown third party lib


_logger = logging.getLogger(__name__)

class TWCRMLeadInherit(models.Model):
    _inherit = "tw.lead"

    # 7: defaults methods

    # 8: fields
    spk_count = fields.Integer(compute='_compute_spk_count')

    # 9: relation fields
    spk_id = fields.Many2one(comodel_name='tw.dealer.spk', string='SPK', copy=False)

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    def _compute_spk_count(self):
        for lead in self:
            lead.spk_count = lead.env['tw.dealer.spk'].search_count([('lead_reference', '=', lead.name)])

    # 12: override methods

    # 13: action methods
    def action_create_spk(self):
        """ Creates a new SPK for the lead if it does not already exist. """
        self.ensure_one()
        existing_spk = self.env['tw.dealer.spk'].search([
            ('lead_reference', '=', self.name), 
            ('lead_id', '=', self.id),
            ('state', '!=', 'cancelled')])
        if existing_spk:
            existing_spk_names = ', '.join(existing_spk.mapped('name'))
            raise Warning(_(f"You must cancel the following existing SPK(s): {existing_spk_names} before creating a new one!"))
        
        try:
            spk = self._create_spk()  # Create SPK if it doesn't exist
        except Exception as e:
            _logger.error(e.__class__.__name__)
            raise Warning(_(f"Failed to create SPK: {str(e)}"))
        
        if spk:
            self.write({ 'state': 'spk', 'spk_id': spk.id })

    def action_view_spk(self):
        """ Opens the SPK associated with the lead in a form view. """
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'name': _('SPK'),
            'res_model': 'tw.dealer.spk',
            'view_mode': 'list,form',
            'target': 'current',
        }
        spk = self.env['tw.dealer.spk'].search([('lead_reference', '=', self.name)])
        if len(spk) > 1:
            action['view_mode'] = 'list,form'
            action['domain'] = [('id', 'in', spk.ids)]
        else:
            action['view_mode'] = 'form'
            action['res_id'] = spk.id
        
        return action

    # 14: private methods
    def _create_spk(self):
        """ Creates a new SPK for the lead if it does not already exist. """
        if self.state != 'spk':
            spk_vals = {
                'division': 'Unit',
                'date_order': date.today(),
                'delivery_address': self.partner_id and self.partner_id.contact_address or '',
                'identification_number': self.identification_number,
                'company_id': self.company_id.id,
                'partner_id': self.partner_id.id,
                'finco_id': self.finco_id.id,
                'sales_id': self.sales_id.id,
                'sales_coordinator_id': self.sales_coordinator_id.id,
                'sales_channel_id': self.sales_channel_id.id,
                'sales_source_location_id': self.sales_source_location_id.id,
                'lead_reference': self.name,
                'payment_type_id': self.payment_type_id.id,
                'lead_id': self.id,
                'line_ids': [Command.create({
                    'product_qty': 1,
                    'is_bbn': self.finco_id and True or False,
                    'down_payment': self.down_payment or 0.0,
                    'tenor': self.tenor or 0,
                    'installment': self.installment or 0.0,
                    'discount': self.discount or 0.0,
                    'partner_stnk_id': self.partner_stnk_id.id,
                    'product_id': self.product_id.id
                })],
            }
            spk = self.env['tw.dealer.spk'].create(spk_vals)
            if not spk:
                raise Warning(_("Failed to create SPK for the lead."))
            
            return spk
    
    def _get_spk(self):
        """ Retrieves the SPK associated with the lead. """
        if not self.spk_id:
            self._create_spk()
        return self.spk_id
