# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.osv import expression
from datetime import date

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
import logging
_logger = logging.getLogger(__name__)
# 5: local imports

# 6: Import of unknown third party lib

class InheritStockPickingBatchNRFS(models.Model):
    _inherit = "stock.picking.batch"

    # 7: defaults methods
    def _get_default_nrfs_location_id(self):
        domain = [
            ('type_id.value', '=', 'nrfs'),
            ('company_id', '=', self.env.company.id)
        ]
        if self.division:
            domain.append(('division', '=', self.division))
            
        location = self.env['stock.location'].search(domain, limit=1)
        return location.id if location else False

    # 8: fields
    has_nrfs = fields.Selection([
        ('have_nrfs', 'Have NRFS'),
        ('no_nrfs', 'No NRFS')
    ], string='Has NRFS', default='no_nrfs', compute='_compute_has_nrfs')
    
    # 9: relation fields
    nrfs_location_id = fields.Many2one(comodel_name='stock.location', string='NRFS Location', default=lambda self: self._get_default_nrfs_location_id(), help='Location for NRFS')
    
    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    @api.depends('batch_line_ids.is_rfs', 'move_line_ids.is_rfs')
    def _compute_has_nrfs(self):
        for record in self:
            record.has_nrfs = 'no_nrfs'
            check_nrfs_batch_line = record.batch_line_ids.filtered(lambda x: not x.is_rfs)
            check_nrfs_move_line = record.move_line_ids.filtered(lambda x: not x.is_rfs)
            if check_nrfs_batch_line or check_nrfs_move_line:
                record.has_nrfs = 'have_nrfs'

    # 12: override methods
    
    # 13: action methods
    def action_done(self):
        if self.state != 'in_progress':
            raise UserError(f'Silakan refresh halaman ini, karena state telah {self._get_state_value()}')
        for record in self:
            if record.has_nrfs == 'have_nrfs':
                for source_picking in record.source_picking_ids:
                    # TODO: Confirm Division pada Stock Location / buat method get location berdasarkan division sama tipe 
                    nrfs_location = self.env['stock.location'].search([('type_id.value','=','nrfs')],limit=1)
                    if not nrfs_location:
                        raise Warning("NRFS Location Not Found!")
                    source_picking.nrfs_location_id = nrfs_location.id
                    record._update_location_nrfs(source_picking)
        return super(InheritStockPickingBatchNRFS,self).action_done()

    # 14: private methods
    def _update_location_nrfs(self, picking):
        company_warehouse = self.env['stock.warehouse']._get_company_warehouse(self.company_id)
        for move_line in self.move_line_ids:
            if not move_line.is_rfs:
                if not picking.nrfs_location_id:
                    raise Warning("Please fill in the NRFS Location first!")

                if company_warehouse.reception_steps in ['three_steps', 'two_steps'] and (move_line.location_id.id == company_warehouse.wh_qc_stock_loc_id.id or move_line.location_id.id == company_warehouse.wh_input_stock_loc_id.id):
                    move_line.location_qc_id = picking.nrfs_location_id.id
                else:
                    move_line.location_dest_id = picking.nrfs_location_id.id
      
    def _prepare_batch_picking_vals(self):
        vals = super()._prepare_batch_picking_vals()
        if self.nrfs_location_id:
            vals['nrfs_location_id'] = self.nrfs_location_id.id
        return vals
    
    def _prepare_create_batch_vals(self, picking_ids, picking_type_id):
        vals = super()._prepare_create_batch_vals(picking_ids, picking_type_id)
        if self.nrfs_location_id:
            vals['nrfs_location_id'] = self.nrfs_location_id.id
        return vals
            
        