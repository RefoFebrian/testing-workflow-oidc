# -*- coding: utf-8 -*-

# 1: imports of python lib
from contextlib import contextmanager
from datetime import datetime
# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

# 4:  imports from odoo modules


# 5: local imports

# 6: Import of unknown third party lib

class InheritAccountMove(models.Model):
    _inherit = "account.move"
    _order = "id desc"
    
    # 7: defaults methods
    def _get_default_date(self):
        return self.env['res.company'].get_default_date()

    # 8: fields
    confirm_uid = fields.Many2one('res.users', 'Confirmed by')
    confirm_date = fields.Datetime('Confirmed on')
    cancel_uid = fields.Many2one('res.users', 'Cancelled by')
    cancel_date = fields.Datetime('Cancelled on')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
    is_limit_edit = fields.Boolean('Limit Editing', help="Limit the value that can be edited, this used for transaction like PO, when the product, price, and other is based on the PO transaction.")
    note = fields.Text('Note')
    supplier_invoice_number = fields.Char('Supplier Invoice Number')

    # 9: relation fields
    product_category_ids = fields.Many2many(
        comodel_name='product.category',
        relation='tw_account_move_prod_categ_rel', column1='move_id', column2='product_category_id',
        compute='_compute_product_category_ids',
        string="Product Category")
    
    # === Partner fields di inherit untuk menghilangkan check_company=True === #
    partner_id = fields.Many2one('res.partner', string='Partner', readonly=False, tracking=True, inverse='_inverse_partner_id', change_default=True, index=True, ondelete='restrict', check_company=False)
    commercial_partner_id = fields.Many2one('res.partner', string='Commercial Entity', compute='_compute_commercial_partner_id', store=True, readonly=True, ondelete='restrict', check_company=False)
    partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address', compute='_compute_partner_shipping_id', store=True, readonly=False, precompute=True, help="The delivery address will be used in the computation of the fiscal position.", check_company=False)
    partner_bank_id = fields.Many2one('res.partner.bank', string='Recipient Bank', compute='_compute_partner_bank_id', store=True, readonly=False, help="Bank Account Number to which the invoice will be paid. "
             "A Company bank account if this is a Customer Invoice or Vendor Credit Note, "
             "otherwise a Partner bank account number.", tracking=True, ondelete='restrict', check_company=False)

    # 10: constraints & sql constraints
    @api.constrains('journal_id', 'move_type')
    def _check_journal_move_type(self):
        # Inherit constraint bawaan untuk membuat warning yang lebih bagus
        for move in self:
            identifier = move.name or move.ref
            if move.is_purchase_document(include_receipts=True) and move.journal_id.type != 'purchase':
                raise ValidationError(_("Cannot create a purchase document %s in a non purchase journal %s") % (identifier, move.journal_id.name))
            if move.is_sale_document(include_receipts=True) and move.journal_id.type != 'sale':
                raise ValidationError(_("Cannot create a sale document %s in a non sale journal %s") % (identifier, move.journal_id.name))

    # 11: compute/depends & on change methods
    @api.depends('division')
    def _compute_product_category_ids(self):
        for order in self:
            prod_categ = order.env['product.category']
            if order.division:
                prod_categ_ids = prod_categ.get_child_ids(order.division)
            else:
                prod_categ_ids = prod_categ.get_child_ids('All')
            order.product_category_ids = [(6, 0, prod_categ_ids)]
        
    def _compute_payments_widget_to_reconcile_info(self):
        # Inherit untuk menghilangkan tombol ADD di bawah kanan invoice 
        # Tombol tersebut digunakan untuk melakukan pembayaran secara cepat
        # Namun tidak sesuai dengan flow yang ada di Teds
        for move in self:
            move.invoice_outstanding_credits_debits_widget = False
            move.invoice_has_outstanding = False

    # 12: override methods
    @contextmanager
    def _sync_tax_lines(self, container):
        """Override untuk memastikan company_id pada tax line yang di-generate otomatis
        mengikuti company dari account.move-nya, bukan dari active branch.

        Diperlukan karena account.move.line.company_id sudah di-override menjadi
        field manual (bukan related), sehingga tidak ter-propagasi otomatis.
        """
        with super()._sync_tax_lines(container):
            yield
        for move in container.get('records', self.env['account.move']):
            if move.state != 'draft':
                continue
            wrong_company_tax_lines = move.line_ids.filtered(
                lambda l: l.display_type == 'tax' and l.company_id != move.company_id
            )
            if wrong_company_tax_lines:
                wrong_company_tax_lines.with_context(skip_invoice_sync=True).write(
                    {'company_id': move.company_id.id}
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # isi company di journal items
            if vals.get('name'):
                existed_entry_name = self.env['account.move'].sudo().search([('name','=',vals['name'])],limit=1)
                if existed_entry_name:
                    raise UserError('Failed to create move %s. Another entry with the same name already exist'%(vals['name']))
            if vals.get('line_ids'):
                for line_vals in vals.get('line_ids'):
                    if not line_vals[2].get('company_id'):
                        if vals.get('company_id'):
                            line_vals[2]['company_id'] = vals.get('company_id')
                        else:
                            raise UserError("Company ID is required on the line %s" % line_vals[2].get('name'))
            # isi company di invoice line
            if vals.get('invoice_line_ids'):
                for line_vals in vals.get('invoice_line_ids'):
                    if not line_vals[2].get('company_id'):
                        if vals.get('company_id'):
                            line_vals[2]['company_id'] = vals.get('company_id')
                        else:
                            raise UserError("Company ID is required on the invoice line %s" % line_vals[2].get('name'))
        created = super().create(vals_list)
        return created

    def write(self, vals):
        if vals.get('name'):
            existed_entry_name = self.env['account.move'].sudo().search([('name','=',vals['name'])],limit=1)
            if existed_entry_name:
                raise UserError('Failed to edit move %s. Another entry with the same name already exist'%(vals['name']))
        for move in self:
            if move.name:
                lines_without_name = move.line_ids.filtered(lambda x: not x.name)
                if lines_without_name:
                    lines_without_name.write({'name': move.name})
        return super().write(vals)

    def unlink(self):
        for data in self:
            if data.state != 'draft':
                raise UserError('You cannot delete a document that is not in draft state')
        return super().unlink()

    def get_formview_action(self, access_uid=None):
        """ Override this method in order to redirect many2one towards the right model depending on access_uid """
        user = self.env.user
        if access_uid:
            user = self.env['res.users'].browse(access_uid).sudo()
        if not user.has_group('tw_account.group_tw_account_move_form_read'):
            raise UserError(_("You do not have access to this document."))
            
        res = super().get_formview_action(access_uid=access_uid)
        return res

    # 13: action methods
    def action_open(self):
        """
        The 'open' state is an intermediate state between 'draft' and 'posted'.
        It should allow the invoice/move to be editable, especially for pricing and discounts.
        """
        self._check_valid_invoice()
        self.is_limit_edit = True
        self.sudo()._create_intercompany_move()
    
    def _post(self, soft=True):
        self.sudo()._create_intercompany_move()
        account_move = super()._post(soft)
        return account_move
    
    def action_post(self):
        self._check_valid_invoice()
        account_move = super().action_post()
        self.write({
            'confirm_uid': self.env.uid,
            'confirm_date': datetime.now(),
        })
        return account_move
    
    def action_print_invoice_pdf(self):
        self.ensure_one()
        return self.env.ref('account.account_invoices').report_action(self)
    
    def button_cancel(self):
        account_move = super().button_cancel()
        self.write({
            'cancel_uid': self.env.uid,
            'cancel_date': datetime.now()
        })
        return account_move
    
    def button_draft(self):
        account_move = super().button_draft()
        self.write({
            'confirm_uid': False,
            'confirm_date': False,
        })
        return account_move
    
    def _check_valid_invoice(self):
        for move in self:
            if move.state == 'posted':
                raise UserError("Invoice sudah terposting! Silahkan refresh halaman Anda.")
            if move.move_type != 'entry':
                for inv_line in move.invoice_line_ids:
                    if inv_line.product_id:
                        if inv_line.price_unit <= 0:
                            raise UserError("Harga harus lebih dari 0 ! \n\nPerbaiki harga untuk produk %s !" % inv_line.product_id.name)
                        if inv_line.quantity <= 0:
                            raise UserError("Jumlah harus lebih dari 0 ! \n\nPerbaiki jumlah untuk produk %s !" % inv_line.product_id.name)
                        if inv_line.discount < 0:
                            raise UserError("Discount tidak boleh negatif ! \n\nPerbaiki discount untuk produk %s !" % inv_line.product_id.name)

    def _ajust_payment_term_line_account(self):
        for move in self:
            journal_id = move.journal_id
            if not journal_id:
                continue
            debit_acc  = journal_id.default_debit_account_id
            credit_acc = journal_id.default_credit_account_id
            target_account = False
            if move.is_sale_document(include_receipts=True) and debit_acc:
                target_account = debit_acc
            elif move.is_purchase_document(include_receipts=True) and credit_acc:
                target_account = credit_acc
            if target_account:
                move.line_ids.filtered(lambda l: l.display_type == 'payment_term').write({'account_id': target_account.id})

    def _create_intercompany_move(self):
        """
        Create intercompany journal entries for moves with transactions across multiple branches.
        
        Args:
            move_ids (list): List of account.move ids to process
            
        Returns:
            list: List of processed move ids
        """
        for move in self:
            branch_summary = {}
            # Cek move dengan branch, jika tidak ada, tidak perlu interco
            move_lines = move.line_ids.filtered(lambda l: l.company_id)
            if not move_lines:
                continue
                
            # Group lines by branch and calculate totals
            for line in move_lines:
                branch = line.company_id
                if branch not in branch_summary:
                    branch_summary[branch] = {
                        'debit': line.debit,
                        'credit': line.credit,
                        'division': line.division,
                        'total': line.debit + line.credit
                    }
                else:
                    branch_summary[branch]['debit'] += line.debit
                    branch_summary[branch]['credit'] += line.credit
                    branch_summary[branch]['total'] += line.debit + line.credit
            
            # Skip if not enough branches or the imbalance does'nt exist
            # This prevent duplicate intercompany move
            if len(branch_summary) < 2 or all(
                values['debit'] == values['credit'] 
                for values in branch_summary.values()
            ):
                continue
                
            # Sort branches by total amount (descending)
            sorted_branches = sorted(
                branch_summary.items(),
                key=lambda branch: branch[1]['total'],
                reverse=True
            )
            
            main_branch, main_values = sorted_branches[0]
            main_branch_account = main_branch.branch_setting_id.inter_company_account_id
            
            if not main_branch_account:
                raise UserError((
                    "[%s] Account Inter belum diisi pada Master branch %s - %s"
                ) % (move.name,main_branch.code, main_branch.name))
                
            # Prepare intercompany entries
            interco_lines_vals = []
            
            for branch, values in sorted_branches[1:]:
                branch_account = branch.branch_setting_id.inter_company_account_id
                if not branch_account:
                    raise UserError((
                        "[%s] Account Inter belum diisi dalam Master branch %s - %s"
                    ) % (move.name, branch.code, branch.name))
                    
                balance = values['debit'] - values['credit']
                if balance == 0:
                    continue
                    
                # Create intercompany entries (debit and credit)
                interco_line_vals = {
                    'name': 'Interco %s' % branch.name,
                    'ref': 'Interco %s' % branch.name,
                    'move_id': move.id,
                    'journal_id': move.journal_id.id,
                    'date': move.date,
                    'company_id': branch.id,
                    'division': values['division'],
                    'account_id': main_branch_account.id,
                    'debit': abs(balance) if balance < 0 else 0,
                    'credit': balance if balance > 0 else 0,
                }
                interco_lines_vals.append(interco_line_vals)
                
                counterpart_line_vals = {
                    'name': 'Interco %s' % main_branch.name,
                    'ref': 'Interco %s' % main_branch.name,
                    'move_id': move.id,
                    'journal_id': move.journal_id.id,
                    'date': move.date,
                    'company_id': main_branch.id,
                    'division': values['division'],
                    'account_id': branch_account.id,
                    'debit': balance if balance > 0 else 0,
                    'credit': abs(balance) if balance < 0 else 0,
                }
                interco_lines_vals.append(counterpart_line_vals)
            
            # Create all lines in a single operation
            if interco_lines_vals:
                self.env['account.move.line'].create(interco_lines_vals)
                
        return True

    
    def _get_sequence_format_param(self, previous):
        self.ensure_one()
        format, format_values = super()._get_sequence_format_param(previous)

        branch = self.company_id.code
        prefix1 = format_values['prefix1']
        # Set prefix1 jadi '{journal_code}/{branch}/' 
        format_values['prefix1'] = f"{self.journal_id.code}/{branch}/" if branch else prefix1

        return format, format_values
