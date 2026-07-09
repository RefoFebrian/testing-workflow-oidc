from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning


class MutationOrder(models.Model):
    _name = "tw.mutation.order"
    _description = "Mutation Order"

    # 7: defaults methods
    def _get_default_date(self):
        return datetime.now()
    
    def _get_state_value(self):
        # Mengambil value yang sesuai dengan key di state
        selection = self._fields.get('state') and self._fields['state'].selection
        return dict(selection).get(self.state, self.state) if selection else self.state

    name = fields.Char("Name")
    description = fields.Text('Description')

    amount_total = fields.Float('Amount Total', compute='_compute_amount_total', digits='Product Price', store=True)

    date = fields.Date("Date", default=_get_default_date)
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")

    state = fields.Selection([
        ('draft','Draft'),
        ('confirm','Confirmed'),
        ('done','Done'),
        ('cancelled','Cancelled'),
    ], string='state', default='draft')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())

    confirm_uid = fields.Many2one('res.users', string='Confirm By')
    confirm_date = fields.Datetime('Confirm On')
    done_uid = fields.Many2one('res.users', string='Done By')
    done_date = fields.Datetime('Done On')
    cancelled_uid = fields.Many2one('res.users', string='Cancelled By')
    cancelled_date = fields.Datetime('Cancelled On')

    company_id = fields.Many2one('res.company', 'Branch Sender', default=lambda self: self.env.company,index=True, required=True)
    employee_id = fields.Many2one('hr.employee', string='Responsible', domain=[('company_id', '=', company_id)])
    requester_id = fields.Many2one('res.partner', string='Branch Requester')
    location_id = fields.Many2one('stock.location', string='Location', domain="[('company_id','=',company_id),('usage','=','internal')]")
    pricelist_id = fields.Many2one('product.pricelist', string='Price List', compute='_compute_pricelist_id', store=True)
    stock_distribution_id = fields.Many2one('tw.stock.distribution', string='Stock Distribution', ondelete='restrict')
    mutation_order_ids = fields.One2many('tw.mutation.order.line', 'mutation_order_id', string='Mutation Order Line')
    picking_ids = fields.One2many('stock.picking', 'mutation_order_id', string='Pickings')
    picking_count = fields.Integer(compute='_compute_picking_count', string='Picking Count')

    @api.depends('company_id', 'division')
    def _compute_pricelist_id(self):
        for order in self:
            if order.state != 'draft':
                continue

            order = order.with_company(order.company_id)
            order.pricelist_id = order._get_pricelist()

    @api.depends('mutation_order_ids.sub_total')
    def _compute_amount_total(self):
        for order in self:
            order.amount_total = sum(line.sub_total for line in order.mutation_order_ids)

    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if vals.get('company_id'):
                branch_src = self.env['res.company'].suspend_security().search([('id','=',vals['company_id'])],limit=1)
            vals['name'] = self.env['ir.sequence'].suspend_security().get_sequence_code('MO', str(branch_src.code))
        return super(MutationOrder, self).create(vals_list)

    def write(self,vals):
        return super(MutationOrder, self).write(vals)
    
    def unlink(self):
        raise Warning('Warning! \nCannot delete records!')

    def action_confirm(self):
        if not self.mutation_order_ids:
            raise Warning("Detail Line cannot be empty!")

        # Renew Available Stock and write performance HPP
        self.renew_available()
        for mo_line in self.mutation_order_ids:
            self.write_initial_cogs(mo_line)

        self.with_company(self.company_id).action_create_picking()

        self.suspend_security().write({
            'confirm_uid': self.env.uid,
            'confirm_date': datetime.now(),
            'date': self._get_default_date(),
            'state' : 'confirm'
        })

    def action_done(self):
        """Mark Mutation Order as done.
        
        This method can be inherited by other modules to add additional 
        actions when the mutation order is completed (e.g., updating 
        Stock Distribution or Mutation Request status).
        """
        if self.state == 'done':
            raise Warning(f'Silakan refresh halaman ini, karena state telah {self._get_state_value()}')
        
        self.suspend_security().write({
            'state': 'done',
            'done_uid': self.env.uid,
            'done_date': datetime.now(),
        })
        
        # Also mark linked Stock Distribution as done
        if self.stock_distribution_id and self.stock_distribution_id.state not in ('done', 'cancel'):
            self.stock_distribution_id.action_done()

    def action_cancel(self):
        if self.state == 'cancelled':
            raise Warning(f'Silakan refresh halaman ini, karena state telah {self._get_state_value()}')
        
        self.suspend_security().write({
            'state': 'cancelled',
            'cancelled_uid': self.env.uid,
            'cancelled_date': datetime.now(),
        })

        # Calculate product quantities from order lines
        product_qty = {}
        for line in self.mutation_order_ids:
            product_qty[line.product_id] = product_qty.get(line.product_id, 0) + line.qty

        # Update the quantities in the distribution lines
        if self.stock_distribution_id:
            for dist_line in self.stock_distribution_id.stock_distribution_ids:
                if dist_line.product_id in product_qty:
                    dist_line.qty -= product_qty[dist_line.product_id]

    def _prepare_picking_vals(self, picking_type_obj):
        """Prepare values for stock.picking creation.
        
        Args:
            picking_type_obj (recordset): Stock Picking Type
            
        Returns:
            dict: Values for stock.picking creation
        """

        # Create procurement group to link the picking chain (push rules)
        group = self.env['procurement.group'].sudo().create({'name': self.name})

        return {
            'picking_type_id': picking_type_obj.id,
            'partner_id': self.requester_id.id,
            'date': self.date,
            'origin': self.name,
            'group_id': group.id,
            'mutation_order_id': self.id, 
            'company_id': self.company_id.id,
            'location_id': self.location_id.id if self.location_id else picking_type_obj.default_location_src_id.id,
            'location_dest_id': picking_type_obj.default_location_dest_id.id,
            'division': self.division,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'min_date': self.end_date,
        }

    def action_create_picking(self):
        """Create a picking for the mutation order.
        
        Returns:
            recordset: Created stock.picking record
        """
        self.ensure_one()
        
        # Get the warehouse - first try company's warehouse, then fallback to any warehouse
        warehouse = self.company_id.warehouse_id
        if not warehouse:
            warehouse = self.env['stock.warehouse'].suspend_security().search(
                [('company_id', '=', self.company_id.id)], 
                limit=1
            )
            if not warehouse:
                raise Warning(_(
                    "No warehouse found for company %s. "
                    "Please configure a warehouse first.") % self.company_id.name)
        
        # Use interbranch out picking type based on division
        picking_type_obj = self._get_interbranch_out_type(warehouse)
            
        if not picking_type_obj:
            division_label = self.division or 'Unit'
            raise Warning(_(
                "No interbranch out picking type (%(division)s) found for warehouse %(warehouse)s. "
                "Please configure interbranch picking types in warehouse settings.",
                division=division_label, warehouse=warehouse.name))

        # Create picking
        picking_vals = self._prepare_picking_vals(picking_type_obj)
        picking = self.env['stock.picking'].with_company(self.company_id).suspend_security().create(picking_vals)
        
        # Create stock moves
        self.create_stock_moves(picking)
        
        # Validate picking if there are moves
        if picking.move_ids:
            picking.action_confirm()
            picking.action_assign()
            picking.do_unreserve()
            
        return picking


    def create_stock_moves(self, picking=False):
        moves_ids = []
        for order_line in self.mutation_order_ids:
            if not order_line.product_id:
                continue

            # Check product type
            if order_line.product_id.type in ('product', 'consu'):
                prepared_moves = self.prepare_order_line_move(order_line, picking)
                for vals in prepared_moves:
                    if vals.get('product_uom_qty', 0) > 0:
                        stock_move_obj = self.env['stock.move'].suspend_security().create(vals)
                        stock_move_obj._action_confirm()
                        
    def write_initial_cogs(self, mo_line_obj):
        if self.division == 'Unit' and self.company_id.branch_type_id.value == 'MD':

            # TODO : Price List Jual Unit untuk Main Dealer ini dipastikan ngambil value kemana
            branch_setting_obj = self.env['tw.branch.setting'].get_branch_setting(self.company_id)
            pricelist_purchase_unit_id = branch_setting_obj.pricelist_purchase_unit_id
            if not pricelist_purchase_unit_id:
                raise Warning("Please fill in the Unit Purchase Price List for Main Dealer!")
            
            price = pricelist_purchase_unit_id.with_company(self.company_id.id)._price_get(mo_line_obj.product_id, 1)[pricelist_purchase_unit_id.id]
            mo_line_obj.initial_cogs = price
            
            if mo_line_obj.initial_cogs < 1:
                raise Warning(f"Please set the price for Product '{mo_line_obj.product_id.name}' on the Pricelist : '{pricelist_purchase_unit_id.name}'!" )
            
    def renew_available(self):
        self.mutation_order_ids._onchange_product_id()

    def prepare_order_line_move(self, order_line, picking):
        # Fetch warehouse and validate picking type
        branch_name = self.company_id.name
        warehouse = self.env['stock.warehouse'].suspend_security()._get_company_warehouse(self.company_id)
        if not warehouse:
            raise Warning(
                f"Please set the warehouse for branch '{branch_name}' first."
            )
        
        picking_type_obj = self._get_interbranch_out_type(warehouse)
        
        if not picking_type_obj:
            division_label = self.division or 'Unit'
            raise Warning(
                f"Please set the interbranch out ({division_label}) picking type for warehouse '{warehouse.name}' first."
            )

        if picking_type_obj.company_id != self.company_id:
            picking_name = picking_type_obj.name
            raise Warning(
                f"Type picking '{picking_name}' is not for branch '{branch_name}'"
            )
        
        if self.location_id:
            location_id = self.location_id.id
        else:
            location_id = picking_type_obj.default_location_src_id.id

        location_dest_id = picking_type_obj.default_location_dest_id.id

        # Include warehouse routes so _get_push_rule can find the push rule
        # even when warehouse_id is set to False for inter-company transfers
        route_ids = [(4, route.id) for route in warehouse.route_ids]

        return [{
            'name': order_line.description or '',
            'product_id': order_line.product_id.id,
            'product_uom': order_line.product_id.uom_id.id,
            'product_uom_qty': order_line.qty,
            'date': datetime.now(),
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            'picking_id': picking.id if picking else False,
            'group_id': picking.group_id.id if picking and picking.group_id else False,
            'route_ids': route_ids,
            'state': 'draft',
            'price_unit': order_line.price,
            'picking_type_id': picking_type_obj.id,
            'origin': self.name,
            'warehouse_id': warehouse.id,
            'company_id': self.company_id.id,
        }]

    def action_view_stock_distribution(self):
        """
        Open the linked stock distribution in form view.
        This method is used for the smart button to view the linked stock distribution.
        
        Returns:
            dict: Action to open the stock distribution form view
            or client action with warning message if no distribution is linked
        """
        self.ensure_one()
        if not self.stock_distribution_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Warning'),
                    'message': _('No stock distribution is linked to this mutation order.'),
                    'type': 'warning',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'}
                }
            }
            
        return {
            'type': 'ir.actions.act_window',
            'name': _('Stock Distribution'),
            'res_model': 'tw.stock.distribution',
            'res_id': self.stock_distribution_id.id,
            'view_mode': 'form',
            'target': 'current',
            'views': [(False, 'form')],
            'context': {
                'form_view_ref': 'tw_stock_distribution.tw_stock_distribution_form_view',
                'default_origin': self.name,
            }
        }

    def _get_picking_domain(self):
        """Return domain to fetch all pickings related to this mutation order.
        
        Includes push-created pickings that share the same procurement group
        but do not carry mutation_order_id directly.
        """
        self.ensure_one()
        group_ids = self.picking_ids.mapped('group_id').ids
        domain = ['|', ('mutation_order_id', '=', self.id)]
        if group_ids:
            domain += [('group_id', 'in', group_ids)]
        else:
            domain += [('id', 'in', [])]
        return domain

    def _compute_picking_count(self):
        """Compute the number of pickings for this mutation order."""
        for order in self:
            order.picking_count = self.env['stock.picking'].suspend_security().search_count(
                order._get_picking_domain()
            )

    def action_view_picking(self):
        """
        Open the linked stock pickings (both OUT and IN) in list view.
        Includes push-created pickings that share the same procurement group.
        
        Returns:
            dict: Action to open the stock picking(s) in list view
            or client action with warning message if no picking is found
        """
        self.ensure_one()
        domain = self._get_picking_domain()
        picking_obj = self.env['stock.picking'].suspend_security().search(domain, order='id asc')
        
        if not picking_obj:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Warning'),
                    'message': _('No stock pickings found for this mutation order.'),
                    'type': 'warning',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'}
                }
            }

        # Always show list view for multiple pickings (OUT + IN + push-created)
        return {
            'name': _('Stock Picking'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': domain,
            'context': {'create': False},
        }

    def _get_pricelist(self):
        current_pricelist=False
        if self.division =='Unit':
            current_pricelist = self.company_id.branch_setting_id.pricelist_sale_unit_id
        elif self.division == 'Sparepart':  
            current_pricelist = self.company_id.branch_setting_id.pricelist_sale_sparepart_id
        return current_pricelist

    def _get_interbranch_out_type(self, warehouse):
        """Return the correct interbranch OUT picking type based on MO division.

        Args:
            warehouse (recordset): stock.warehouse record

        Returns:
            recordset: stock.picking.type for outgoing interbranch transfer
        """
        if self.division == 'Sparepart':
            return warehouse.interbranch_out_sparepart_type_id
        return warehouse.interbranch_out_unit_type_id
