# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class InheritNrfsMutationInternal(models.Model):
    _inherit = "tw.nrfs"
    
    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    picking_id = fields.Many2one('stock.picking', string='Picking')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_validate(self):
        if self.claim_type in ['item', 'disposal']:
            location_dest_id = False
            if self.claim_type == 'disposal':
                location_dest_obj = self.env['stock.location'].suspend_security().search([
                    ('company_id', '=', self.company_id.id),
                    ('division', '=', self.division),
                    ('scrap_location', '=', True),
                ], limit=1)
                if not location_dest_obj:
                    raise Warning(f"Destination Location Scrap for branch '{self.company_id.name}' and division '{self.division}' not found!")
                
                location_dest_id = location_dest_obj.id
            self.action_create_internal_transfer(location_dest_id)
        return super(InheritNrfsMutationInternal, self).action_validate()

    def action_open_internal_transfer(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'view_id': self.env.ref('tw_mutation_internal.tw_mutation_internal_form_view').id,
            'res_id': self.picking_id.id
        }

    def action_create_internal_transfer(self, location_dest_id=None):
        warehouse = self.company_id.suspend_security().warehouse_id
        if not warehouse:
            raise Warning(f"Please configure a warehouse for branch '{self.company_id.name}' first.")
        
        picking_type_obj = warehouse.int_type_id
        location_id = self.env['stock.location'].suspend_security().search([
            ('type_id.value', 'in', ['NRFS', 'nrfs']),
            ('company_id', '=', self.company_id.id),
            ('division', '=', self.division),
        ], limit=1).id
        if not location_id:
            raise Warning(f"Source Location NRFS for branch '{self.company_id.name}' and division '{self.division}' not found!")
        
        try:
            picking_vals = {
                'company_id': self.company_id.id,
                'division': self.division,
                'date': date.today(),
                'origin': self.name,
                'picking_type_id': picking_type_obj.id,
                'location_id': location_id
            }

            picking_line_vals = []
            if not self.nrfs_type:
                for line in self.line_ids:
                    location_dest_id = self._get_location_dest_id(line.product_sparepart_id, self.company_id.id, self.division)
                    picking_line = {
                        'product_id': line.product_sparepart_id.id,
                        'location_id': location_id,
                        'location_dest_id': location_dest_id,
                        'quantity': line.qty
                    }
                    if line.lot_id:
                        picking_line['lot_id'] = line.lot_id.id
                    picking_line_vals.append((0, 0, picking_line))
            else:
                location_dest_id = self._get_location_dest_id(self.product_id, self.company_id.id, self.division)
                picking_line = {
                    'product_id': self.product_id.id,
                    'lot_id': self.lot_id.id,
                    'location_id': location_id,
                    'location_dest_id': location_dest_id,
                    'quantity': 1
                }
                picking_line_vals.append((0, 0, picking_line))
            
            if picking_line_vals:
                picking_vals['picking_line_ids'] = picking_line_vals
            picking_vals['location_dest_id'] = location_dest_id
                
            picking_obj = self.env['stock.picking'].suspend_security().with_company(self.company_id).create(picking_vals)
            picking_obj.action_renew_available()

        except Exception as e:
            raise Warning(f"Error creating internal transfer: {str(e)}")
        
        self.write({'picking_id': picking_obj.id})

    # 14: private methods
    def _get_location_dest_id(self, product_id, company_id, division):
        """
            Mencari Lokasi tujuan yang ready for sale dengan lokasi available berdasarkan product
        """
        location_dest_ids = self.env['stock.quant'].with_company(company_id).sudo()._get_location_available_by_product(product_id, company_id)
        if not location_dest_ids:
            location_dest_obj = self.env['stock.location'].suspend_security().search([
                ('type_id.value', 'in', ['RFS', 'rfs']),
                ('company_id', '=', company_id),
                ('division', '=', division),
            ], limit=1)
            if not location_dest_obj:
                raise Warning(f"Destination Location Stock RFS for branch '{self.company_id.name}' and division '{self.division}' not found!")
            return location_dest_obj.id
        return location_dest_ids[0]
        
