# 1: imports of python lib
from datetime import date, datetime, timedelta, time

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api
from odoo.exceptions import UserError as Warning, ValidationError

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwWorkOrder(models.Model):
    _inherit = "tw.work.order"

    # 7: default methods

    # 8: fields
    is_customer_hotline = fields.Boolean(string="Customer Memiliki Hotline?", default=False)
    is_part_hotline = fields.Boolean(string="Is Part Hotline", compute="_compute_is_part_hotline")

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('order_line.part_hotline_id')
    def _compute_is_part_hotline(self):
        for record in self:
            record.is_part_hotline = any(line.part_hotline_id for line in record.order_line)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        onchange = super(TwWorkOrder, self)._onchange_partner_id()
        self.is_customer_hotline = False
        if self.partner_id:
            part_hotline_id = self.env['tw.part.hotline'].search([
                ('customer_id', '=', self.partner_id.id),
                ('state', '=', 'approved')
            ])
            for part_hotline in part_hotline_id:
                for line in part_hotline.part_detail_ids:
                    if line.qty_available > 0 and line.qty_reserved < line.qty_available:
                        self.is_customer_hotline = True
        return onchange

    # 12: override methods
    def write(self, vals):
        res = super(TwWorkOrder, self).write(vals)
        if vals.get('state') == 'done':
            self._check_done_hotline()
        return res

    # 13: action methods
    def action_view_part_hotline(self):
        """View hotline records linked to this WO's order lines."""
        hotline_ids = self.order_line.mapped('part_hotline_id').ids
        if not hotline_ids:
            raise Warning('Part Hotline tidak ditemukan !')
        if len(hotline_ids) == 1:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'tw.part.hotline',
                'view_mode': 'form',
                'target': 'current',
                'res_id': hotline_ids[0],
            }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tw.part.hotline',
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [('id', 'in', hotline_ids)],
        }

    def action_request_approval(self):
        if self.state != 'draft':
            raise UserError(f'Silakan refresh halaman ini, karena state sudah {self._get_state_value()}')
        self._check_qty_available_in_hotline_detail()
        return super(TwWorkOrder, self).action_request_approval()

    def action_approval(self):
        self._check_qty_available_in_hotline_detail()
        return super(TwWorkOrder, self).action_approval()

    # 14: private methods
    def _get_state_value(self):
        # Mengambil value yang sesuai dengan key di state
        selection = self._fields.get('state') and self._fields['state'].selection
        return dict(selection).get(self.state, self.state) if selection else self.state

    def _check_qty_available_in_hotline_detail(self):
        for line in self.order_line:
            if not line.part_hotline_id:
                continue
            for hotline_detail in line.part_hotline_id.part_detail_ids:
                if hotline_detail.product_id == line.product_id:
                    # Jika order ini sudah berstatus WFA ke atas (bukan draft), 
                    # qty dari order ini sudah mengurangi qty_available pada hotline.
                    # Maka kita harus menambahkan kembali qty order ini ke qty_available untuk divalidasi.
                    already_reserved_qty = 0
                    if line.order_id.state not in ['draft', 'cancel', 'unused']:
                        already_reserved_qty = line.product_uom_qty
                        
                    effective_qty_available = hotline_detail.qty_available + already_reserved_qty
                    
                    if effective_qty_available < line.product_uom_qty:
                        raise Warning('Qty Available tidak mencukupi %s pada Hotline %s!' % (line.product_id.display_name, line.part_hotline_id.name))

    def _check_done_hotline(self):
        for hotline in self.order_line.mapped('part_hotline_id'):
            if hotline.part_detail_ids.filtered(lambda x: x.qty_po >= x.qty_reserved):
                hotline.write({'state': 'done'})