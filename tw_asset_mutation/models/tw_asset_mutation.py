# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwAssetMutation(models.Model):
    _name = "tw.asset.mutation"
    _description = "Asset Mutation"
    _order = "date DESC"

    # 7: defaults methods
    def _get_default_date(self):
        return date.today()

    # 8: fields
    name = fields.Char(string="Name", readonly=True, default='New', copy=False, index=True, compute='_compute_name', store=True)
    date = fields.Date('Date',default=_get_default_date)
    division = fields.Selection([('Umum','Umum')],default='Umum',readonly=True)
    state = fields.Selection([
        ('draft','Draft'),
        ('open','Open'),
        ('done','Done')],default='draft')
    
    # Audit Trail
    confirm_date = fields.Datetime('Confirmed on',default=fields.Datetime.now)
    confirm_uid = fields.Many2one('res.users',string="Confirmed by")


    # 9: relation fields
    company_id = fields.Many2one('res.company','Branch Sender')
    company_request_id = fields.Many2one('res.company', string='Branch Request',default=lambda self: self.env.user.company_id)
    detail_ids = fields.One2many('tw.asset.mutation.line','mutation_id')
    approval_ids = fields.One2many('tw.approval.line','transaction_id',string="Table Approval",domain=[('model_id','=',_name)])
    distribution_asset_id = fields.Many2one('tw.asset.distribution','Distribution Asset')
    distribution_count = fields.Integer(string='Distribution Count', compute='_compute_distribution_count')
    pic_asset_id = fields.Many2one('hr.employee','PIC Asset',domain="[('company_id','=',company_id),('job_id.name','!=','SALESMAN PARTNER')]")

    # 10: constraints & sql constraints
    @api.constrains('detail_ids')
    def _check_detail_ids(self):
        if len(self.detail_ids) <= 0:
            raise Warning("Detail Asset tidak boleh kosong!")
        err_msg = ""
        # Validasi ini harusnya ada di peminjaman asset
        # for x in self.detail_ids:
        #     if x.asset_id.sudo().lend_id:
        #         err_msg += "Aset [%s] - [%s] %s sedang dipinjam di %s\n" % (x.asset_id.sudo().name, x.asset_id.sudo().code, x.asset_id.sudo().name, x.asset_id.sudo().lend_id.name)
        if err_msg:
            raise Warning(err_msg)

    # 11: compute/depends & on change methods
    def _compute_distribution_count(self):
        for rec in self:
            rec.distribution_count = 1 if rec.distribution_asset_id else 0

    @api.depends('company_id')
    def _compute_name(self):
        for rec in self: 
            if not rec.name or rec.name == 'New':
                if rec.company_id:
                    rec.name = self.env['ir.sequence'].get_sequence_code('MRA', rec.company_id.code)
    
    @api.onchange('company_request_id')
    def onchange_company_request_id(self):
        self.detail_ids = False
        

    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list):
        return super(TwAssetMutation,self).create(vals_list)


    def unlink(self):
        for me in self:
            if me.state != 'draft':
                raise Warning("Data selain draft tidak bisa dihapus !")
        return super(TwAssetMutation, self).unlink()

    # 13: action methods
    def action_confirm(self):        
        # Create Mutasi Asset
        detail_ids = []
        for detail in self.detail_ids:
            if not detail.location_asset_id:
                raise Warning("Lokasi Asset tidak boleh kosong!")
            amount = detail.asset_id.real_purchase_value
            amount_depreciated = detail.asset_id.value - (detail.asset_id.salvage_value + detail.asset_id.value_residual)
            book_value = detail.asset_id.value_residual

            detail_ids.append([0,False,{
                'asset_id':detail.asset_id.id,
                'code':detail.asset_id.code,
                'category_id':detail.asset_id.category_id.id,
                'amount':amount,
                'amount_depreciated':amount_depreciated,
                'book_value':book_value,
                'note':detail.note,
            }])
            
            # Update employee_user_id if new user is specified on this line
            if detail.new_employee_user_id:
                detail.asset_id.write({'employee_user_id': detail.new_employee_user_id.id})

        vals = {
            'company_id':self.company_request_id.id,
            'company_sender_id':self.company_id.id,
            'mutation_request_id':self.id,
            'division':self.division,
            'detail_ids':detail_ids,
        }
        mutation_obj = self.env['tw.asset.distribution'].suspend_security().create(vals)
        
        self.write({
            'state':'open',
            'distribution_asset_id':mutation_obj.id,
            'confirm_uid':self._uid,
            'confirm_date':self._get_default_date()
        })


    # 14: private methods
    def action_view_distribution(self):
        """Smart button action to open the related Asset Distribution."""
        self.ensure_one()
        if not self.distribution_asset_id:
            return {'type': 'ir.actions.act_window_close'}
        return {
            'type': 'ir.actions.act_window',
            'name': 'Asset Distribution',
            'res_model': 'tw.asset.distribution',
            'view_mode': 'form',
            'res_id': self.distribution_asset_id.id,
        }



    
