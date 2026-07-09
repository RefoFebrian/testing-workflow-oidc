from datetime import datetime, date
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class StockDistribution(models.Model):
    _name = "tw.stock.distribution"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'Stock Distribution'
    _order = 'id desc'

    # 7: defaults methods
    def _get_default_date(self):
        return datetime.now()
    
    def _get_default_company(self):
        company_ids = False
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1:
            return company_ids[0].id
        return False

    name = fields.Char(string="Stock Distribution", readonly=True, default='New', copy=False, index=True, compute='_compute_name', store=True)
    state = fields.Selection([
        ('draft','Draft'),
        ('open','Open'),
        ('done','Done'),
        ('cancel','Cancelled'),
        ('closed','Closed'),
    ], 'State', default='draft', tracking=True)
    description = fields.Text('Description')
    origin = fields.Char('Origin')
    model_name = fields.Char('Model Name')
    origin_transaction_id = fields.Integer('Origin Transaction ID')

    date = fields.Date('Date',default=_get_default_date)
    start_date = fields.Date('Start Date', tracking=True)
    end_date = fields.Date('End Date', tracking=True)
    amount_total = fields.Float('Amount Total', compute='_compute_amount', digits='Product Price', store=True, tracking=True)
    is_effective_date = fields.Boolean('Is Effective Date', compute='_compute_is_effective_date')

    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())

    confirm_uid = fields.Many2one('res.users', string="Confirmed by")
    confirm_date = fields.Datetime('Confirmed on')
    done_uid = fields.Many2one('res.users', string="Done by")
    done_date = fields.Datetime('Done on')
    cancel_uid = fields.Many2one('res.users', string="Rejected by")
    cancel_date = fields.Datetime('Rejected on')
    close_uid = fields.Many2one('res.users', string="Closed by")
    close_date = fields.Datetime('Closed on')

    # 9: relation fields
    purchase_order_type_id = fields.Many2one('tw.purchase.order.type', 'Type', domain="[('division', '=', division),('company_id', 'in', [company_id, False])]")
    pricelist_id = fields.Many2one(comodel_name='product.pricelist',string="Pricelist",compute='_compute_pricelist_id',store=True, readonly=False, precompute=True,domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",help="If you change the pricelist, only newly added lines will be affected.")
    company_id = fields.Many2one('res.company', string='Branch Sender', default=_get_default_company)
    employee_id = fields.Many2one('hr.employee', 'Responsible', domain=[('company_id', '=', company_id)])
    requester_id = fields.Many2one('res.partner', string="Branch Requester")
    sale_order_id = fields.Many2one('tw.sale.order', 'Sale Order')
    stock_distribution_ids = fields.One2many('tw.stock.distribution.line', 'stock_distribution_id', 'Stock Distribution Line', tracking=True)

    # 10: constraints & sql constraints
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        today = fields.Date.context_today(self)
        for record in self:
            # Jika dari API, bisa jadi start date di bawah hari ini, jadi tidak di jegat
            if record.origin:
                continue

            if record.start_date and record.start_date < today:
                raise ValidationError(_("Start date cannot be in the past. Must be today or future date"))
            if record.end_date and record.end_date < today:
                raise ValidationError(_("End date cannot be in the past. Must be today or future date"))
            if record.start_date and record.end_date and record.end_date < record.start_date:
                raise ValidationError(_("End date cannot be before start date"))


    # 11: compute/depends & on change methods
    @api.depends('company_id')
    def _compute_name(self):
        for rec in self:
            if not rec.name or rec.name == 'New':
                if rec.company_id:
                    seq_name = self.env['ir.sequence'].with_company(rec.company_id).get_sequence_code('SD', str(rec.company_id.code))
                    rec.name = seq_name
                
    @api.depends('company_id', 'division')
    def _compute_pricelist_id(self):
        for order in self:
            if order.state != 'draft':
                continue

            order = order.with_company(order.company_id)
            order.pricelist_id = order._get_pricelist()

    @api.depends('stock_distribution_ids.sub_total')
    def _compute_amount(self):
        for record in self:
            record.amount_total = sum(line.sub_total for line in record.stock_distribution_ids)

    @api.depends('start_date', 'end_date')
    def _compute_is_effective_date(self):
        condition = False
        if (not self.start_date and not self.end_date) or (self.start_date and self.end_date and self.start_date <= date.today() and self.end_date >= date.today()) :
            condition = True
        self.is_effective_date = condition

    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if vals.get('company_id'):
                company_src = self.env['res.company'].suspend_security().search([('id','=',vals['company_id'])],limit=1)
                vals['name'] = self.env['ir.sequence'].get_sequence_code('SD', str(company_src.code))
        return super(StockDistribution, self).create(vals_list)
    
    def unlink(self):
        raise Warning('Warning!\nCannot delete records!')

    def action_create_order(self):
        self.ensure_one()
        if self.sale_order_id or self.state != 'open':
            raise UserError(f'Silakan refresh halaman browser Anda. State sudah {self._get_state_value()}')
        self.action_create_sale_order()

    def action_create_sale_order(self):
        self.ensure_one()  # Pastikan hanya satu record yang diproses
        so_obj = self.env['tw.sale.order']
        
        picking_type = self.purchase_order_type_id.default_outgoing_type_id
        location_id = picking_type.default_location_src_id.id if picking_type and picking_type.default_location_src_id else False
        
        sale_order_vals = {
            'company_id': self.company_id.id,
            'division': self.division,
            'date_order': self.date,
            'partner_id': self.requester_id.id,
            'origin': self.name,
            'state': 'draft',
            'warehouse_id': self.get_warehouse(self.company_id.id).id,
            'payment_term_id': self.requester_id.property_payment_term_id.id,
            'stock_distribution_id': self.id,
            'note': f"{self.purchase_order_type_id.name} - {self.date.strftime('%B')} - {self.date.strftime('%Y')}",
            'order_line': self._prepare_sale_order_line(),
        }
        
        if location_id:
            sale_order_vals['location_id'] = location_id

        so_obj = so_obj.with_company(self.company_id.id).suspend_security().create(sale_order_vals)
        so_obj.onchange_company_id()
        so_obj.order_line._onchange_product_id_warning()
        so_obj.order_line._compute_cogs()
        so_obj.order_line._compute_cogs_total()
        self.sale_order_id = so_obj.id
        return so_obj
    
    def action_view_sale_order(self):
        """
        Open the linked sale order in form view.
        This method is used for the smart button to view the linked sale order.
        """
        self.ensure_one()
        if not self.sale_order_id:
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
            'name': _('Sale Order'),
            'res_model': 'tw.sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'form_view_ref': 'tw_sale.tw_sale_order_form_view',
            }
        }

    def action_close_order(self):
        self._check_transaction_before_closing_the_order()
        self.suspend_security().write(
            {
                'state': 'closed',
                'close_uid': self.env.user.id,
                'close_date': fields.Datetime.now(),
            }
        )
    
    def action_update_date_wizard(self):
        form_id = self.env.ref('tw_stock_distribution.tw_stock_distribution_update_date_view_wizard').id
        return {
            'name': 'Update Start Date & End Date',
            'res_model': 'tw.stock.distribution',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'view_id': form_id,
            'target': 'new'
        }
    
    def action_confirm_update_date(self):
        return True
    
    def action_reject_request(self):
        if self.state == 'draft':
            self.write({
                'state': 'reject',
                'cancel_uid': self.env.user.id,
                'cancel_date': fields.Datetime.now(),
            })

    def get_warehouse(self, company_id):
        warehouse = self.env['stock.warehouse'].suspend_security().search([('company_id', '=', company_id)], limit=1)
        if not warehouse:
            raise Warning("No Default Warehouse Found.")
        return warehouse
    
    def action_confirm_qty(self):
        self.is_approved_qty_zero()
        self.write({
            'state': 'open',
            'confirm_uid': self.env.user.id,
            'confirm_date': fields.Datetime.now(),
            'date': self._get_default_date(),
        })

    def is_approved_qty_zero(self):
        if self.state == 'draft' and sum(line.approved_qty for line in self.stock_distribution_ids) < 1:
            raise Warning("Approved Qty must be greater than 0.")

    def action_done(self):
        """Mark Stock Distribution as done.
        
        This method can be inherited by other modules to add additional 
        actions when the stock distribution is completed.
        """
        self.suspend_security().write({
            'state': 'done',
            'done_uid': self.env.uid,
            'done_date': datetime.now(),
        })

    def is_done(self, tx_obj):
        # Menghitung jumlah approved_qty dan supply_qty
        approved_qty = sum(line.approved_qty for line in self.stock_distribution_ids)
        supply_qty = sum(line.supply_qty for line in self.stock_distribution_ids)

        # Jika approved_qty - supply_qty == 0, ubah state menjadi 'done'
        if approved_qty - supply_qty == 0:
            self.action_done()

        # Jika state adalah 'closed', cek apakah sale order/mutation order sudah selesai atau dibatalkan
        if self.state == 'closed':
            if not tx_obj or all(order.state in ('done', 'cancel', 'cancelled') for order in tx_obj):
                self.action_done()

    # 14: private methods
    def _prepare_sale_order_line(self):
        sale_order_lines = []
        for line in self.stock_distribution_ids:
            approved_qty = line.approved_qty - line.qty
            if approved_qty > 0:
                sale_order_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'product_uom_qty': approved_qty,
                    'tax_id': [(6, 0, [x.id for x in line.product_id.taxes_id])],
                }))
        return sale_order_lines

    def _validate_purchase_order_type(self, type, division='Sparepart'):
        po_type = self.env['tw.purchase.order.type'].sudo().search([
            ('division', '=', division.title()),
            ('name', '=', type.title())
        ], limit=1)
        return po_type
    
    def _validate_stock_distribution(self, vals, po_type_id):
        po_name = vals.get('po_name')
        return self.sudo().search([
            ('origin', '=', po_name),
            ('purchase_order_type_id', '=', po_type_id),
        ],limit=1)
    
    
    def _get_pricelist(self):
        current_pricelist=False
        if self.division =='Unit':
            current_pricelist = self.company_id.branch_setting_id.pricelist_sale_unit_id
        elif self.division == 'Sparepart':  
            current_pricelist = self.company_id.branch_setting_id.pricelist_sale_sparepart_id
        return current_pricelist

    def _check_transaction_before_closing_the_order(self):
        if self.sale_order_id:
            return

    def _schedulle_close_order(self,date=False):
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')

        stock_distribution_obj = self.search([
            ('state', '=', 'open'),
            ('end_date', '<', date)
        ])

        for stock_distribution in stock_distribution_obj:
            stock_distribution.action_close_order()
        