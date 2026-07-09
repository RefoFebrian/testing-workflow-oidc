# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging

_logger = logging.getLogger(__name__)

# 2: import of known third party lib
from datetime import datetime, date

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.tools import float_is_zero, groupby, SQL

# 5: local imports

# 6: Import of unknown third party lib

class TwSaleOrder(models.Model):
    """
    Dealer Sale Order model that inherits from the sale.order model.
    """
    _name = "tw.dealer.sale.order"
    _inherit = "sale.order"
    _description = "Dealer Sale Order"

    # 7: defaults methods
    def _get_default_date(self):
        return self.env['res.company'].get_default_date()
        
    def _get_state_value(self):
        # Mengambil value yang sesuai dengan key di state
        selection = self._fields.get('state') and self._fields['state'].selection
        return dict(selection).get(self.state, self.state) if selection else self.state

    # 8: fields
    qq = fields.Char('qq')
    delivery_address = fields.Text('Alamat Kirim')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
    state = fields.Selection(selection_add=[
        ('draft', 'Draft'),
        ('waiting_for_approval', 'Request For Approval'),
        ('approved', 'Approved'),
        ('sale', ),
        ('cancel', ),
        ('done', 'Done')
    ], string="Status", readonly=True, copy=False, index=True, tracking=3, default='draft')
    is_cod = fields.Boolean(help="Indicates if the order is a Cash On Delivery (COD) order.")
    
    amount_selling_price = fields.Float(string='Total Harga Jual', compute='_compute_amounts', store=True, help="The total Price.")
    amount_unit_price = fields.Float(string='Total Harga Unit', compute='_compute_amounts', store=True, help="The total Unit Price.")
    amount_downpayment = fields.Float(string='Total Uang Muka/DP', compute='_compute_amounts', store=True, help="Down payments are made when creating invoices from a sales order. They are not copied when duplicating a sales order.")
    amount_payment = fields.Float(string='Payment', compute='_compute_payment_amounts', store=True, help="Payments are made when creating invoices from a sales order. They are not copied when duplicating a sales order.")
    amount_gp_unit = fields.Float(string='GP Unit', compute='_compute_amounts', store=True, help="Total Gross Profit Unit.")
    amount_discount_regular = fields.Float(string='Diskon Regular', compute='_compute_amounts', store=True, help="Regular Discount.")
    amount_discount_direct = fields.Float(string='Diskon Potongan Langsung', compute='_compute_amounts', store=True, help="Direct Discount.")
    amount_discount_total = fields.Float(string="Discount Total", compute='_compute_amounts', store=True, help="Total of discount amount given each line. Previously this field was called amount_ps")
    amount_dealer_expense = fields.Float(string="Dealer Expense",compute='_compute_amounts', store=True, help="Total of Discount amount given each line. Previously this field was called amount_pot")
    amount_receivable = fields.Float(string='Piutang', compute='_compute_amounts', store=True, help="Total Receivable.")
    amount_unit_tax = fields.Float(string='Amount unit tax', compute='_compute_amounts', store=True, help="Total Harga Unit - Discount Total (Tanpa pajak).")

    # Audit Trail Fields
    date_order = fields.Datetime("Order Date", default=_get_default_date)
    confirm_uid = fields.Many2one('res.users', 'Confirmed By')
    confirm_date = fields.Datetime('Confirmed Date')
    
    # 9: relation fields
    payment_type_id = fields.Many2one('tw.selection', string='Jenis Pembayaran', domain=[('type','=','PaymentType')])
    payment_type = fields.Char(string='Payment Type Value',compute='_compute_payment_type')
    mediator_id = fields.Many2one('res.partner', 'Mediator')
    sales_id = fields.Many2one('hr.employee', 'Salesman')
    sales_coordinator_id = fields.Many2one('hr.employee', 'Sales Coordinator', store=True, compute='_compute_sales_coordinator_id')
    order_line = fields.One2many('tw.dealer.sale.order.line',inverse_name='order_id',string="Order Lines",copy=True, auto_join=True)
    payment_ids = fields.One2many('tw.dealer.sale.order.payment',inverse_name='order_id',string="Payments Lines",copy=True, auto_join=True)
    payment_entry_ids = fields.Many2many('account.move.line',relation='tw_dealer_sale_order_payment_entry_rel',column1='order_id', column2='move_line_id',compute='_compute_payment_entries',string='Payment Entries', store=False)
    summary_discount_ids = fields.One2many('tw.dealer.sale.order.summary', inverse_name='order_id', string='Summary Discount')
    picking_ids = fields.One2many('stock.picking', 'dealer_sale_order_id', string='Transfers')
    tag_ids = fields.Many2many('crm.tag',relation='tw_dealer_sale_order_tag_rel',column1='order_id', column2='tag_id',string="Tags")
    transaction_ids = fields.Many2many('payment.transaction',relation='tw_dealer_sale_order_transaction_rel',column1='order_id', column2='transaction_id',string="Transactions",copy=False, readonly=True)
    authorized_transaction_ids = fields.Many2many('payment.transaction',relation='tw_dealer_sale_order_authorized_transaction_rel',column1='order_id', column2='transaction_id',string="Authorized Transactions",compute='_compute_authorized_transaction_ids',copy=False,compute_sudo=True)
    product_category_ids = fields.Many2many('product.category',relation='tw_dealer_sale_order_prod_categ_rel',column1='order_id', column2='product_category_id',compute='_compute_product_category_ids',string="Product Category")
    account_move_count = fields.Integer(string="Journal Entry Count", compute='_compute_account_move_count')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('order_line.price_subtotal','order_line.gross_profit_unit','order_line.price_subtotal','order_line.discount_total', 'currency_id', 'company_id')
    def _compute_amounts(self):
        super()._compute_amounts()
        for order in self:
            order._recompute_totals()

    @api.depends('partner_id')
    def _compute_payment_entries(self):
        for order in self:
            move_line_ids = order.env['account.move.line'].search([
                ('company_id', '=', order.company_id.id),
                ('division', '=', order.division),
                ('partner_id', '=', order.partner_id.id),
                ('reconciled', '=', False),
                ('move_id.state', '=', 'posted'),
                ('credit', '>', 0)])
            order.payment_entry_ids = [(6, 0, move_line_ids.ids)]

    @api.depends('payment_ids.amount_allocation')
    def _compute_payment_amounts(self):
        for order in self:
            order.amount_payment = sum(order.payment_ids.mapped('amount_allocation'))

    @api.depends('user_id', 'company_id')
    def _compute_warehouse_id(self):
        for order in self:
            default_warehouse_id = self.env['ir.default'].with_company(
                order.company_id.id)._get_model_defaults('tw.dealer.sale.order').get('warehouse_id')
            if order.state in ['draft', 'sent'] or not order.ids:
                # Should expect empty
                if default_warehouse_id is not None:
                    order.warehouse_id = default_warehouse_id
                else:
                    order.warehouse_id = order.user_id.with_company(order.company_id.id)._get_default_warehouse_id()

    @api.depends('payment_type_id')
    def _compute_payment_type(self):
        for order in self:
            order.payment_type = order.payment_type_id.value

    @api.depends('company_id')
    def _compute_journal_id(self):
        super()._compute_journal_id()
        for order in self:
            journal = order._get_journal_id()
            order.journal_id = journal

    @api.depends('division')
    def _compute_product_category_ids(self):
        for order in self:
            if order.division:
                order.product_category_ids = [(6, 0, self.env['product.category'].get_child_ids(order.division))]
            else:
                order.product_category_ids = False

    @api.depends('transaction_ids')
    def _compute_authorized_transaction_ids(self):
        for trans in self:
            trans.authorized_transaction_ids = trans.transaction_ids.filtered(lambda t: t.state == 'authorized')

    @api.depends('partner_id', 'company_id')
    def _compute_pricelist_id(self):
        for order in self:
            if order.company_id:
                if order.company_id.branch_setting_id:
                    order.pricelist_id = order.company_id.branch_setting_id.pricelist_sale_unit_id
                else:
                    raise Warning(_("Tidak ada pricelist yang dipilih! Set 'Price List Jual Unit' di Branch Setting sebelum membuat Dealer Sale Order."))
            else:
                super()._compute_pricelist_id()

    @api.depends('order_line.invoice_lines')
    def _get_invoiced(self):
        # The invoice_ids are obtained thanks to the invoice lines of the SO
        # lines, and we also search for possible refunds created directly from
        # existing invoices. This is necessary since such a refund is not
        # directly linked to the SO.
        for order in self:
            invoices = order.order_line.sudo().invoice_lines.move_id.filtered(lambda r: r.ref == order.client_order_ref and r.move_type in ('out_invoice', 'out_refund', 'entry'))
            order.invoice_ids = invoices
            order.invoice_count = len(invoices)
    
    def _compute_account_move_count(self):
        for order in self:
            order.account_move_count = self.env['account.move'].search_count([
                ('ref', '=', order.name),
                ('company_id', '=', order.company_id.id),
            ])

    @api.depends('sales_id')
    def _compute_sales_coordinator_id(self):
        for order in self:
            if order.sales_id:
                if order.sales_id.job_id.sales_force_id.value in ('sales_coordinator', 'sales_operation_head'):
                    order.sales_coordinator_id = order.sales_id.id
                else:
                    if not order.sales_id.coach_id:
                        raise Warning(_("Salesman yang dipilih tidak memiliki Coach / Coordinator!"))
                    order.sales_coordinator_id = order.sales_id.coach_id.id

    @api.depends('partner_id')
    def _compute_payment_term_id(self):
        for order in self:
            order = order.with_company(order.company_id)
            order.payment_term_id = order.partner_id.property_payment_term_id.id

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        super()._onchange_partner_id()
        self.amount_payment = False
        self.payment_ids = False

    @api.onchange('company_id')
    def _onchange_company_id(self):
        selection = self.env['tw.selection']
        job = self.env['hr.job']
        employee = self.env['hr.employee']

        self.mediator_id = False
        self.sales_id = False
        self.sales_coordinator_id = False
        
        sales_forces = selection.search([('type', '=', 'SalesForce'), ('value', '!=', 'mechanic')])
        jobs = job.search([('sales_force_id', 'in', sales_forces.ids)])
        sales_domain = [('job_id', 'in', jobs.ids)]
        if self.company_id:
            sales_domain.append(('company_id', '=', self.company_id.id))

        salesmen = employee.search(sales_domain)
        if not salesmen:
            raise Warning(_("Pastikan ada Salesman yang terdaftar di %s!", self.company_id.name))

    # 12: override base methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('company_id'):
                raise Warning(_("Dealer/Cabang harus diisi!"))
            branch = self.env['res.company'].browse(vals.get('company_id'))
            ref = self.env['ir.sequence'].get_sequence_code('SO', branch.code)
            vals['name'] = ref
            vals['client_order_ref'] = ref  # the default _prepare_invoice() method using this field as ref
            if not vals.get('order_line'):
                raise Warning(_("Detail sales (order lines) tidak boleh kosong!"))
            
        create = super().create(vals_list)
        return create
    
    def write(self, vals):
        if vals.get('name'):
            vals['client_order_ref'] = vals['name']
        write = super().write(vals)
        if not self.order_line:
            raise Warning(_("Detail sales (order lines) tidak boleh kosong!"))
        return write
    
    def unlink(self):
        for dso in self:
            if dso.state != 'draft':
                raise Warning('Tidak bisa di hapus selain draft!')
            for line in dso.order_line:
                line.lot_id.write({'state': 'stock'})
        return super().unlink()

    # 13: action methods
    def action_dso_list(self):
        emp = self.env['hr.employee'].suspend_security().search([('user_id', '=', self.env.uid)], limit=1)
        areas_ids = self.env.user.company_ids.ids
        if emp.job_id.is_sales_digital:
            sales_digital_ids = self._get_sales_digital_user()
            _logger.info(f"Sales Digital IDs: {sales_digital_ids}")
            domain = [('sales_id', 'in', sales_digital_ids), ('company_id', 'in', areas_ids)]
            _logger.info(f"Domain Sales Digital: {domain}")
        else:
            domain = [('company_id', 'in', areas_ids)]
            
        list_id = self.env.ref('tw_dealer_sale_order.tw_dealer_order_view_list').id
        form_id = self.env.ref('tw_dealer_sale_order.tw_dealer_order_view_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Dealer Sales Order',
            'path': 'dealer-sale-order',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.dealer.sale.order',
            'domain': domain,
            'views': [(list_id, 'list'), (form_id, 'form')],
            'context': {
                'search_default_state_draft': 1,
                'default_division': 'Unit',
                'readonly_by_pass': True
            }
        }

    def action_view_invoice(self, invoices=False):
        invoices = self.env['account.move'].search([
            ('company_id', '=', self.company_id.id),
            ('ref', '=', self.client_order_ref),
            ('move_type', 'in', ('out_invoice', 'out_refund','entry'))
        ])
        return super().action_view_invoice(invoices=invoices)
    
    def action_view_journal_entry(self):
        invoices = self.env['account.move'].search([
            ('company_id', '=', self.company_id.id),
            ('ref', '=', self.client_order_ref),
        ])
        return super().action_view_invoice(invoices=invoices)

    def action_confirm(self):
        self.ensure_one()
        if self.confirm_date:
            raise Warning('SO sudah di confirm!')

        self.sudo()._recompute_totals()
        self.sudo()._validate_dealer_sale_order()
        res = super().action_confirm()
        # Create invoice after confirmation
        self.sudo().action_create_invoice()

        additional_vals_lot = {
            'invoice_date': self._get_default_date(),
            'payment_type_id': self.payment_type_id.id
        }
        self.order_line.sudo().update_lot(additional_vals=additional_vals_lot)
        self.write({
            'confirm_uid': self.env.user.id,
            'confirm_date': fields.Datetime.now()
        })
        return res
    
    def _check_dso_done(self):
        """
        Check if the DSO should be moved to 'done' state.
        Conditions:
        - Delivery status is 'full' (all pickings done)
        - Relevant invoice is paid (SL for Cash, DP for Credit)
        """
        self.ensure_one()
        if self.state != 'sale':
            return
        
        order_line = self.order_line.filtered(lambda l: l.item_type == 'main')
        # 1. Check Delivery Status
        ordered_qty = sum(order_line.mapped('product_uom_qty'))
        delivered_qty = sum(order_line.mapped('qty_delivered'))
        if ordered_qty == 0 or delivered_qty < ordered_qty:
            return
        
        # 2. Check Payment Status based on Payment Type
        is_paid = False
        payment_type = self.payment_type_id.name
        account_setting = self.company_id.branch_setting_id.account_setting_id
        
        if payment_type == 'Cash':
            # For Cash, we expect the main (Settlement/SL) invoice to be paid.
            journal = account_setting.journal_dso_settlement_id
            sl_invoices = self.invoice_ids.filtered(lambda inv: inv.journal_id.id == journal.id and 'SL/' in inv.name)
            if sl_invoices and all(inv.payment_state in ('paid', 'in_payment') for inv in sl_invoices):
                is_paid = True
        elif payment_type == 'Credit':
            # For Credit, we expect the DP invoice to be paid.
            journal = account_setting.journal_dso_downpayment_id
            dp_invoices = self.invoice_ids.filtered(lambda inv: inv.journal_id.id == journal.id and 'DP/' in inv.name)
            if dp_invoices and all(inv.payment_state in ('paid', 'in_payment') for inv in dp_invoices):
                is_paid = True
        
        if is_paid:
            self.action_done()

    def _check_dso_revert_sale(self):
        """
        Check if a 'done' DSO needs to be reverted back to 'sale' state.
        This happens when a delivery is returned or a payment is cancelled.
        """
        self.ensure_one()

        # 1. Check Payment Status based on Payment Type
        is_paid = False
        payment_type = self.payment_type_id.name
        order_line = self.order_line.filtered(lambda l: l.item_type == 'main')

        if payment_type == 'Cash':
            sl_invoices = self.invoice_ids.filtered(lambda inv: inv.name and 'SL/' in inv.name)
            if sl_invoices and all(inv.payment_state in ('paid', 'in_payment') for inv in sl_invoices):
                is_paid = True
        elif payment_type == 'Credit':
            dp_invoices = self.invoice_ids.filtered(lambda inv: inv.name and 'DP/' in inv.name)
            if dp_invoices and all(inv.payment_state in ('paid', 'in_payment') for inv in dp_invoices):
                is_paid = True

        if not is_paid:
            for lot in order_line.mapped('lot_id'):
                # Revert paid → sold jika payment dibatalkan.
                # paid_offtr tidak di-revert karena off-the-road memiliki alur tersendiri.
                if lot.state == 'paid':
                    lot.write({'state': 'sold'})
            if self.state == 'done':
                self.write({'state': 'sale'})

        # 2. Check Delivery Status
        ordered_qty = sum(order_line.mapped('product_uom_qty'))
        delivered_qty = sum(order_line.mapped('qty_delivered'))
        if ordered_qty == 0 or delivered_qty < ordered_qty:
            for lot in order_line.mapped('lot_id'):
                if lot.state == 'sold':
                    lot.write({'state': 'reserved'})
            if self.state == 'done':
                self.write({'state': 'sale'})
            return
        

    def action_done(self):
        self.ensure_one()
        self.write({
            'state': 'done',
        })

    def action_paid(self):
        self.ensure_one()
        self.order_line.update_lot_state_paid()
        # Trigger 'Done' check when an invoice related to this order is paid
        self._check_dso_done()
    
    def action_create_invoice(self):
        for line in self.order_line:
            line.qty_to_invoice = 1
        moves = self._create_invoices()
        moves.filtered(lambda x: x.state == 'draft').action_post()

    def action_cancel(self):
        if self.state == 'cancel':
            raise UserError(f'Silakan refresh halaman ini, karena state telah {self._get_state_value()}')
        for order in self:
            order.write({
                'state': 'cancel',
            })
        super().action_cancel()
    
    def action_set_summary_discount(self):
        self._set_summary_discount()

    def action_recompute_totals(self):
        self._recompute_totals()
    
    def action_dummy_create_procurement(self):
        self.ensure_one()
        for line in self.order_line:
            line._action_launch_stock_rule()

    # 14: private
    def _get_sales_digital_user(self, branch=None):
        if not branch:
            branch = self.env.user.area_id.company_ids.ids
            
        if not branch:
            return []

        self.env.cr.execute(SQL("""
            SELECT e.id
            FROM resource_resource r
            INNER JOIN hr_employee e ON r.id = e.resource_id
            INNER JOIN hr_job j ON e.job_id = j.id
            INNER JOIN res_users u ON r.user_id = u.id
            WHERE 1 = 1
            AND (e.working_end_date IS NULL OR e.working_end_date > NOW())
            AND u.active = true
            AND r.active = true
            AND j.is_sales_digital = true
            AND e.company_id IN %(company_id)s
        """, company_id=tuple(branch)))
        
        res = self.env.cr.fetchall()
        return [r[0] for r in res] if res else []

    def _recompute_totals(self):
        # Recompute Line
        for order in self:
            order.order_line._recompute_line_totals()
            # Recompute Header
            currency = order.currency_id or order.company_id.currency_id
            total_downpayment = total_price_unit = total_price = total_gp_unit = total_discount = total_dealer_expense = total_discount_regular = total_discount_direct = total_discount_untaxed = total_price_unit_tax = 0
            for line in order.order_line:
                total_downpayment += line.downpayment
                total_gp_unit += line.gross_profit_unit
                total_discount += line.discount_total
                total_dealer_expense += line.amount_dealer_expense
                total_discount_regular += line.discount_regular
                total_discount_direct += line.discount_direct
                # Compute Price Unit
                tax = line.tax_id
                price_unit = tax.compute_all(line.price_unit, currency=currency, quantity=line.product_uom_qty)
                total_price += price_unit['total_excluded']
                if line.item_type == 'main':
                    total_price_unit += price_unit['total_excluded']
                    total_price_unit_tax += line.price_unit_tax

            order.amount_selling_price = total_price
            order.amount_unit_price = total_price_unit
            order.amount_downpayment = total_downpayment
            order.amount_gp_unit = total_gp_unit
            order.amount_discount_regular = total_discount_regular
            order.amount_discount_direct = total_discount_direct
            order.amount_discount_total = total_discount
            order.amount_dealer_expense = total_dealer_expense
            order.amount_receivable = order.amount_total - order.amount_downpayment
            order.amount_unit_tax = total_price_unit_tax

    ### ------------ Validation ---------------- ###
    def _validate_dealer_sale_order(self):
        self.ensure_one()
        serial_number = []
        for line in self.order_line:
            # Helper: use engine number (lot_id.name) if available, otherwise product name
            line_identifier = line.lot_id.name if line.lot_id else line.product_id.display_name

            if line.item_type == 'main':
                if not line.lot_id:
                    raise Warning(_("Serial Number pada produk %s harus di isi!") % line.product_id.display_name)
            
                if line.lot_id:
                    if line.lot_id in serial_number:
                        raise Warning(_("Serial Number %s pada produk %s tidak boleh duplikat!") % (line.lot_id.name, line.product_id.display_name))
                    serial_number.append(line.lot_id)

                if self.finco_id and line.product_id and line.item_type == 'main':
                    if not all([line.finco_po_date, line.finco_po_number]):
                        raise Warning(_("Nomor PO Finco dan Tanggal PO untuk No Mesin %s harus di isi!") % line_identifier)
                    if line.tenor <= 0 or line.installment <= 0:
                        raise Warning(_("Tenor dan Cicilan untuk No Mesin %s harus lebih dari 0!") % line_identifier)
                    if not line.biro_jasa_id:
                        raise Warning(_("Penjualan credit untuk No Mesin %s harus menggunakan biro jasa!") % line_identifier)
                    if line.downpayment <= 0:
                        raise Warning(_("DP untuk No Mesin %s harus di isi!") % line_identifier)
                    if not line.tax_id:
                        raise Warning(_("Tax untuk No Mesin %s harus di isi!") % line_identifier)
                    if line.biro_jasa_id and line.bbn_amount <= 0:
                        raise Warning(_("BBN Price untuk No Mesin %s cannot be 0!") % line_identifier)
                else:
                    if line.downpayment > 0:
                        raise Warning(_("Cash sales down payment untuk No Mesin %s harus 0!") % line_identifier)

                if line.discount_regular < 0:
                    raise Warning(_("Discount untuk No Mesin %s tidak boleh negatif!") % line_identifier)
            
                # ? Diskon input diminta untuk dimatikan oleh Bu Indira & Pak Riki di UAT 12 Juni
                # if line.discount_input != line.discount_total:
                #     raise Warning(_("Discount Input dan Discount Total untuk No Mesin %s harus sama!") % line_identifier)
                    
        # Ensure all payment lines are validated before requesting approval
        self._validate_payment()

    def _validate_payment(self):
        total_allocation = 0
        self.payment_ids._validate_allocation_amount()
        for payment in self.payment_ids:
            total_allocation += payment.amount_allocation

        dp_rounded = round(self.amount_downpayment, 2)
        total_alloc_rounded = round(total_allocation, 2)
        total_rounded = round(self.amount_total, 2)

        currency = self.currency_id or self.company_id.currency_id
        if self.finco_id:
            if not self.is_cod and dp_rounded != total_alloc_rounded:
                raise Warning(_("""Validasi Gagal, Total pembayaran harus sama dengan nilai DP! \n DP: %s \n Pembayaran: %s""" % (
                    currency.format(dp_rounded),
                    currency.format(total_alloc_rounded)
                )))
        else:
            if not self.is_cod and total_rounded != total_alloc_rounded:
                raise Warning(_("""Validasi Gagal, Total pembayaran harus sama dengan nilai total! \n Total: %s \n Pembayaran: %s""" % (
                    currency.format(total_rounded),
                    currency.format(total_alloc_rounded)
                )))
        
        # Jika journal bukan journal pelunasan SO maka ubah
        journal_pelunasan = self.company_id.branch_setting_id.account_setting_id.journal_dso_settlement_id.id
        if self.journal_id.id != journal_pelunasan:
            self.journal_id = journal_pelunasan

    ### ------------ Invoicing ---------------- ###
    def _prepare_invoice(self):
        values = super()._prepare_invoice()
        if not self.journal_id:
            self.journal_id = self._get_journal_id()
        
        code = self.journal_id.code
        prefix = self.company_id.code
        values.update({
            'name': self.env['ir.sequence'].get_sequence_code(code, prefix),
            'company_id': self.company_id.id,
            'division': self.division,
            'invoice_date': fields.Date.today()
        })
        return values
    
    def _create_account_invoices(self, invoice_vals_list, final):
        """Small method to allow overriding the behavior right after an invoice is created."""
        # Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
        # sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.
        created_move = self.env['account.move'].sudo().with_company(self.company_id).with_context(default_move_type='out_invoice').create(invoice_vals_list)
        # Change payment term line account_id with default debit account from its journal.
        created_move._ajust_payment_term_line_account()
        return created_move
    
    def _create_invoices(self, grouped=False, final=False, date=None):
        self._validate_payment()
        
        main_invoice = self._create_main_invoice()
        dp_invoice = self._create_downpayment_invoice()
        payment_allocation_move = self._create_and_reconcile_payment_allocation_move(main_invoice, dp_invoice)
        
        moves = main_invoice + dp_invoice + payment_allocation_move
        return moves
    
    def _create_main_invoice(self):
        self.ensure_one()
        invoice_vals = self._prepare_main_invoice()
        move = self._create_account_invoices(invoice_vals, final=True)
        return move

    def _prepare_main_invoice(self):
        invoice_vals = self._prepare_invoice()
        invoice_vals['invoice_line_ids'] = self._prepare_main_invoice_line()
        invoice_vals['line_ids'] = self._prepare_main_move_line()
        invoice_vals['line_ids'] += self._prepare_main_move_additional_line()
        invoice_vals['line_ids'] += self._prepare_main_move_discount_line()
        return invoice_vals

    def _prepare_main_invoice_line(self):
        invoiceable_lines = self._get_main_invoiceable_lines(True)
        account_conf = self.company_id.branch_setting_id.account_setting_id
        if not account_conf.journal_dso_downpayment_id:
            raise Warning('Konfigurasi Journal Downpayment pada branch %s belum disetting!' % (self.company_id.branch_setting_id.name))
        default_credit_account_id = account_conf.journal_dso_downpayment_id.default_credit_account_id
        if not default_credit_account_id:
            raise Warning('Konfigurasi default credit account pada journal %s belum disetting!' % (account_conf.journal_dso_downpayment_id.name))    

        # Main Item
        # Group invoices by product, as dealer sale order lines only accept one quantity per serial number.
        invoice_line = []
        for product, line in groupby(invoiceable_lines, key=lambda x: x.product_id):
            price_unit = sum([rec.price_unit for rec in line])
            qty = sum([rec.product_uom_qty for rec in line])
            downpayment = sum([rec.downpayment for rec in line])
            line_ids = [rec.id for rec in line]
            invoice_line.append(
                Command.create(line[0]._prepare_invoice_line(**{
                    'product_id': product.id,
                    'price_unit': price_unit / qty,
                    'quantity': qty,
                    'sequence': 1,
                    'dealer_sale_order_line_ids': [Command.link(line_ids)]
                }))
            )
            if downpayment:
                invoice_line.append(
                    Command.create(line[0]._prepare_invoice_line(**{
                        'name': 'Customer DP',
                        'product_id': False,
                        'account_id': account_conf.journal_dso_downpayment_id.default_credit_account_id.id,
                        'price_unit': -(downpayment),
                        'discount': 0,
                        'quantity': 1,
                        'sequence': 4,
                        'dealer_sale_order_line_ids': [Command.link(line_ids)],
                        'tax_ids': False
                    }))
                )
        return invoice_line
    
    def _prepare_main_move_additional_line(self):
        invoiceable_lines = self._get_additional_invoiceable_lines(True)
        invoice_line = []
        # Additional Item
        for add_line in invoiceable_lines:
            invoice_line.append(
                Command.create(add_line._prepare_invoice_line(**{
                    'name': add_line.name,
                    'product_id': add_line.product_id.id,
                    'price_unit': add_line.price_unit,
                    'quantity': add_line.product_uom_qty,
                    'tax_ids': [Command.set(add_line.tax_id.ids)],
                    'sequence': 2,
                    'dealer_sale_order_line_ids': [Command.link([add_line.id])]
                }))
            )
        return invoice_line
    
    def _prepare_main_move_discount_line(self):
        # Add direct_discount as invoice line 
        # Direct Discount adalah angka diskon yang langsung memotong nilai pelunasan
        invoiceable_lines = self._get_main_invoiceable_lines(True)
        account_conf = self.company_id.branch_setting_id.account_setting_id
        invoice_line = []
        if not account_conf.account_dso_discount_regular_id:
            raise Warning('Konfigurasi Account Discount Regular pada branch %s belum disetting!' % (self.company_id.branch_setting_id.name))
        direct_discount = self._get_direct_discount()
        if direct_discount > 0:
            invoice_line.append(
                Command.create(invoiceable_lines[0]._prepare_invoice_line(**{
                    'name': 'Discount Regular',
                    'price_unit': -direct_discount,
                    'product_id': False,
                    'discount': 0,
                    'quantity': 1,
                    'sequence': 3,
                    'account_id': account_conf.account_dso_discount_regular_id.id
                }))
            )
        return invoice_line

    def _prepare_main_move_line(self):
        return []

    def _get_additional_cancel_account_moves(self):
        self.ensure_one()
        try:
            moves = super()._get_additional_cancel_account_moves()
        except AttributeError:
            moves = self.env['account.move']

        account_conf = self.company_id.branch_setting_id.account_setting_id
        allocation_journal = account_conf.journal_dso_downpayment_allocation_id if account_conf else False
        if not allocation_journal:
            return moves

        allocation_moves = self.env['account.move'].sudo().search([
            ('company_id', '=', self.company_id.id),
            ('journal_id', '=', allocation_journal.id),
            ('move_type', '=', 'entry'),
            ('state', '=', 'posted'),
            ('reversed_entry_id', '=', False),
            ('ref', '=', self.name),
        ])
        return moves | allocation_moves
    
    def _create_and_reconcile_payment_allocation_move(self, main_invoice, dp_invoice):
        to_pay_invoice = main_invoice if self.payment_type_id.name == 'Cash' else dp_invoice

        dp_allocation_move = self.env['account.move']
        if self.payment_ids:
            dp_allocation_move = self._create_downpayment_allocation_move(to_pay_invoice)
            self._reconcile_payment_invoice(to_pay_invoice, dp_allocation_move)

        return dp_allocation_move
    
    def _create_downpayment_invoice(self):
        move = self.env['account.move']
        invoice_vals = self._prepare_downpayment_invoice()
        if invoice_vals:
            move = self._create_account_invoices(invoice_vals, final=True)
        return move
    
    def _prepare_downpayment_invoice(self):
        account_conf = self.company_id.branch_setting_id.account_setting_id
        if not account_conf.journal_dso_downpayment_id:
            raise Warning(_("Journal Downpayment tidak terkonfigurasi.\nSilakan konfigurasikan di menu Branch Settings."))
        invoice_vals = {}
        
        downpayment = sum([line.downpayment for line in self.order_line])
        if downpayment:
            invoice_vals = self._prepare_invoice()
            code = account_conf.journal_dso_downpayment_id.code
            prefix = self.company_id.code
            invoice_vals['name'] = self.env['ir.sequence'].get_sequence_code(code, prefix)
            invoice_vals['journal_id'] = account_conf.journal_dso_downpayment_id.id
            invoice_vals['company_id'] = self.company_id.id
            invoice_vals['invoice_line_ids'] = [
                Command.create(self.order_line[0]._prepare_invoice_line(**{
                    'name': 'Customer Downpayment',
                    'product_id': False,
                    'company_id': self.company_id.id,
                    'price_unit': downpayment,
                    'quantity': 1,
                    'account_id': account_conf.journal_dso_downpayment_id.default_credit_account_id.id,
                    'dealer_sale_order_line_ids': [Command.link([line.id for line in self.order_line])],
                    'tax_ids': False
                }))
            ]
            invoice_vals['line_ids'] = [
                Command.create({
                    'debit': downpayment,
                    'credit': 0,
                    'name': self.name,
                    'ref': self.name,
                    'account_id': account_conf.journal_dso_downpayment_id.default_debit_account_id.id,
                    'company_id': self.company_id.id,
                    'division': self.division
                })
            ]
        return invoice_vals
    
    def _create_downpayment_allocation_move(self, to_pay_invoice):
        allocated_move = self.env['account.move']
        account_conf = self.company_id.branch_setting_id.account_setting_id
        if not account_conf.journal_dso_downpayment_id:
            raise Warning(_("Journal Downpayment tidak terkonfigurasi.\nSilakan konfigurasikan di menu Branch Settings."))
        
        credit_account = to_pay_invoice.line_ids.filtered(lambda x: x.display_type == 'payment_term' and x.debit > 0).account_id
        
        if self.payment_ids:
            AccountMove = self.env['account.move']
            if not account_conf.journal_dso_downpayment_allocation_id:
                raise Warning(_("Journal Alokasi DP tidak terkonfigurasi.\n"
                                "Silakan konfigurasikan di menu Branch Settings."))
            
            allocated_move_vals = self._prepare_invoice()
            code = account_conf.journal_dso_downpayment_allocation_id.code
            prefix = self.company_id.code
            allocated_move_vals.update({
                'name': self.env['ir.sequence'].get_sequence_code(code, prefix),
                'move_type': 'entry',
                'journal_id': account_conf.journal_dso_downpayment_allocation_id.id,
                'partner_id': self.partner_id.id,
                'partner_shipping_id': self.partner_id.id,
            })

            total_payment = 0
            allocated_move_line = []
            for payment in self.payment_ids:
                if payment.payment_entry_id.reconciled:
                    raise Warning(_("Payment entry '{payment.payment_entry_id.name}' sudah dilakukan pencairan."))
                if payment.amount_balance < payment.amount_allocation:
                    raise Warning(_(f"Jumlah alokasi pembayaran tidak boleh melebihi saldo yang tersisa dari payment entry '{payment.payment_entry_id.name}'."))
                
                total_payment += payment.amount_allocation
                move_line = payment.payment_entry_id.read()[0]
                allocated_move_line.append(Command.create({
                    'debit': payment.amount_allocation,
                    'credit': 0,
                    'name': payment.payment_entry_id.name,
                    'ref': self.name,
                    'account_id': move_line.get('account_id')[0],
                    'company_id': move_line.get('company_id')[0],
                    'division': move_line.get('division')
                }))
            
            allocated_move_line.append(Command.create({
                'debit': 0,
                'credit': total_payment,
                'ref': self.name,
                'display_type': 'product',
                'account_id': credit_account.id,
                'company_id': self.company_id.id,
                'division': self.division
            }))
            allocated_move_vals['line_ids'] = allocated_move_line
            allocated_move = AccountMove.with_context(default_move_type='entry').create(allocated_move_vals)
            allocated_move.sudo().action_post()
        return allocated_move
    
    def _reconcile_payment_invoice(self, to_pay_invoice, dp_allocation_move):
        to_reconcile_inv = to_pay_invoice + dp_allocation_move
        draft_to_reconcile_inv = to_reconcile_inv.filtered(lambda x: x.state == 'draft')
        if draft_to_reconcile_inv:
            draft_to_reconcile_inv.sudo().action_post()

        # Reconcile Setlement (AL) dengan Invoice (DP) supaya DP langsung paid
        credit_line = dp_allocation_move.line_ids.filtered(lambda x: x.credit > 0)
        payment_receivable = to_pay_invoice.line_ids.filtered(lambda x: x.account_id == credit_line.account_id and x.debit > 0)
        if not credit_line:
            raise Warning(_("Settlement (%s) tidak memiliki credit line." % dp_allocation_move.name))
        if not payment_receivable:
            raise Warning(_("Invoice yang akan dibayar (%s) tidak memiliki payment receivable line dengan account %s." % (to_pay_invoice.name, credit_line.account_id.display_name)))
        (credit_line | payment_receivable).reconcile()

        # Reconcile Setlement (AL) dengan Receive Payment (HL)
        debit_line = dp_allocation_move.line_ids.filtered(lambda x: x.debit > 0)
        journal_hl = self.payment_ids.mapped('payment_entry_id')
        if not debit_line:
            raise Warning(_("Settlement (%s) tidak memiliki debit line." % dp_allocation_move.name))
        if not journal_hl:
            raise Warning(_("Hutang Lainnya di Payment Line tidak ada."))
        (debit_line | journal_hl).reconcile()

    def _generate_downpayment_invoices(self):
        """ Generate invoices as down payments for sale order.

        :return: The generated down payment invoices.
        :rtype: recordset of `account.move`
        """
        generated_invoices = self.env['account.move']

        for order in self:
            downpayment_wizard = order.env['tw.dealer.sale.advance.payment.inv'].create({
                'delaer_sale_order_ids': order,
                'advance_payment_method': 'fixed',
                'fixed_amount': order.amount_paid,
            })
            generated_invoices |= downpayment_wizard._create_invoices(order)

        return generated_invoices
    
    def _get_journal_id(self):
        self.ensure_one()
        if not self.company_id:
            raise Warning(_("Dealer/Cabang belum diisi!"))
        
        account_conf = self.company_id.branch_setting_id.account_setting_id
        if not account_conf:    
            raise Warning(_("Pastikan Dealer/Cabang yang dipilih sudah memiliki Accounting yang terkonfigurasi.\nAnda bisa mengaturnya di menu Branch Setting."))
        if not account_conf.journal_dso_settlement_id:
            raise Warning(_("Journal Pelunasan SO belum terkonfigurasi.\nSilakan konfigurasikan di menu Branch Setting."))
        return account_conf.journal_dso_settlement_id.id
    
    def _get_main_invoiceable_lines(self, final=False):
        invoiceable_lines = self._get_invoiceable_lines(final)
        return invoiceable_lines.filtered(lambda x: x.item_type == 'main')
    
    def _get_additional_invoiceable_lines(self, final=False):
        invoiceable_lines = self._get_invoiceable_lines(final)
        return invoiceable_lines.filtered(lambda x: x.item_type == 'additional')
    
    def _get_invoiceable_lines(self, final=False):
        """Return the invoiceable lines for order `self`."""
        down_payment_line_ids = []
        invoiceable_line_ids = []
        pending_section = None
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self.order_line:
            if line.display_type == 'line_section':
                # Only invoice the section if one of its lines is invoiceable
                pending_section = line
                continue
            if line.display_type != 'line_note' and float_is_zero(line.qty_to_invoice, precision_digits=precision):
                continue
            if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final) or line.display_type == 'line_note':
                if line.is_downpayment:
                    # Keep down payment lines separately, to put them together
                    # at the end of the invoice, in a specific dedicated section.
                    down_payment_line_ids.append(line.id)
                    continue
                if pending_section:
                    invoiceable_line_ids.append(pending_section.id)
                    pending_section = None
                invoiceable_line_ids.append(line.id)

        return self.env['tw.dealer.sale.order.line'].browse(invoiceable_line_ids + down_payment_line_ids)
    
    ### ------------End of Invoicing ---------------- ###

    def _get_direct_discount(self):
        discount = sum(self.order_line.mapped('discount_regular'))
        return discount
    
    def _log_decrease_ordered_quantity(self, documents, cancel=False):
        def _render_note_exception_quantity_so(rendering_context):
            order_exceptions, visited_moves = rendering_context
            visited_moves = list(visited_moves)
            visited_moves = self.env[visited_moves[0]._name].concat(*visited_moves)
            order_line_ids = self.env['tw.dealer.sale.order.line'].browse([order_line.id for order in order_exceptions.values() for order_line in order[0]])
            sale_order_ids = order_line_ids.mapped('order_id')
            impacted_pickings = visited_moves.filtered(lambda m: m.state not in ('done', 'cancel')).mapped('picking_id')
            values = {
                'sale_order_ids': sale_order_ids,
                'order_exceptions': order_exceptions.values(),
                'impacted_pickings': impacted_pickings,
                'cancel': cancel
            }
            return self.env['ir.qweb']._render('sale_stock.exception_on_so', values)

        self.env['stock.picking']._log_activity(_render_note_exception_quantity_so, documents)

    def _prepare_partner_cdb(self):
        """
        Prepare CDB (Customer Database) values from dealer sale order data.
        """
        for order in self.filtered(lambda o: o.partner_id):
            # Check if CDB record already exists for this partner and lot
            order_line_objs = order.order_line.filtered(lambda l: l.item_type == 'main')
            for line in order_line_objs:
                cdb_vals = {
                    'lot_ids': [(4, line.lot_id.id)],
                    'company_id': order.company_id.id,
                    'product_id': line.product_id.id,
                    'downpayment': line.downpayment,
                    'installments': line.installment,
                    'tenor': line.tenor,
                    'sales_channel_id': order.sales_channel_id.id,
                    'employee_id': order.sales_id.id,
                }
        return cdb_vals
    
    def _set_summary_discount(self):
        product_ids = []
        # Sort order lines by product_id to allow grouping
        order_lines = self.order_line.filtered(lambda l: l.item_type == 'main')
        order_lines = sorted(order_lines, key=lambda l: l.product_id.id)
        # Group lines by product_id
        for product_id, lines in groupby(order_lines, key=lambda l: l.product_id.id):
            # SUM() untuk mengubah list of recordsets menjadi object
            # EX : [tw.dealer.sale.order.line(10,),tw.dealer.sale.order.line(11,)] -> tw.dealer.sale.order.line(10,11)
            lines = sum(lines, self.env['tw.dealer.sale.order.line'])
            product_ids.append(product_id)
            data = self._prepare_sumary_discount_data(product_id, lines)
            existing_summary = self.summary_discount_ids.filtered(lambda x: x.product_id.id == product_id)
            if existing_summary:
                existing_summary.write(data)
            else:
                self.env['tw.dealer.sale.order.summary'].create(data)

        # Delete summary that not in product_ids
        to_be_deleted_summary = self.env['tw.dealer.sale.order.summary'].search([('order_id', '=', self.id), ('product_id', 'not in', product_ids)])
        to_be_deleted_summary.unlink()

        # Update the record with the new summary
        return self.env['tw.dealer.sale.order.summary'].search([('order_id', '=', self.id), ('product_id', 'in', product_ids)])
    
    def _prepare_sumary_discount_data(self, product_id, lines):
        return {
            'order_id': self.id,
            'product_id': product_id,
            'currency_id': self.currency_id.id or self.company_id.currency_id.id,
            'tax_id': [(6, 0, list(set(lines.mapped('tax_id').ids)))],
            'product_qty': sum(lines.mapped('product_uom_qty')),
            'price_unit': sum(lines.mapped('price_unit')),
            'direct_discount': self._get_direct_discount(),
            'discount_regular': sum(lines.mapped('discount_regular')),
            'price_unit_purchase': sum(lines.mapped('price_unit_purchase')),
            'gross_profit_unit': sum(lines.mapped('gross_profit_unit')),
        }
