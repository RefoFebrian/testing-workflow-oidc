# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
import os
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class MutationRequest(models.Model):
    _name = "tw.mutation.request"
    _description = "Mutation Request"
    
    # 7: defaults methods
    def _get_default_date(self):
        return date.today().strftime("%Y-%m-%d")
    
    def _get_branch_type(self):
        branch_type_ids = []
        branch_type_obj = self.env['tw.selection'].search([
            ('type','=','BranchType'),
            ('value','in',['MD','DL'])
            ])
        if branch_type_obj:
            branch_type_ids = [branch_type.id for branch_type in branch_type_obj]
        return branch_type_ids

    # 8: fields
    name = fields.Char(string='Mutation Request', compute='_compute_name', store=True)
    description = fields.Char(string='Description')
    date = fields.Date(string='Date', default=_get_default_date)
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    amount_total = fields.Float(string='Total', digits='Product Price', compute='_compute_amount', store=True)
    state = fields.Selection([
        ('draft','Draft'),
        ('confirm','Requested'),
        ('open','Open'),
        ('done','Done'),
        ('cancel','Cancelled')
    ], string='State', default='draft')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
    is_picking = fields.Boolean(string='Picking?', compute='_compute_is_picking')
    incoming_picking_count = fields.Integer(string='Incoming Pickings', compute='_compute_incoming_picking_count')
    
    # Audit Trail 
    confirm_date = fields.Datetime(string='Confirmed on')
    confirm_uid = fields.Many2one(comodel_name='res.users', string='Confirmed by')
    done_date = fields.Datetime(string='Done on')
    done_uid = fields.Many2one(comodel_name='res.users', string='Done by')
    cancel_date = fields.Datetime(string='Cancelled on')
    cancel_uid = fields.Many2one(comodel_name='res.users', string='Cancelled by')

    # 9: relation fields
    stock_distribution_id = fields.Many2one('tw.stock.distribution', string='Stock Distribution', readonly=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Branch Requester', default=lambda self: self.env.company)
    branch_sender_id = fields.Many2one(comodel_name='res.partner', string='Branch Sender', check_company=False)
    user_id = fields.Many2one(comodel_name='res.users', string='Responsible', default=lambda self: self.env.uid)
    purchase_order_type_id = fields.Many2one(comodel_name='tw.purchase.order.type', string='Type',domain="[('division', '=', division),('company_id', 'in', [company_id, False])]")
    branch_type_ids = fields.Many2many(
        comodel_name='tw.selection',
        relation='tw_mutation_request_branch_type_rel', column1='mutation_request_id', column2='branch_type_id',
        compute='_compute_branch_type',
        string='Branch Type')
    request_line_ids = fields.One2many(comodel_name='tw.mutation.request.line', inverse_name='request_id', string='Mutation Line')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('company_id')
    def _compute_name(self):
        for record in self:
            branch_obj = record.company_id
            seq_name = self.env['ir.sequence'].with_company(branch_obj).get_sequence_code('MR', branch_obj.code)
            record.name = seq_name
            
    @api.depends('branch_sender_id')
    def _compute_branch_type(self):
        self.branch_type_ids = False
        for record in self:
            record.branch_type_ids = [(6, 0, self._get_branch_type())]
                
    @api.depends('request_line_ids.sub_total')
    def _compute_amount(self):
        self.amount_total = 0
        val_total = 0
        for line in self.request_line_ids :
            val_total += line.sub_total
        self.amount_total = val_total

    def _get_incoming_picking_domain(self):
        self.ensure_one()
        # Use sudo() because distribution and MO might belong to the sender branch
        distribution_ids = self.env['tw.stock.distribution'].sudo().search([
            ('mutation_request_id', '=', self.id)
        ]).ids
        mutation_orders = self.env['tw.mutation.order'].sudo().search([
            ('stock_distribution_id', 'in', distribution_ids)
        ])
        
        mutation_names = mutation_orders.mapped('name')
        group_ids = mutation_orders.mapped('picking_ids.group_id').ids
        
        domain = [('picking_type_code', '=', 'incoming')]
        
        if mutation_names:
            domain += ['|', ('origin', 'in', mutation_names)]
            
        if group_ids:
            domain += [('group_id', 'in', group_ids)]
        else:
            domain += [('id', 'in', [])]
            
        return domain

    def _compute_is_picking(self):
        """Check if there are any incoming pickings linked to this mutation request via MO."""
        for record in self:
            record.is_picking = bool(self.env['stock.picking'].search_count(record._get_incoming_picking_domain()))

    def _compute_incoming_picking_count(self):
        """Count all incoming pickings linked to this mutation request via MO."""
        for record in self:
            record.incoming_picking_count = self.env['stock.picking'].search_count(record._get_incoming_picking_domain())

    @api.onchange('division')
    def _onchange_division(self):
        if self.division :
            self.request_line_ids = False
            
    @api.onchange('start_date','end_date')
    def _onchange_date(self):
        if self.start_date and self.end_date :
            if self.start_date > self.end_date :
                self.start_date = self.end_date = False
                return {'warning':{'title':'Perhatian !','message':'Start Date tidak boleh melebihi End Date.'}}
            
    @api.onchange('purchase_order_type_id')
    def _onchange_purchase_order_type_id(self):
        self.start_date = False
        self.end_date = False
        if self.purchase_order_type_id:
            self.start_date = self.purchase_order_type_id.get_date(self.purchase_order_type_id.start_date_id.value)
            self.end_date = self.start_date + relativedelta(days=30)
            
    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('request_line_ids'):
                raise Warning("Tidak bisa disimpan!, Silahkan isi detail mutasi terlebih dahulu")
        return super(MutationRequest, self).create(vals_list)

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise Warning(f'Invalid action! Cannot delete a Mutation Request which is in state {record.state}!')
        return super(MutationRequest, self).unlink()
    
    # 13: action methods
    def action_cancel(self):
        distribution_obj = self.env['tw.stock.distribution'].search([('mutation_request_id','=',self.id)])
        for distribution in distribution_obj:
            distribution.write({'state': 'cancel'})
            
        self.write({
            'state': 'cancel',
            'cancel_uid':self._uid,
            'cancel_date':datetime.now()
            })
        
    def action_confirm_order(self):
        self._check_valid_request()
        self.action_distribution_create()
        self.write({'state': 'confirm'})
        
    def action_distribution_create(self):
        branch_sender_obj = self.env['res.company'].sudo().search([('partner_id', '=', self.branch_sender_id.id)])
        distribution_vals = {
            'origin': self.name,
            'company_id': branch_sender_obj.id,
            'requester_id': self.company_id.partner_id.id,
            'division' : self.division,
            'mutation_request_id': self.id,
            'purchase_order_type_id': self.purchase_order_type_id.id,
            'date': self.date,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'description': self.description,
            'state': 'draft',
        }
        distribution_id = self.env['tw.stock.distribution'].sudo().create(distribution_vals)
        self.stock_distribution_id = distribution_id
        for line in self.request_line_ids :
            distribution_line_vals = {
                'stock_distribution_id': distribution_id.id,
                'product_id': line.product_id.id,
                'description': line.description,
                'requested_qty': line.requested_qty,
                'approved_qty': line.requested_qty,
                'qty': 0,
                'supply_qty': 0,
                'price': line.price,
            }
            self.env['tw.stock.distribution.line'].sudo().create(distribution_line_vals)
            
    def action_view_picking(self):
        """Legacy header button: open incoming pickings linked to this mutation request."""
        return self.action_view_incoming_picking()

    def action_view_incoming_picking(self):
        """Smart button action: open list/form of incoming pickings from MO linked to this request."""
        self.ensure_one()
        picking_ids = self.env['stock.picking'].search(self._get_incoming_picking_domain()).ids

        if not picking_ids:
            raise Warning(_("Perhatian! Tidak ditemukan incoming picking untuk Mutation Request '%s'.") % self.name)

        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        action['domain'] = [('id', 'in', picking_ids)]
        action['context'] = {}
        return action

    def action_view_stock_distribution(self):
        self.ensure_one()
        if not self.stock_distribution_id:
            raise Warning(f"Tidak ditemukan Stock Distribution untuk Mutation Request '{self.name}'")
        
        return {
            'name': 'Stock Distribution',
            'type': 'ir.actions.act_window',
            'res_model': 'tw.stock.distribution',
            'view_mode': 'form',
            'res_id': self.stock_distribution_id.id,
            'target': 'current',
        }
            
    # 14: private methods
    def action_done(self):
        """Mark Mutation Request as done.
        
        This method can be inherited by other modules to add additional 
        actions when the mutation request is completed.
        """
        self.suspend_security().write({
            'state': 'done',
            'done_uid': self.env.uid,
            'done_date': datetime.now(),
        })

    def button_dummy(self):
        return True

    def _check_valid_request(self):
        for mutation in self:
            if not mutation.request_line_ids:
                raise Warning("Perhatian!\nTab Mutation Request Line tidak boleh kosong!")
            if mutation.branch_sender_id.id == mutation.company_id.partner_id.id:
                raise Warning(f"Gagal Validasi! Branch Sender tidak boleh sama dengan Company")
            if len(mutation.request_line_ids) != len(mutation.request_line_ids.mapped('product_id')):
                raise Warning(f"Gagal Validasi! Terdapat duplikasi produk pada Mutation Request '{mutation.name}'")
            for line in mutation.request_line_ids:
                if line.requested_qty <= 0:
                    raise Warning(f"Gagal Validasi! Jumlah mutasi harus lebih dari 0 pada Mutation Request '{mutation.name}'")
            
            