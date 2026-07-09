from odoo import models, fields, api, _


class StockDistribution(models.Model):
    _inherit = "tw.stock.distribution"

    is_internal = fields.Boolean(
        string="Is Internal",
        compute='_compute_is_internal',
        help="Technical field to determine if the distribution is internal (between branches)"
    )

    mutation_order_id = fields.Many2one('tw.mutation.order', string='Mutation Order')

    @api.depends('requester_id')
    def _compute_is_internal(self):
        for record in self:
            record.is_internal = bool(record.requester_id.route_type == 'internal')
    
    def action_create_order(self):
        self.ensure_one()
        if self.is_internal:
            self.action_create_mutation_order()
        else:
            self.action_create_sale_order()
    
    def action_create_mutation_order(self):
        mo_obj = self.env['tw.mutation.order'].search([
            ('stock_distribution_id', '=', self.id)
        ])
        if mo_obj:
            return

        # Determine location from purchase order type (always use outgoing type)
        picking_type = self.purchase_order_type_id.default_outgoing_type_id
        location_id = picking_type.default_location_src_id.id if picking_type and picking_type.default_location_src_id else False

        vals = {
            'company_id': self.company_id.id,
            'requester_id': self.requester_id.id,
            'division': self.division,
            'employee_id': self.employee_id.id,
            'stock_distribution_id': self.id,
            'date': self.date,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'description': self.description,
            'mutation_order_ids': self._prepare_mutation_order_line(),
            'state': 'draft',
        }
        
        if location_id:
            vals['location_id'] = location_id

        # Membuat Mutation Order
        mo_obj = self.env['tw.mutation.order'].sudo().create(vals)
        mo_obj.sudo().renew_available()
        self.sudo().write({
            'mutation_order_id': mo_obj.id,
        })

        # Auto Confirm SD to MO if Company sender is not MD
        is_sender_md = self._is_company_md(self.company_id)

        if not is_sender_md:
            mo_obj.mutation_order_ids.suspend_security()._validate_order()
            mo_obj.sudo().action_confirm()
    
    def action_view_mutation_order(self):
        """
        Open the linked mutation order in form view.
        This method is used for the smart button to view the linked mutation order.
        """
        self.ensure_one()
        if not self.mutation_order_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _('No Order is linked to this distribution.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }
            
        return {
            'type': 'ir.actions.act_window',
            'name': _('Mutation Order'),
            'res_model': 'tw.mutation.order',
            'res_id': self.mutation_order_id.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'form_view_ref': 'tw_mutation.tw_mutation_order_form_view',
            }
        }
    
    def _prepare_mutation_order_line(self):
        mutation_order_line = []
        for line in self.stock_distribution_ids:
            if (line.approved_qty - line.qty) > 0:
                qty_available = 0
                if self.division == 'Unit':
                    qty_available = self.env['stock.quant'].get_stock_available( line.product_id.id, self.company_id.id )
                
                mutation_order_line.append((0, 0, {
                    'mutation_order_id': self.id,
                    'product_id': line.product_id.id,
                    'description': line.description,
                    'price': line.price,
                    'qty': line.approved_qty - line.qty,
                    'qty_available': qty_available
                }))
        return mutation_order_line

    def _check_transaction_before_closing_the_order(self):
        check = super(StockDistribution, self)._check_transaction_before_closing_the_order()
        if self.mutation_order_id:
            return
        return check

    def _is_company_md(self, company):
        if not company:
            return False
        try:
            md_code = self.env['res.company'].get_default_main_dealer_code()
        except:
            return False
        return company.code == md_code and company.branch_type_id.value == 'MD'
                
        