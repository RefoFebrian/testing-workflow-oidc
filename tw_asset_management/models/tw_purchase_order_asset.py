# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.osv import expression

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import float_compare

# 5: local imports

# 6: Import of unknown third party lib

class InheritPurchaseOrderAsset(models.Model):
    _name = "purchase.order.asset"
    _inherit = "purchase.order" 
    _description = "Purchase Order Asset"
    _order = 'id desc'

    # 7: defaults methods

    # 8: fields
    state = fields.Selection(selection_add=[
        ('open','Open'),
        ('partial_received','Partial Received'),
        ('received','Received'),
        ('partial_payment','Partial Payment'),
        ('payment','Payment'),
        ('purchase',),
    ])
    po_type = fields.Selection(selection=lambda self: self.env['tw.selection'].get_option_list('PoTypeAssets'))

    # Collecting Check 
    collecting_count = fields.Integer(compute="_compute_collecting", string='Collecting Count', copy=False, default=0, store=True)
    collecting_ids = fields.Many2many('tw.good.receive.collecting', compute="_compute_collecting", string='Collectings', copy=False, store=True)
    
    # Good Receive Check
    good_receive_count = fields.Integer(compute="_compute_good_receive", string='Good Receive Count', copy=False, default=0, store=True)
    good_receive_ids = fields.Many2many('tw.good.receive.asset.line', compute="_compute_good_receive", string='Good Receive', copy=False, store=True)

    # * Audit Trail
    confirm_date = fields.Datetime('Confirmed on')
    confirm_uid = fields.Many2one('res.users',string="Confirmed by")

    received_date = fields.Datetime('Received on')
    received_uid = fields.Many2one('res.users',string="Received by")

    payment_date = fields.Datetime('Payment on')
    payment_uid = fields.Many2one('res.users',string="Payment by")
    
    paid_date = fields.Datetime('Paid on')
    paid_uid = fields.Many2one('res.users',string="Paid by")
    
    partial_received_date = fields.Datetime('Partial Received on')
    partial_received_uid = fields.Many2one('res.users',string="Partial Received by")
    
    partial_payment_date = fields.Datetime('Partial Payment on')
    partial_payment_uid = fields.Many2one('res.users',string="Partial Payment by")

    # 9: relation fields   
    order_line = fields.One2many('purchase.order.asset.line', 'order_id', string='Order Asset Lines', copy=True)

    # 10: constraints & sql constraints
    @api.constrains('order_line')
    def _check_duplicate_product(self):
        """Override parent constraint: allow duplicate products if CIP asset."""
        for order in self:
            # Filter non-CIP lines only for duplicate check
            non_cip_lines = order.order_line.filtered(
                lambda l: l.product_id and not l.display_type and not l.is_cip
            )
            product_ids = [line.product_id.id for line in non_cip_lines]
            if len(product_ids) != len(set(product_ids)):
                seen = set()
                duplicates = []
                for line in non_cip_lines:
                    if line.product_id.id in seen:
                        duplicates.append(line.product_id.display_name)
                    seen.add(line.product_id.id)
                raise Warning(_(
                    "Duplicate products are not allowed in Purchase Order Asset.\n"
                    "Duplicate product(s): %s\n"
                    "Please consolidate quantities for the same product into a single line.\n"
                    "Note: Product CIP diperbolehkan duplikat."
                ) % ', '.join(set(duplicates)))

    # 11: compute/depends & on change methods
    @api.depends('state')
    def _compute_collecting(self):
        for order in self:
            collectings = order.env['tw.good.receive.collecting.line'].search([('purchase_order_id', '=', order.id), ('collecting_id.state', '!=', 'draft')])
            if collectings:
                collectings = collectings.mapped('collecting_id')
                order.collecting_ids = collectings.ids
                order.collecting_count = len(collectings)
            else:
                order.collecting_ids = False
                order.collecting_count = 0
    
    @api.depends('state')
    def _compute_good_receive(self):
        for order in self:
            good_receives = order.env['tw.good.receive.asset.line'].search([('purchase_order_id', '=', order.id), ('picking_id.state', '!=', 'draft')])
            if good_receives:
                order.good_receive_ids = good_receives.ids
                order.good_receive_count = len(good_receives)
            else:
                order.good_receive_ids = False
                order.good_receive_count = 0

    @api.onchange('date_planned')
    def _onchange_date_planned(self):
        for order in self:
            if order.date_planned:
                date_planned = order.date_planned.date()
                if date_planned < order.date_order.date():
                    raise Warning(_("Date Planned cannot be in the past."))
    
    @api.onchange('start_date','end_date')
    def _onchange_date_asset(self):
        for order in self:
            if order.start_date and order.end_date:
                if order.start_date > order.end_date:
                    raise Warning(_("Start Date cannot be greater than End Date."))
                
                if order.start_date < order.date_order.date():
                    raise Warning(_("Start Date cannot be in the past."))
                
                if order.end_date < order.date_order.date():
                    raise Warning(_("End Date cannot be in the past."))
    
    @api.onchange('date_order')
    def _onchange_date_order_asset(self):
        for order in self:
            if order.date_order:
                date_order = order.date_order.date()
                if date_order < fields.Date.today():
                    raise Warning(_("Date Order cannot be in the past."))
    
    @api.onchange('company_id', 'division')
    def _onchange_branch_division(self):
        self.picking_type_id = False
        stock_picking_type = self.env['stock.picking.type']
        if self.company_id and self.division:
            picking_type = stock_picking_type.get_picking_type_asset('incoming', self.company_id.id, 'Umum')
            self.picking_type_id = picking_type

    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list):
        for values in vals_list:
            # Give sequence name
            company_id = values.get('company_id', self.default_get(['company_id'])['company_id'])
            branch_obj = self.env['res.company'].browse(company_id)
            if values.get('name', 'New') == 'New':
                seq_name = self.with_company(company_id).env['ir.sequence'].get_sequence_code('POA', branch_obj.code)
                values['name'] = seq_name 
            
        create = super(InheritPurchaseOrderAsset, self).create(vals_list)
        create._check_qty_order()
        create._check_date_in_order()
        return create

    def get_formview_action(self, access_uid=None):
        """ Override this method to add access control for user form view """
        user = self.env.user
        if access_uid:
            user = self.env['res.users'].browse(access_uid).sudo()
        if not user.has_group('tw_asset_management.group_purchase_order_asset_read'):
            raise AccessError(_("You do not have access to this document."))
            
        res = super().get_formview_action(access_uid=access_uid)
        return res

    # 13: action methods
    def action_confirm(self):
        for order in self:
            if order.state not in ('draft','approved'):
                raise UserError(f'Silakan refresh halaman PO Asset ini, karena state sudah {self._get_state_value()}')
            else:
                order.write({
                    'state': 'open',
                    'confirm_uid': self._uid,
                    'confirm_date': datetime.now()
                })
                
        return True

    def action_purchase_order_list(self, type):
        action = super(InheritPurchaseOrderAsset, self).action_purchase_order_list(type)
        if type == 'Asset':
            search_view = self.env.ref('tw_asset_management.tw_inherit_purchase_order_asset_search_view')
            action['search_view_id'] = search_view.id
            action['domain'] = [('division', '=', 'Umum')]
            action['context'] = {
                'view_type': 'form',
                'default_division': 'Umum',
                'is_asset': True,
                'readonly_by_pass': True
            }
        return action
    
    def action_view_good_receive(self):
        picking_ids = self._check_purchase_order_asset()
        if not picking_ids:
            raise Warning(_("No Good Receive found for this Purchase Order."))

        result = self.env['ir.actions.act_window']._for_xml_id('tw_asset_management.tw_good_receive_asset_action')
        if len(picking_ids) > 1:
            result['domain'] = [('id', 'in', picking_ids.ids)]
        elif len(picking_ids) == 1:
            res = self.env.ref('tw_asset_management.tw_inherit_good_receive_asset_1_form_view', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = picking_ids.id
        else:
            result = {'type': 'ir.actions.act_window_close'}
            
        return result

    def action_view_collecting(self, collecting=False):
        if not collecting:
            self.invalidate_model(['collecting_ids'])
            collecting = self.collecting_ids

        result = self.env['ir.actions.act_window']._for_xml_id('tw_good_receive.action_good_receive_collecting')
        # choose the view_mode accordingly
        if len(collecting) > 1:
            result['domain'] = [('id', 'in', collecting.ids)]
        elif len(collecting) == 1:
            res = self.env.ref('account.view_move_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = collecting.id
        else:
            result = {'type': 'ir.actions.act_window_close'}

        return result

    # 14: private methods
    def _get_actions_act_window(self):
        is_asset = self.env.context.get('is_asset', False)
        if is_asset:
            list_view = self.env.ref('tw_asset_management.tw_purchase_order_asset_list_view')
            form_view = self.env.ref('tw_asset_management.tw_inherit_purchase_order_asset_form_view')
            search_view = self.env.ref('tw_asset_management.tw_inherit_purchase_order_asset_search_view')

            return {
                'name': _("Purchase Order Asset"),
                'view_mode': 'list,form',
                'views' : [(list_view.id, 'list'), (form_view.id, 'form')],
                'search_view_id' : search_view.id,
                'res_model': 'purchase.order.asset',
                'type': 'ir.actions.act_window',
                'target': 'current',
            }
        else:
            return super(InheritPurchaseOrderAsset, self)._get_actions_act_window()
        
    def _check_purchase_order_asset(self):
        """ 
            Check if the purchase order has any Good Receive associated with it.
        """
        good_receive_ids = []
        check_gr_line = self.env['tw.good.receive.asset.line'].search([('purchase_order_id', '=', self.id)])
        good_receive_ids = check_gr_line.mapped('picking_id')
        return good_receive_ids
    
    def _check_qty_order(self):
        po_line = self.order_line.filtered(lambda x: x.state == 'draft' and not x.display_type)
        for data in po_line:
            if data.product_qty <= 0:
                raise Warning(_("Quantity Order cannot be less than or equal to 0."))

        return True
    
    def _check_date_in_order(self):
        message = ''
        for order in self:
            if order.date_order:
                date_order = order.date_order.date()
                if date_order < fields.Date.today():
                    message += _("Date Order cannot be in the past. \n")
            
            if order.start_date and order.end_date:
                if order.start_date > order.end_date:
                    message += _("Start Date cannot be greater than End Date. \n")
                
                if order.start_date < order.date_order.date():
                    message += _("Start Date cannot be in the past. \n")
                
                if order.end_date < order.date_order.date():
                    message += _("End Date cannot be in the past. \n")


        if message:
            raise Warning(message)

        return True
    

    # 14: private methods
    def action_check_received(self):
        """
        Method ini dipanggil dari Good Receive (GR) dan Good Receive Collecting (GRC)
        untuk memperbarui status Purchase Order Asset (POA) berdasarkan kuantitas
        yang diterima dan yang telah dibayar.
        Logika diadaptasi dari Odoo 8 dengan penyesuaian model Odoo 18.
        """
        for order in self:
            if order.state in ('draft', 'cancel'):
                continue

            total_ordered = 0
            total_received = 0
            total_paid = 0

            # Loop melalui setiap baris PO untuk mengakumulasi kuantitas
            for line in order.order_line:
                total_ordered += line.product_qty

                # --- 1. Hitung Kuantitas yang Diterima (Received) ---
                # Cari semua baris GR yang tervalidasi ('done') untuk PO line ini
                gr_lines = self.env['tw.good.receive.asset.line'].search([
                    ('purchase_order_line_id', '=', line.id),
                    ('state', '=', 'open')
                ])
                qty_received_for_line = sum(gr_lines.mapped('qty'))
                total_received += qty_received_for_line

                # --- 2. Hitung Kuantitas yang Sudah Dibayar (Paid) ---
                # Cari baris GRC yang statusnya 'done' yang merujuk ke gr_lines di atas
                if gr_lines:
                    grc_lines = self.env['tw.good.receive.collecting.line'].search([
                        ('collecting_good_receive_id', 'in', gr_lines.ids),
                        ('collecting_good_receive_id.state', '=', 'done')
                    ])
                    qty_paid_for_line = sum(grc_lines.mapped('qty'))
                    total_paid += qty_paid_for_line
            
            # --- 3. Tentukan State Baru Berdasarkan Akumulasi Total ---
            new_state = order.state
            vals_to_write = {}

            # Gunakan float_compare untuk perbandingan angka desimal yang aman
            is_fully_received = float_compare(total_received, total_ordered, precision_digits=2) >= 0
            is_partially_received = not is_fully_received and total_received > 0
            
            is_fully_paid = float_compare(total_paid, total_ordered, precision_digits=2) >= 0
            is_partially_paid = not is_fully_paid and total_paid > 0

            # Logika penentuan state secara hierarkis (dari yang paling tinggi ke rendah)
            if is_fully_paid:
                new_state = 'payment' # State untuk Lunas/Paid
            elif is_partially_paid:
                new_state = 'partial_payment'
            elif is_fully_received:
                new_state = 'received'
            elif is_partially_received:
                new_state = 'partial_received'
            else:
                # Jika tidak ada yang diterima, kembali ke 'open'
                new_state = 'open'
            
            # Hanya lakukan 'write' jika ada perubahan state
            if new_state != order.state:
                vals_to_write['state'] = new_state
                
                # Update jejak audit (audit trail) sesuai dengan state baru
                now = datetime.now()
                user_id = self.env.user.id

                if new_state == 'payment' and not order.paid_date:
                    vals_to_write.update({'paid_date': now, 'paid_uid': user_id})
                elif new_state == 'partial_payment' and not order.partial_payment_date:
                    vals_to_write.update({'partial_payment_date': now, 'partial_payment_uid': user_id})
                elif new_state == 'received' and not order.received_date:
                    vals_to_write.update({'received_date': now, 'received_uid': user_id})
                elif new_state == 'partial_received' and not order.partial_received_date:
                    vals_to_write.update({'partial_received_date': now, 'partial_received_uid': user_id})

            if vals_to_write:
                order.write(vals_to_write)
                
        return True
