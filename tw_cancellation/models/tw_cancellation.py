# 1: imports of python lib

# 2: import of known third party lib
from datetime import date

# 3:  imports of odoo
from odoo import models, fields, api , _
from odoo.exceptions import UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwCancellation(models.Model):
    _name = "tw.cancellation"
    _inherit = ['mail.thread', 'tw.approval.mixin']
    _description = 'Transaction Cancellation'
    _order = 'id desc'

    # 7: defaults methods
    def _get_default_date(self):
        return date.today().strftime("%Y-%m-%d")
    
    def _get_state_value(self):
        # Mengambil value yang sesuai dengan key di state
        selection = self._fields.get('state') and self._fields['state'].selection
        return dict(selection).get(self.state, self.state) if selection else self.state
    
    # 8: fields
    name = fields.Char(string='Name')
    state = fields.Selection([
        ('draft','Draft'),
        ('waiting_for_approval','Waiting For Approval'),
        ('approved','Approved'),
        ('confirmed','Confirmed'),
        ], 'State', default='draft')
    
    
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
    date = fields.Date('Date',default=_get_default_date)
    transaction_name = fields.Char('Transaction Name')
    reason = fields.Text('Reason')
    note = fields.Text('Catatan')
    
    # Audit Trail
    confirm_uid = fields.Many2one('res.users', string="Confirmed by")
    confirm_date = fields.Datetime('Confirmed on')
    approve_date = fields.Datetime(string='Approved on')
    approve_uid = fields.Many2one('res.users', string="Approved by")

    # 9: relation fields
    company_id = fields.Many2one("res.company", string="Branch", domain="[('parent_id', '!=', False)]", default=lambda self: self.env.company.id if self.env.company.parent_id else False)
    model_id = fields.Many2one('ir.model',string="Form",ondelete='set null')
    transaction_cancel_id = fields.Integer('Transaction ID')
    period_id = fields.Many2one('tw.account.period', string="Period")
    move_id = fields.Many2one('account.move', 'Account Entry', copy=False)
    move_ids = fields.One2many(related='move_id.line_ids', string='Journal Items', readonly=True)
    period_id = fields.Many2one('tw.account.period', string="Period")


    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    @api.onchange('model_id')
    def _onchange_model_id(self):
        if self.model_id:
            # * Jika sudah ada module childs (seperti Purchase order Cancel, DSO Cancel dan lainnya) maka harus create pada menu di module tersebut
            self._warn_if_specific_module_exists()
        
    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list):
        
        for values in vals_list:
            if not values.get('transaction_name',False):
                raise Warning("Transaction name does not exist !")
            name = "X" + values['transaction_name']
            self._check_duplicate_transaction(name)
            values['name'] = name
            values['date'] = self._get_default_date()
            # values['period_id'] = self.env['account.period'].find(dt=self._get_default_date()).id
        return super(TwCancellation, self).create(vals_list)

    def unlink(self):
        for record in self:
            if record.state and record.state != 'draft':
                raise Warning('Warning! \nCannot delete records with a state other than draft!')
            else:
                raise Warning('Warning! \nCannot delete records!')

        return super(TwCancellation, self).unlink()
    
    # 13: action methods
    def action_request_approval(self):
        # Mengajukan permintaan approval
        # * Jika sudah ada module childs (seperti Purchase order Cancel, DSO Cancel dan lainnya) maka harus create pada menu di module tersebut
        self._warn_if_specific_module_exists()
        return super().action_request_approval(value=5)

    def action_confirm(self):
        """
        Override this method to implement specific business flow logic 
        for confirming the cancellation of other models.
        """
        self.write({
            'state': 'confirmed',
            'confirm_uid': self.env.uid,
            'confirm_date': fields.Datetime.now()
        })  

    # 14: private methods
    def _get_installed_redirects(self):
        """
        Return dict model → handler info, only if module is installed.
        """
        handlers = self.env['tw.cancellation.handler'].sudo().search([])
        redirects = {}
        
        for handler in handlers:
            module_installed = self.env['ir.module.module'].sudo().search([
                ('name', '=', handler.module),
                ('state', '=', 'installed')
            ], limit=1)
            if module_installed:
                redirects[handler.model] = {
                    'module': handler.module,
                    'model': handler.model,
                }

        return redirects
    
    def _warn_if_specific_module_exists(self):
        context_model = self.env.context.get('default_model_type',False)
        if context_model:
            return True
        redirects = self._get_installed_redirects()
        model_name = self.model_id.model
        handler = redirects.get(model_name)

        if handler:
            self.model_id = False
            raise Warning(
                "Silahkan gunakan menu cancel pada module %s untuk melakukan pembatalan pada model %s. "%(handler['module'], handler['model'])
            )
    
    def _check_duplicate_transaction(self, name):
        """
        Check if a transaction with the same name already exists.
        """
        existing_record = self.suspend_security().search([('name', '=', name)], limit=1)
        if existing_record:
            raise Warning("Transaction with this name already exists.")
        
    def _return_picking(self,transaction_obj):
        self._cancel_pending_pickings(transaction_obj)
        # Filter pickings that are 'done' and have at least one move that is the last in its route.
        pickings = transaction_obj.picking_ids.filtered(
            lambda p: p.state == 'done' and any(m._is_last_move_from_route() for m in p.move_ids)
        )
        # Exclude pickings that are already return pickings themselves
        pickings = pickings.filtered(
            lambda p: not p.return_id and not any(m.origin_returned_move_id for m in p.move_ids)
        )
        # Skip pickings that have already been returned
        pickings = pickings.filtered(
            lambda p: not all(
                sum(ret_move.quantity for ret_move in m.returned_move_ids if ret_move.state == 'done') >= m.quantity 
                for m in p.move_ids
            )
        )
        processed_pickings = self.env['stock.picking']
        pending_pickings = []

        for picking in pickings:
            return_picking = self._create_and_validate_return_picking(picking)
            next_pickings = return_picking._get_next_transfers().filtered(
                lambda p: p.state not in ('done', 'cancel')
            )
            processed_pickings |= picking | return_picking
            pending_pickings.extend([
                next_picking.id
                for next_picking in next_pickings
                if next_picking.id not in processed_pickings.ids
            ])

        while pending_pickings:
            next_picking = self.env['stock.picking'].browse(pending_pickings.pop(0)).exists()
            if not next_picking or next_picking in processed_pickings:
                continue

            processed_pickings |= next_picking
            self._validate_reverse_chain_picking(next_picking)
            chained_pickings = next_picking._get_next_transfers().filtered(
                lambda p: p.state not in ('done', 'cancel')
            )
            pending_pickings.extend([
                chained_picking.id
                for chained_picking in chained_pickings
                if chained_picking.id not in processed_pickings.ids
            ])

    def _prepare_return_picking(self,picking_ids):
        vals_list = []
        for picking in picking_ids:
            line_return_moves = []
            for move in picking.move_ids:
                line_return_moves.append((0, 0, {
                    'product_id': move.product_id.id,
                    'move_id': move.id,
                    'quantity': move.quantity,
                }))
            vals_list.append({
                'picking_id': picking.id,
                'product_return_moves': line_return_moves
            })
        return vals_list

    def _cancel_pending_pickings(self, transaction_obj):
        pending_pickings = transaction_obj.picking_ids.filtered(
            lambda p: p.state not in ('done', 'cancel')
        )
        for picking in pending_pickings:
            picking.action_cancel()

    def _create_and_validate_return_picking(self, picking):
        stock_return_picking_form = self.env['stock.return.picking'].create(
            self._prepare_return_picking(picking)
        )
        if not stock_return_picking_form:
            return self.env['stock.picking']

        stock_return_picking_form.ensure_one()
        return_action = stock_return_picking_form.action_create_returns()
        if not return_action:
            return self.env['stock.picking']

        return_picking = self.env['stock.picking'].browse(return_action['res_id']).exists()
        if not return_picking:
            return self.env['stock.picking']

        self._prepare_picking_for_auto_validation(return_picking)
        self._validate_picking_with_context(return_picking)
        return return_picking

    def _validate_reverse_chain_picking(self, picking):
        self._prepare_picking_for_auto_validation(picking)
        self._validate_picking_with_context(picking)

    def _prepare_picking_for_auto_validation(self, picking):
        if picking.state == 'draft':
            picking.action_confirm()

        if picking.state in ('confirmed', 'waiting', 'partially_available'):
            picking.action_assign()

        for move in picking.move_ids:
            source_move_lines = self._get_reverse_source_move_lines(move)
            if source_move_lines:
                if move.move_line_ids:
                    move.move_line_ids.unlink()

                for source_move_line in source_move_lines:
                    quantity = source_move_line.quantity or source_move_line.quantity_product_uom
                    if not quantity:
                        continue

                    self.env['stock.move.line'].create({
                        'move_id': move.id,
                        'picking_id': picking.id,
                        'product_id': move.product_id.id,
                        'product_uom_id': move.product_uom.id,
                        'location_id': move.location_id.id,
                        'location_dest_id': move.location_dest_id.id,
                        'lot_id': source_move_line.lot_id.id,
                        'quantity': quantity,
                    })

            move.quantity = move.product_uom_qty

            if move.move_line_ids:
                for move_line in move.move_line_ids:
                    if not move_line.quantity:
                        move_line.quantity = move_line.quantity_product_uom or move.product_uom_qty

    def _get_reverse_source_move_lines(self, move):
        source_moves = move.origin_returned_move_id
        if not source_moves:
            source_moves = move.move_orig_ids.filtered(lambda m: m.product_id == move.product_id)

        return source_moves.mapped('move_line_ids').filtered(
            lambda ml: ml.quantity or ml.quantity_product_uom
        )

    def _validate_picking_with_context(self, picking):
        picking.with_context(
            skip_backorder=True,
            skip_sms=True,
            skip_immediate=True
        ).button_validate()




    
