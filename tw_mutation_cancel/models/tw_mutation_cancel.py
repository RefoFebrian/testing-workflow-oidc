# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api
from odoo.exceptions import UserError as Warning
from odoo.tools.float_utils import float_compare

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwMutationOrderCancel(models.Model):
    _name = "tw.mutation.order.cancel"
    _inherit = ['mail.thread', 'tw.approval.mixin']
    _description = 'Mutation Order Cancel'
    _inherits = {'tw.cancellation': 'cancellation_id'}
    _order = 'id desc'


    # 7: defaults methods
    @api.model
    def _get_default_date(self):
        return datetime.now()

    # 8: fields

    # 9: relation fields
    mutation_order_id = fields.Many2one('tw.mutation.order', 'Mutation Order')
    cancellation_id = fields.Many2one('tw.cancellation', required=True, ondelete='cascade')

    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    @api.onchange('mutation_order_id')
    def _onchange_mutation_order_id(self):
        if self.mutation_order_id:
            self.transaction_name = self.mutation_order_id.name
        else:
            self.transaction_name = False
                

    # 12: override methods
    def unlink(self):
        for record in self:
            if record.state and record.state != 'draft':
                raise Warning('Warning! \nCannot delete records with a state other than draft!')
            else:
                raise Warning('Warning! \nCannot delete records!')

        return super(TwMutationOrderCancel, self).unlink()

    # 13: action methods

    # 14: private methods

    _sql_constraints = [
        ('unique_mutation_order_id', 'unique(mutation_order_id)', 'Mutation Order pernah diinput sebelumnya !')
    ]
    
    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if vals.get('mutation_order_id'):
                mo_id = self.env['tw.mutation.order'].browse(vals['mutation_order_id'])
                vals['transaction_name'] = mo_id.name
                name = "X" + mo_id.name
                self._check_duplicate_transaction(name)
                vals['name'] = "X" + mo_id.name
                vals['date'] = self._get_default_date()
        return super(TwMutationOrderCancel, self).create(vals_list)

    def action_confirm(self):
        if self.state == 'approved' and self.mutation_order_id:
            self.validity_check()
            self.picking_cancel()
            # Set Mutation Order state to 'cancelled'
            self.mutation_order_id.sudo().action_cancel()
            
            # Also cancel related Stock Distribution and Mutation Request
            self.sudo()._cancel_related_documents()
            
            return self.cancellation_id.action_confirm()

    def _cancel_related_documents(self):
        """Cancel related Stock Distribution and Mutation Request when MO is cancelled.
        
        This method handles safe dependency checking for mutation_request_id field
        which may not exist if tw_mutation_request module is not installed.
        """
        mo = self.mutation_order_id
        if not mo:
            return
            
        # Cancel Stock Distribution if exists
        sd = mo.stock_distribution_id
        if sd and sd.state not in ('done', 'cancel'):
            sd.sudo().write({
                'state': 'cancel',
                'cancel_uid': self.env.uid,
                'cancel_date': datetime.now(),
            })
            
            # Cancel Mutation Request if the field exists (safe dependency handling)
            if hasattr(sd, 'mutation_request_id') and sd.mutation_request_id:
                mr = sd.mutation_request_id
                if mr.state not in ('done', 'cancel'):
                    mr.sudo().write({
                        'state': 'cancel',
                        'cancel_uid': self.env.uid,
                        'cancel_date': datetime.now(),
                    })

    def action_view_mutation_order(self):
        """Open the linked Mutation Order record."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Mutation Order',
            'res_model': 'tw.mutation.order',
            'view_mode': 'form',
            'res_id': self.mutation_order_id.id,
        }

    def action_request_approval(self):
        return super().action_request_approval(value=5)
        
    def check_shipments(self):
        """Pastikan stock mutasi sudah kembali ke lokasi internal asal.

        Berlaku untuk alur multi-step maupun mutasi balik:
        - Internal -> Internal: kurangi saldo lokasi asal, tambah lokasi tujuan.
        - Internal -> Transit/External: kurangi saldo lokasi asal.
        - Transit/External -> Internal: tambah saldo lokasi tujuan.

        Jika masih ada saldo negatif pada lokasi internal, berarti stock belum
        kembali seluruhnya ke lokasi asal sehingga mutation cancel harus diblok.
        """
        picking_ids = self.mutation_order_id.picking_ids.filtered(lambda p: p.state != 'cancel')
        qty_by_product_location = {}

        for picking in picking_ids:
            if picking.state == 'done':
                for move in picking.move_ids:
                    product = move.product_id
                    move_qty = move.product_uom_qty

                    if move.location_id.usage == 'internal':
                        key = (product, move.location_id)
                        qty_by_product_location[key] = qty_by_product_location.get(key, 0.0) - move_qty

                    if move.location_dest_id.usage == 'internal':
                        key = (product, move.location_dest_id)
                        qty_by_product_location[key] = qty_by_product_location.get(key, 0.0) + move_qty

        products = set()
        for (product, _location), value in qty_by_product_location.items():
            if float_compare(value, 0.0, precision_rounding=product.uom_id.rounding) < 0:
                products.add(product.display_name or product.name)

        if products:
            raise Warning(
                "Transaksi tidak bisa dicancel!\n"
                "Product %s sudah ditransfer dan belum kembali seluruhnya ke lokasi asal, "
                "Silahkan return picking terlebih dahulu!\n"
                "atau melakukan mutasi balik jika product tersebut sudah selesai diterima oleh Dealer Tujuan!"
                % ", ".join(sorted(products))
            )
        return True

    def picking_cancel(self):
        picking_ids = self.mutation_order_id.picking_ids.filtered(lambda picking: picking.state not in ('done', 'cancel'))
        for picking_id in picking_ids:
            picking_id.action_cancel()

    def validity_check(self):
        self.check_shipments()

    def _check_duplicate_transaction(self,name):
        return self.cancellation_id._check_duplicate_transaction(name)
