# -*- coding: utf-8 -*-

# 1: imports of python lib
from openupgradelib.openupgrade import UserError
from datetime import date, datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command
from odoo.tools import SQL

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning, ValidationError

# 5: local imports

# 6: Import of unknown third party lib


import logging

_logger = logging.getLogger(__name__)

class TWDealerSPK(models.Model):
    _name = "tw.dealer.spk"
    _description = "SPK Dealer"

    # 7: defaults methods
    def _get_default_branch(self):
        return self.env.user.company_ids[0].id if self.env.user.company_ids else False
        
    def _get_default_date(self):
        return date.today()
    
    def _get_default_datetime(self):
        return datetime.now()
    
    def _get_state_value(self):
        # Mengambil value yang sesuai dengan key di state
        selection = self._fields.get('state') and self._fields['state'].selection
        return dict(selection).get(self.state, self.state) if selection else self.state
        
    # 8: fields
    name = fields.Char(string='SPK', compute='_compute_name', store=True)
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options(), default='Unit')
    date_order = fields.Date(string='Date Order', default=_get_default_date, readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('progress', 'SPK'),
        ('so', 'Sales Order'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft')
    delivery_address = fields.Text(string='Delivery Address', help='Address for delivery of the vehicle')
    identification_number = fields.Char(string="No KTP", compute='_compute_identification_number', store=True)
    lead_reference = fields.Char(string='Lead Reference', help="Reference to the Lead associated with this SPK.")
    payment_type = fields.Char(compute='_compute_payment_type')
    reason_cancel = fields.Text(string='Reason Cancel')
    dso_count = fields.Integer(compute='_compute_dso_count')
    # dealer_sale_order_id = fields.Integer()
    
    # identification_number = fields.Char(related="partner_id.identification_number", string="No KTP")
    # is_mandatory_spk = fields.Boolean(related="company_id.is_mandatory_spk",string="Mandatory SPK")

    # 9: relation fields
    company_id = fields.Many2one(comodel_name='res.company', string='Branch', required=True, default=_get_default_branch)
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer', check_company=True, index=True,
                                 help="You can find a partner by its Name, TIN, Email or Internal Reference.")
    finco_id = fields.Many2one(comodel_name='res.partner', string='Finco', domain="[('category_id.name', '=', 'Finance Company')]", help='')
    sales_id = fields.Many2one(comodel_name='hr.employee', string='Sales Person', domain="[('company_id', '=', company_id)]")
    sales_coordinator_id = fields.Many2one(comodel_name='hr.employee', string='Sales Coordinator',
                                           compute='_compute_sales_coordinator_id', store=True,
                                           domain="[('company_id', '=', company_id), ('job_id.sales_force_id.value', '=', 'sales_coordinator')]")
    payment_term_id = fields.Many2one(comodel_name='account.payment.term', string='Payment Term', compute='_compute_payment_term_id', store=True)
    payment_type_id = fields.Many2one(comodel_name='tw.selection', string='Tipe Pembayaran', domain="[('type', '=', 'PaymentType')]")
    dealer_sale_order_id = fields.Many2one(comodel_name='tw.dealer.sale.order', string='Dealer Sale Order', copy=False)
    line_ids = fields.One2many(comodel_name='tw.dealer.spk.line', inverse_name='spk_id', string='SPK Detail')
    lead_id = fields.Many2one(comodel_name='tw.lead', string='Lead')
    product_category_ids = fields.Many2many(
        comodel_name='product.category',
        relation='tw_dealer_sale_order_prod_categ_rel', column1='order_id', column2='product_category_id',
        compute='_compute_product_category_ids',
        string="Product Category")      
    
    # 9.1 Audit Trails
    cancel_date = fields.Datetime(string='Cancelled on', store=True)
    cancel_uid = fields.Many2one(comodel_name='res.users', string="Cancelled by", store=True)
    confirm_date = fields.Datetime(string='Confirmed on', store=True)
    confirm_uid = fields.Many2one(comodel_name='res.users', string="Confirmed by", store=True)
    sale_order_date = fields.Date(string='Sale Order on', store=True)
    sale_order_uid = fields.Many2one(comodel_name='res.users', string="Sale Order by", store=True)
    
    # 10: constraints & sql constraints
    @api.constrains('sales_id', 'sales_coordinator_id')
    def _check_sales_coordinator(self):
        for order in self:
            if order.sales_id and order.sales_coordinator_id:
                if order.sales_id.job_id.sales_force_id.value not in ('sales_coordinator', 'sales_operation_head', 'area_manager'):
                    if order.sales_id.coach_id != order.sales_coordinator_id and order.sales_id.parent_id != order.sales_coordinator_id:
                        raise ValidationError("Sales Coordinator yang dipilih harus Coach atau Manager dari Sales Person.")

    @api.constrains('line_ids')
    def _check_empty_lines(self):
        for order in self:
            if not order.line_ids:
                raise ValidationError("SPK lines tidak boleh kosong. Silahkan hapus baris yang kosong atau isi semua field yang diperlukan sebelum menyimpan SPK.")

    # 11: compute/depends & on change methods
    @api.depends('company_id')
    def _compute_name(self):
        for spk in self:
            if spk.id:
                code = 'SPK'
                prefix = spk.company_id.code
                spk.name = spk.env['ir.sequence'].get_sequence_code(code, prefix)

    @api.depends('payment_type_id')
    def _compute_payment_type(self):
        for spk in self:
            spk.payment_type = spk.payment_type_id.name
                
    def _compute_dso_count(self):
        for spk in self:
            spk.dso_count = spk.env['tw.dealer.sale.order'].search_count([('spk_id', '=', spk.id)])

    @api.depends('division')
    def _compute_product_category_ids(self):
        for order in self:
            if order.division:
                order.product_category_ids = [(6, 0, self.env['product.category'].get_child_ids(order.division))]
            else:
                order.product_category_ids = False

    @api.depends('sales_id')
    def _compute_sales_coordinator_id(self):
        for order in self:
            if order.sales_id:
                if order.sales_id.job_id.sales_force_id.value in ('sales_coordinator', 'sales_operation_head'):
                    order.sales_coordinator_id = order.sales_id.id
                else:
                    if not order.sales_id.coach_id:
                        raise Warning("Sales yang dipilih tidak memiliki Coach / Koordinator!")
                    order.sales_coordinator_id = order.sales_id.coach_id.id
    
    @api.depends('partner_id', 'finco_id')
    def _compute_payment_term_id(self):
        for record in self:
            record = record.with_company(record.company_id)
            if record.finco_id:
                record.payment_term_id = record.finco_id.property_payment_term_id.id
            elif record.partner_id:
                record.payment_term_id = record.partner_id.property_payment_term_id.id

    @api.depends('partner_id')
    def _compute_identification_number(self):
        for record in self:
            record.identification_number = record.partner_id.identification_number

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['date_order'] = self._get_default_date()
            # dealer_spks = super().create(vals)
            # update_reg = self.env['dealer.register.spk.line'].search([('id','=',vals['register_spk_id'])])
            # update_reg.write({'spk_id':dealer_spks.id,'state':'spk'})
        return super().create(vals_list)
    
    def write(self, vals):
        #print self.register_spk_id,"ids<<<<"
        # if values.get('register_spk_id', False):
        #     self.register_spk_id.write({'spk_id':False,'state':'open'})
        #     new_reg = self.env['dealer.register.spk.line'].search([('id','=',values.get('register_spk_id',False))])
        #     update_reg_baru = new_reg.write({'spk_id':self.id,'state':'spk'})
        return super().write(vals)

    def unlink(self):
        for item in self:
            if item.state != 'draft':
                raise Warning("Dealer SPK sudah diproses, data tidak dapat dihapus!")
        return super().unlink()
    
       
    # 13: action methods
    def action_spk_list(self):
        emp = self.env['hr.employee'].suspend_security().search([('user_id', '=', self.env.uid)], limit=1)
        areas_ids = self.env.user.company_ids.ids
        if emp.job_id.is_sales_digital:
            sales_digital_ids = self._get_sales_digital_user()
            domain = [('sales_id', 'in', sales_digital_ids), ('company_id', 'in', areas_ids)]
        else:
            domain = [('company_id', 'in', areas_ids)]
        
        list_id = self.env.ref('tw_spk.tw_dealer_spk_list_view').id
        form_id = self.env.ref('tw_spk.tw_dealer_spk_form_view').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'SPK',
            'path': 'dealer-spk',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.dealer.spk',
            'domain': domain,
            'views': [(list_id, 'list'), (form_id, 'form')],
            'context': {
                'search_default_state_draft': 1,
                'search_default_state_spk': 1,
                'readonly_by_pass': True
            }
        }

    def action_create_so(self):
        if self.state not in ('progress','so'):
            raise ValidationError(f'Silakan refresh halaman ini, karena state sudah {self._get_state_value()}')
        if self.dealer_sale_order_id:
            if self.dealer_sale_order_id.state != 'cancel':
                raise ValidationError('SPK masih memiliki SO yang belum cancel. Periksa kembali %s' % self.dealer_sale_order_id.name)
        sale_order = self.sudo()._prepare_dealer_sale_order_vals()
        create_so = self.env['tw.dealer.sale.order'].suspend_security().create(sale_order)
        
        self.suspend_security().write({
            'state': 'so',
            'sale_order_uid': self.env.uid,
            'sale_order_date': self._get_default_datetime(),
            'dealer_sale_order_id': create_so.id,
        })
        return True
    
    def action_view_so(self):
        if not self.env.user.has_group('tw_dealer_sale_order.group_tw_dealer_sale_order_read'):
            raise ValidationError('Anda tidak memiliki akses ke form DSO')

        action = {
            'name': 'Dealer Sale Order',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tw.dealer.sale.order',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': self.dealer_sale_order_id.id
        }
        # Check if dealer_sale_order_id exists and is accessible
        if self.dealer_sale_order_id and self.dealer_sale_order_id._name != '_unknown':
            action['res_id'] = self.dealer_sale_order_id.id
        else:
            # Fallback to searching for related orders
            orders = self.env['tw.dealer.sale.order'].search([('spk_id', '=', self.id)])
            if orders:
                if len(orders) == 1:
                    action['res_id'] = orders.id
                else:
                    action.update({
                        'view_mode': 'tree,form',
                        'domain': [('id', 'in', orders.ids)],
                        'views': [(False, 'tree'), (False, 'form')],
                    })
            else:
                raise Warning("Tidak ada Dealer Sale Order yang terhubung dengan SPK ini.\nSilahkan cek kembali SPK yang sudah di proses.")
        
        return action
    
    def action_confirm_spk(self):
        if self.state != 'draft':
            raise ValidationError(f'Silakan refresh halaman ini, karena state sudah {self._get_state_value()}')
        self.write({
            'confirm_date': self._get_default_datetime(),
            'confirm_uid': self.env.uid,
            'state': 'progress',
            'date_order': self._get_default_date()
        })
        return True
    
    def action_cancel_spk_wizard(self):
        return {
            'name': 'Cancel SPK',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tw.dealer.spk.cancel.reason',
            'views': [(self.env.ref('tw_spk.tw_dealer_spk_cancel_reason_view').id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': { 'default_spk_id': self.id }
        }
    
    def action_state_draft(self):
        if self.state == 'cancelled':
            raise ValidationError(f'SPK sudah {self._get_state_value()}.\nSilakan kembali ke buku tamu')
        self.write({
            'state': 'draft'
        })
        
    def action_cancel(self, reason):
        if self.dealer_sale_order_id:
            if self.dealer_sale_order_id.state != 'cancel':
                raise ValidationError('SPK masih memiliki Sale Order yang belum dibatalkan. Silakan cancel SO dengan nomor %s' % self.dealer_sale_order_id.name)
        if self.state == 'cancelled':
            raise ValidationError(f'Silakan refresh halaman ini, karena state sudah {self._get_state_value()}')
        self.write({
            'reason_cancel': reason,
            'cancel_date': date.today(),
            'cancel_uid': self.env.uid,
            'state': 'cancelled'
        })
        lead = self.env['tw.lead'].search([('spk_id', '=', self.id)])
        if not lead:
            raise ValidationError('Tidak ada buku tamu yang terhubung ke SPK ini')
        else:
            # update state lead to open if spk is cancelled
            lead.write({
                'state': 'open',
                'log_ids': [Command.create({
                    'name': 'SPK canceled, reverting Lead to Open',
                    'date': datetime.now(),
                    'category_id': self.env.ref('tw_lead.tw_lead_log_category_type_general').id
                })]
            })
            
    # 14: private methods
    def _get_sales_digital_user(self, branch=[]):
        if not branch:
            branch = self.env['res.company'].search([('parent_id', '!=', False)]).ids

        self.env.cr.execute(SQL("""
            SELECT e.id
            FROM resource_resource r 
            INNER JOIN hr_employee e ON r.id = e.resource_id
            INNER JOIN hr_job j ON e.job_id = j.id
            INNER JOIN res_users u ON r.user_id = u.id 
            WHERE 1 = 1
            -- AND (e.tgl_keluar IS NULL OR e.tgl_keluar > NOW())
            AND u.active = true
            AND r.active = true
            AND j.is_sales_digital = true
            AND e.company_id IN %(company_id)s
        """, company_id=tuple(branch)))
        
        res = self.env.cr.fetchall()
        return [r[0] for r in res] if res else []
    
    def _prepare_dealer_sale_order_vals(self):
        lead_obj = self.lead_id
        so = {
            'company_id': self.company_id.id,
            'division': self.division,
            'date_order': self._get_default_datetime(),
            'partner_id': self.partner_id.id,
            'sales_id': self.sales_id.id,
            'sales_coordinator_id': self.sales_coordinator_id.id,
            'finco_id': self.finco_id.id,
            'spk_id': self.id,
            'payment_type_id': lead_obj.payment_type_id.id,
        }
            
        sale_order_line = []
        for line in self.line_ids:
            sale_order_line.append(Command.create(line._prepare_dealer_sale_order_line_vals()))
        so['order_line'] = sale_order_line
        return so
            
    def _get_location_id_branch(self, product_id, company_id):
        # TODO: use get_stock_available(product_id, company_id, usage='internal', location_id=False, lot_state='stock', include_reserved=False)
        #       from stock.quant

        quantity = self.env['stock.quant'].get_stock_available(self.product_id.id, self.company_id.id)

        try:
            lot_id = self.env['stock.lot'].search([('product_id', '=', product_id),
                                                   ('state', '=', 'stock'),
                                                   ('company_id', '=', company_id),
                                                   ('location_id.usage', '=', 'internal')])
            lot_ids = []
            for lot in lot_id:
                lot_ids.append(lot.id)

            quant_id = self.env['stock.quant'].search([('lot_id', 'in', lot_ids),
                                                       ('reservation_ids', '=', False)])
            if quant_id:
                return quant_id[0].lot_id
            else:
                _logger.error(f"No stock found for product {product_id}, branch {company_id}\n")
                return False
        except Exception as e:
            _logger.error(f"No stock found for product {e}: {product_id},{company_id},{quant_id}\n")
    
    def _get_pricelist_sales(self):
        self.ensure_one()
        if self.company_id.branch_setting_id:
            pricelist = self.company_id.branch_setting_id.pricelist_sale_unit_id
        elif self.company_id:
            product_pricelist = self.env['product.pricelist']
            pricelist = product_pricelist.search([('company_id', '=', self.company_id.id),
                                                  ('type', '=', 'sales')], limit=1)
        else:
            raise Warning("Tidak ada pricelist yang ditemukan untuk cabang. Silahkan atur pricelist yang valid.")

        return pricelist
    
    def _get_pricelist_sales_bbn(self, plate):
        self.ensure_one()
        branch = self.company_id
        return self.env['product.pricelist']._get_bbn_sales_pricelist(branch, plate)

    def _get_price_unit(self, product_id, product_qty):
        pricelist = self._get_pricelist_sales()
        return pricelist.with_context(self.company_id)._get_product_price(product_id, product_qty)
