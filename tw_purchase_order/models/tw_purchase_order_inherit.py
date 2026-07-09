# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date 

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError, UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwPurchaseOrder(models.Model):
    _inherit = "purchase.order"

    # 7: defaults methods
    def get_default_datetime(self):
        return datetime.now()
    
    def _get_default_branch(self):
        if self.env.company.parent_id:
            return self.env.company.id
        else:
            company_ids = self.env.companies.filtered(lambda x: x.parent_id)
            if company_ids:
                return company_ids[0].id

        raise Warning(_('Please choose another branch / company other than %s on the top right of the screen.'%self.env.company.name))
    
    # 8: fields
    date = fields.Date('Date', required=True, default=date.today())
    start_date = fields.Date(string="Start Date", default=date.today(), copy=False)
    end_date = fields.Date(string="End Date", copy=False)
    is_invisible_button = fields.Boolean(default=False,compute='_compute_is_invisible_button')
    is_need_approval = fields.Boolean(compute="_compute_is_need_approval", store=False)
    is_blank_po = fields.Boolean(string="Is Blank PO", default=False, help="Checklist untuk PO Urgent NRFS atau PO Rekomendasi AHM, jika ingin create PO tanpa detail item")
    
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
    
    # Audit Trail
    rfq_uid = fields.Many2one('res.users',string="Waiting For Purchase by")
    rfq_date = fields.Datetime('Waiting For Purchase on')

    # 9: relation fields
    company_id = fields.Many2one('res.company', 'Branch', required=True, index=True, default=_get_default_branch, domain="[('parent_id', '!=', False)]")
    location_id = fields.Many2one('stock.location', string='Location', domain="[('usage', '=', 'supplier')]")
    purchase_order_type_id = fields.Many2one(comodel_name='tw.purchase.order.type', string="PO Type", domain="[('division', '=', division),('company_id', 'in', [company_id, False])]")
    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To', required=True, domain="['|', ('warehouse_id', '=', False), ('warehouse_id.company_id', '=', company_id), '|', ('division', '=', division), ('division', '=', False)]", help="This will determine operation type of incoming shipment")
    
    product_category_ids = fields.Many2many(comodel_name="product.category", string="Product Category", compute='_compute_product_category_ids',store=True)

    # 10: constraints & sql constraints

    @api.constrains('order_line')
    def _check_empty_lines(self):
        for order in self:
            if not self.is_blank_po and not order.order_line:
                raise ValidationError(_("Empty order lines are not allowed. Please remove any blank lines or fill in all required fields before saving this Purchase Order."))

    @api.constrains('order_line')
    def _check_duplicate_product(self):
        """Prevent duplicate products in purchase order lines."""
        for order in self:
            product_lines = order.order_line.filtered(lambda l: l.product_id and not l.display_type)
            product_ids = [line.product_id.id for line in product_lines]
            if len(product_ids) != len(set(product_ids)):
                # Find duplicate product names for better error message
                seen = set()
                duplicates = []
                for line in product_lines:
                    if line.product_id.id in seen:
                        duplicates.append(line.product_id.display_name)
                    seen.add(line.product_id.id)
                raise ValidationError(_(
                    "Duplicate products are not allowed in Purchase Order.\n"
                    "Duplicate product(s): %s\n"
                    "Please consolidate quantities for the same product into a single line."
                ) % ', '.join(set(duplicates)))
                
    @api.onchange('company_id')
    def onchange_company_id(self):
        """Ganti juga company nya saat branch nya berubah, supaya 1 banding 1
        """
        if self.company_id:
            self.company_id = self.company_id.id
            self.partner_id = self.company_id.default_supplier_id
        else:
            self.company_id = self.env.context.get('company_id') or self.env.company.id
    
    @api.onchange('company_id')
    def _onchange_company_id(self):
        if not self.company_id:
            raise Warning(_('Please choose another branch / company other than %s.'%self.env.company.name))
        super()._onchange_company_id()
        
    # 11: compute/depends & on change methods
    def _compute_name(self):
        for record in self:
            if record.date_order and record.name == 'New Record':
                seq_name = self.env['ir.sequence'].with_company(record.company_id).get_sequence_code('PO', record.company_id.code)
                record.name = seq_name
    
    @api.depends('division')
    def _compute_product_category_ids(self):
        for order in self:
            if order.division:
                product_category_ids = self.env['product.category'].get_child_ids(order.division)
                order.product_category_ids = [(6, 0, product_category_ids)]

    @api.onchange('company_id', 'division')
    def _onchange_branch_division(self):
        self.picking_type_id = False
        stock_picking_type = self.env['stock.picking.type']
        if self.company_id and self.division:
            picking_type = stock_picking_type.get_picking_type('incoming', self.company_id.id, self.division)
            self.picking_type_id = picking_type.id

    @api.onchange('purchase_order_type_id')
    def _onchange_periode(self):
        for order in self:
            if order.purchase_order_type_id:
                start_date = order.purchase_order_type_id.get_date(order.purchase_order_type_id.start_date_id.value)
                end_date = order.purchase_order_type_id.get_date(order.purchase_order_type_id.end_date_id.value)
                order.start_date = start_date
                order.end_date = end_date

    @api.onchange('is_blank_po', 'partner_id')
    def _onchange_is_blank_po(self):
        md_code = self.env['res.company'].get_default_main_dealer_code()
        ahm_code = self.env['res.company'].get_default_main_dealer().default_supplier_id.code
        if self.is_blank_po and self.division == 'Sparepart' and (self.company_id.code != md_code or self.partner_id.code != ahm_code):
            return {
                    'value': {
                        'is_blank_po': False,
                    },
                    'warning': {
                        'title': _("Warning"),
                        'message': _(f"Untuk PO Sparepart Selain Branch {md_code} dan vendor {ahm_code} tidak bisa create PO tanpa detail item."),
                    }
                }
    
    @api.depends('division','state')
    def _compute_is_invisible_button(self):
        # * Invisible button method
        for order in self:
            order.is_invisible_button = False

    @api.depends('division','company_id')
    def _compute_is_need_approval(self):
        for rec in self:
            rec.is_need_approval = False

            if rec.division not in ['Unit','Sparepart']:
                continue

            branch_setting = self.env['tw.branch.setting'].suspend_security().search(
                [('company_id','=',rec.company_id.id)],
                limit=1
            )

            if branch_setting and branch_setting.is_po_need_approval:
                rec.is_need_approval = True
            

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('order_line') and not vals.get('is_blank_po'):
                raise Warning(_('Warning! \nCannot create purchase order without any order line!'))
            
            # Give sequence name
            company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
            branch_obj = self.env['res.company'].browse(company_id)
            if vals.get('name', 'New') == 'New':
                seq_name = self.with_company(company_id).env['ir.sequence'].get_sequence_code('PO', branch_obj.code)
                vals['name'] = seq_name 
                
        return super().create(vals_list)
    
    def unlink(self):
        for record in self:
            # if record.state and record.state != 'draft':
            #     raise Warning(_('Warning! \nCannot delete records with a state other than draft!'))
            record.button_cancel()

        return super().unlink()
    
    def get_formview_action(self, access_uid=None):
        """ Override this method in order to redirect many2one towards the right model depending on access_uid """
        user = self.env.user
        if access_uid:
            user = self.env['res.users'].browse(access_uid).sudo()
        if not user.has_group('tw_purchase_order.group_tw_purchase_order_form_read'):
            raise UserError(_("You do not have access to this document."))
            
        res = super().get_formview_action(access_uid=access_uid)
        return res
      
    # 13: action methods
    def action_view_invoice(self, invoices=False):
        # if invoices:
            #? Auto Post invoice. We dont want user to be able to edit all data on the invoice
            #? Consider changing this method to action_confirm() so it will be "open invoice" instead of "posted invoice" 
            # invoices.action_post()
        
        action = super().action_view_invoice(invoices)
        return action
    
    def action_create_invoice(self):
        create_invoice = super().action_create_invoice()
        created_invoice = create_invoice.get('res_id')
        if created_invoice:
            invoice = self.env['account.move'].sudo().browse(created_invoice)
            invoice.sudo().action_open()
        return create_invoice
    
    def print_quotation(self):
        self._check_valid_po()
        super().print_quotation()
    
    def button_confirm(self):
        if self.is_blank_po:
            self.state = 'confirmed'
            return True

        self._check_valid_po()
        res = super(TwPurchaseOrder, self).button_confirm()
        md_code = self.env['res.company'].get_default_main_dealer_code()
        if self.partner_id.code != md_code and 'Principle' in self.partner_id.category_id.mapped('name') and 'Branch' not in self.partner_id.category_id.mapped('name'):
            self.order_line.move_ids.write({'quantity': 0})
        for line in self.order_line:
            line.original_price_unit = line.price_unit
        return res

    def action_purchase_order_list(self, type):
        action = self._get_actions_act_window()
        if type == 'Showroom':
            action['search_view_id'] = self.env.ref('tw_purchase_order.tw_inherit_purchase_order_search_view').id
            action['domain'] = [('division', '=', 'Unit')]
            action['context'] = {
                'view_type': 'form',
                'default_division': 'Unit',
                'default_po_type': 'showroom',
                'search_default_outstanding':True,
            }
            
        elif type == 'Workshop':
            action['search_view_id'] = self.env.ref('tw_purchase_order.tw_inherit_purchase_order_search_view').id
            action['domain'] = [('division', '=', 'Sparepart')]
            action['context'] = {
                'view_type': 'form',
                'default_division': 'Sparepart',
                'default_po_type': 'workshop',
                'search_default_outstanding':True,
            }

        elif type == 'Umum':
            action['search_view_id'] = self.env.ref('tw_purchase_order.tw_inherit_purchase_order_search_view').id
            action['domain'] = [('division', '=', 'Umum')]
            action['context'] = {
                'view_type': 'form',
                'default_division': 'Umum',
                'default_po_type': 'general',
                'search_default_outstanding':True,
            }

        elif type == 'General':
            action['search_view_id'] = self.env.ref('tw_purchase_order.tw_inherit_purchase_order_search_view').id
            action['domain'] = [('division', 'in', ['Umum', 'Extras', 'Finance'])]
            action['context'] = {
                'view_type': 'form',
                'default_division': 'Umum',
                'default_po_type': 'general',
                'search_default_outstanding':True,
            }

        return action

    def button_cancel(self):
        if self.state == 'cancel':
            raise UserError(f'Silakan refresh halaman ini, karena state sudah {self._get_state_value()}')
        
        self.write({'state': 'cancel', 'mail_reminder_confirmed': False})

    # 14: private methods
    def _check_valid_po(self):
        for order in self:
            if order.picking_type_id.division and order.picking_type_id.division != order.division:
                raise Warning('Division in Picking Type (%s) must be the same as Division in Purchase Order (%s)' % (order.picking_type_id.division, order.division))

            if not order.order_line:
                raise Warning('You cannot confirm a purchase order without any purchase order lines.')
                
            for line in order.order_line:
                line._verify_costing_method()
                if line.product_qty <= 0:
                    raise Warning('You cannot confirm a purchase order with a product quantity of 0 or less.')
                if line.price_unit < 1:
                    raise Warning("Unit Price Product '%s' tidak boleh '%s'" % (line.product_id.name, line.price_unit))

            
    def _get_actions_act_window(self):
        list_view = self.env.ref('tw_purchase_order.tw_purchase_order_list_view')
        form_view = self.env.ref('purchase.purchase_order_form')
        search_view = self.env.ref('tw_purchase_order.tw_inherit_purchase_order_search_view')

        return {
            'name': _("Purchase Order"),
            'view_mode': 'list,form',
            'views' : [(list_view.id, 'list'), (form_view.id, 'form')],
            'search_view_id' : search_view.id,
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
    
    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        journal_id = self.env['tw.account.setting'].suspend_security()._get_purchase_journal_id(self.company_id.id, self.division)
        if not journal_id:
            raise Warning(_("Journal Purchase not found for division %s in Branch %s, please set journal in branch setting!"%(self.division, self.company_id.name)))

        invoice_vals.update({
            'company_id': self.company_id.id,
            'division': self.division,
            'ref': self.name,
            'invoice_date': self.get_default_datetime().date(),
            'journal_id': journal_id,
            # TODO: Please fix this. Error when not installing approval
            # 'invoice_date': self.date_approve.date(),
        })
        return invoice_vals

    def _prepare_picking(self):
        vals_picking = super()._prepare_picking()
        
        if self.company_id or self.division:
            vals_picking.update({
                'company_id': self.company_id.id,
                'company_id': self.company_id.id,
                'division': self.division
            })
        return vals_picking
    
    def _obtain_product_category_ids(self, division):
        product_category = self.env['product.category']
        parent_category = product_category.search([('name', '=', division.name)])
        prod_categ = product_category.search([('parent_id', 'child_of', parent_category.ids)])
        return prod_categ.ids
    
    @api.model
    def _get_picking_type(self, company_id):
        picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)])
        if not picking_type:
            picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming'), ('warehouse_id', '=', False)])
        company_warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_id)], limit=1)
        if not company_warehouse:
            self.env['stock.warehouse'].with_company(self.company_id)._warehouse_redirect_warning()
        return picking_type[:1]
    
    def _get_action_view_picking(self, pickings):
        result = super()._get_action_view_picking(pickings)
        context = result.get('context', {})
        context['default_division'] = self.division
        context['default_company_id'] = self.company_id.id
        context['group_by'] = ['picking_type_id']
        result['context'] = context
        return result
