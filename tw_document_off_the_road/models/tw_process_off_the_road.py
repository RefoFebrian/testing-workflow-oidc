# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwProcessOffTheRoad(models.Model):
    _name = "tw.process.off.the.road"
    _description = "Pengurusan STNK BPKB"

    # 7: defaults methods
    def _get_default_branch(self):
        if self.env.company.parent_id:
            return self.env.company.id
        else:
            company_ids = self.env.companies.filtered(lambda x: x.parent_id)
            if company_ids:
                return company_ids[0].id
        
        if not self.id:
            return self.env.company.id
            
        raise Warning(_('Please choose another branch / company other than %s on the top right of the screen.'%self.env.company.name))
        
    def _get_default_date(self):
        return datetime.now().strftime('%Y-%m-%d')

    # 8: fields
    division = fields.Selection([('Unit','Unit')], 'Division', default='Unit')
    name = fields.Char('No Reference',size=20, readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('except_invoice', 'Invoice Exception'),
        ('confirm','Confirmed'),
        ('cancel','Canceled'),
        ('done','Done')
    ], 'State', readonly=True,default='draft')
    process_date = fields.Date('Tanggal Pengurusan',default=_get_default_date)
    invoice_count = fields.Integer(string='Invoice', compute='_compute_invoice_count')

    # Audit Trail
    confirm_uid = fields.Many2one('res.users',string="Confirmed by")
    confirm_date = fields.Datetime('Confirmed on')
    done_uid = fields.Many2one('res.users',string="Done by")
    done_date = fields.Datetime('Done on')
    cancel_uid = fields.Many2one('res.users',string="Cancelled by")
    cancel_date = fields.Datetime('Cancelled on')

    # 9: relation fields
    company_id = fields.Many2one('res.company', string='Branch', required=True, default=_get_default_branch)  
    partner_id = fields.Many2one('res.partner','Biro Jasa',domain=[('category_id.name','in',['Birojasa'])])
    available_partner_ids = fields.Many2many('res.partner', string='Domain Partner', compute='_compute_available_partner_ids')
    customer_id = fields.Many2one('res.partner','Customer',domain=[('category_id.name','in',['Customer'])])
    process_otr_line_ids = fields.One2many('tw.process.off.the.road.line','process_offtr_id',string="Table Penerimaan STNK")

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('process_otr_line_ids')
    def _compute_invoice_count(self):
        for record in self:
            if record.id:
                invoice = self.env['account.move'].search([('process_offtr_id', '=', record.id)])
                record.invoice_count = len(invoice)
            else:
                record.invoice_count = 0

    @api.depends('company_id')
    def _compute_available_partner_ids(self):
        for record in self:
            partner_ids = []
            pricelist_bbn_obj = self.env['product.pricelist'].search([
                ('company_id','=',record.company_id.id),
                ('type','=','bbn_purchase')
            ])

            for pricelist in pricelist_bbn_obj:
                partner_ids.append(pricelist.partner_id.id)

            record.available_partner_ids = partner_ids 

    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            line_commands = vals.pop('process_otr_line_ids', [])
            if not line_commands :
                raise Warning(_("Perhatian !\nTidak ada detail pengurusan. Data tidak bisa di save.")) 
            branch_src = self.env['res.company'].suspend_security().search([('id','=',vals['company_id'])],limit=1)
            vals['name'] = self.env['ir.sequence'].with_company(branch_src).get_sequence_code('PSB', branch_src.code)
            vals['process_date'] = self._get_default_date()

            process_offtr_id = super(TwProcessOffTheRoad, self).create(vals)
            return process_offtr_id

    def write(self,values,context=None):
        line_commands = values.pop('process_otr_line_ids', False)
        result = super(TwProcessOffTheRoad,self).write(values)
        return result
    
    def unlink(self):
        for item in self:
            if item.state != 'draft':
                raise Warning(_("Perhatian !\nPengurusan STNK BPKB sudah diproses, data tidak bisa didelete !"))
        return super(TwProcessOffTheRoad, self).unlink()

    # 13: action methods
    def action_view_invoice(self):
        self.ensure_one()
        invoices = self.env['account.move'].search([
            ('process_offtr_id', '=', self.id)
        ])

        action = {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'target': 'current',
        }

        if not invoices:
            # optional: raise UserError
            # raise UserError("Tidak ada invoice untuk dokumen ini.")
            action.update({
                'view_mode': 'list,form',
                'domain': [('id', '=', 0)],
            })
            return action

        # Jika hanya 1 invoice → buka form
        if len(invoices) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': invoices.id,
            })
        else:
            # Jika lebih dari 1 invoice → buka list view
            action.update({
                'view_mode': 'list,form',
                'domain': [('id', 'in', invoices.ids)],
            })

        return action

    def action_cancel(self):
        self.write({
            'state': 'cancel',
            'cancel_uid':self._uid,
            'cancel_date':datetime.now()
        })                          
        for x in self.process_otr_line_ids :
            lot_obj = self.env['stock.lot'].search([
                ('company_id','=',self.company_id.id),
                ('id','=',x.lot_id.id),
            ])
            if not lot_obj :
                raise Warning(_("Perhatian !\nNo Engine Tidak Ditemukan."))
            if lot_obj:
                if lot_obj.registration_process_id or lot_obj.notice_receipt_id or lot_obj.vehicle_registration_receipt_id or lot_obj.vehicle_ownership_receipt_id or lot_obj.birojasa_billing_id :
                    raise Warning(_("Perhatian !\nNo engine \'%s\' telah diproses, data tidak bisa di cancel !")%(lot_obj.name))                    
                else :                
                    lot_obj.write({
                        'process_otr_id':False,
                        'document_state':'document_receive',
                        'biro_jasa_id':False,
                        'process_otr_date' : False
                    })
                     
                    if lot_obj.state == 'sold' :
                        lot_obj.write({'state':'sold_offtr'})
                    if lot_obj.state == 'paid' :
                        lot_obj.write({'state':'paid_offtr'})
         
        self._check_invoice_state(self.name)
        
    def action_confirm(self):
        self._check_available_line()
        tanggal = self._get_default_date()
        self.write({
            'state': 'confirm',
            'process_date':tanggal,
            'confirm_uid':self._uid,
            'confirm_date':datetime.now()
        })       
  
        for x in self.process_otr_line_ids :
            lot_obj = self.env['stock.lot'].search([
                ('id','=',x.lot_id.id)
            ])             
            if lot_obj :               
                lot_obj.write({
                    'biro_jasa_id':self.partner_id.id,                                  
                })
                if lot_obj.state == 'paid_offtr' :
                    lot_obj.write({
                        'state':'paid'
                    })
                if lot_obj.state == 'sold_offtr' :
                    lot_obj.write({
                        'state':'sold'
                    })

    def action_create_invoice(self):
        self._check_invoice_duplication()
        self.action_create_invoice_supplier()
        return self.action_create_invoice_customer()
            
    def action_create_invoice_customer(self):
        invoice_bbn = {}
        invoice_bbn_line = []
        total_bbn = 0
        lot = self.env['stock.lot']
        branch_setting_obj = self.env['tw.branch.setting'].search([('company_id','=',self.company_id.id)],limit=1)
        if not branch_setting_obj :
            raise Warning(_("Perhatian !\nPlease define Branch Setting for this branch: \"%s\".") % (self.company_id.name))
        for x in self.process_otr_line_ids :    
            if x.plate_id.value == 'H':
                if not branch_setting_obj.pricelist_sale_bbn_hitam_id:
                    raise Warning(_("Perhatian !\nPrice List BBN hitam belum diisi di Master Branch")) 
                else :
                    pricelist = branch_setting_obj.pricelist_sale_bbn_hitam_id.id
            elif x.plate_id.value == 'M':
                if not branch_setting_obj.pricelist_sale_bbn_merah_id:
                    raise Warning(_("Perhatian !\nPrice List BBN Merah belum diisi di Master Branch")) 
                else :
                    pricelist = branch_setting_obj.pricelist_sale_bbn_merah_id.id
            price = self.env['product.pricelist'].browse(pricelist).with_company(self.company_id.id)._price_get(x.lot_id.product_id, 1)[pricelist]
            if price is False:
                return Warning(_("Perhatian !\nData Pricelist BBN tidak ditemukan untuk produk engine %s, silahkan konfigurasi data cabang dulu.")%(x.lot_id.name))
            else:
                total_bbn += price

        account_setting_obj = branch_setting_obj.account_setting_id
        if not account_setting_obj :
            raise Warning(_("Perhatian !\nPlease define Account Setting for this branch: \"%s\".") % (self.company_id.name))
                
        if branch_setting_obj :
            debit_account_id = account_setting_obj.journal_customer_bbn_id.default_debit_account_id.id   
            credit_account_id = account_setting_obj.journal_customer_bbn_id.default_credit_account_id.id   
            if not account_setting_obj.journal_customer_bbn_id :
                raise Warning(_('Please define Journal Off the road to on the road in Setup Division for this branch: "%s".') % (self.company_id.name))                 
        elif not account_setting_obj :
            raise Warning(_('Please define Journal in Setup Division for this branch: "%s".') % (self.company_id.name))                              

        code = account_setting_obj.journal_customer_bbn_id.code
        prefix = self.company_id.code
              
        obj_inv = self.env['account.move']
        invoice_bbn = {
            'process_offtr_id':self.id,
            'name':self.env['ir.sequence'].get_sequence_code(code, prefix),
            'ref':self.name,
            'division':self.division,
            'journal_id' : account_setting_obj.journal_customer_bbn_id.id,
            'partner_id':self.customer_id.id,
            'invoice_date':self.process_date,
            'move_type': 'out_invoice',                      
            'invoice_origin': self.name,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids':[],
            'invoice_payment_term_id': self.partner_id.property_supplier_payment_term_id.id,
            'company_id':self.company_id.id
        }
        invoice_bbn_line.append([0,False,{
            'account_id':credit_account_id,
            'partner_id':self.customer_id.id,
            'name': 'BBN ' + str(self.name),
            'quantity': 1,
            'price_unit':total_bbn
        }])
        
        invoice_bbn['invoice_line_ids'] = invoice_bbn_line
        
        invoice_bbn_create = obj_inv.create(invoice_bbn)
        # Sebelumnya action open
        invoice_bbn_create.sudo().action_post()
        
        #add customer invoice pengurusan stnk dan bpkb di lot
        for x in self.process_otr_line_ids :
            lot_search = lot.search([
                ('id','=',x.lot_id.id)
            ])
            if not lot_search :
                raise Warning(_('Perhatian !\nNo engine: "%s" tidak ditemukan.') % (x.lot_id))   
            x.lot_id.write({
                'process_otr_date':self.process_date,
                'inv_process_otr_id':invoice_bbn_create
            })
                  
        return invoice_bbn_create

    def action_create_invoice_supplier(self):
        invoice_bbn = {}
        invoice_bbn_line = []
        total = 0
        obj_inv = self.env['account.move']
        lot = self.env['stock.lot']
        
        branch_setting_obj = self.env['tw.branch.setting'].search([
            ('company_id','=',self.company_id.id),
        ])
        if not branch_setting_obj :
            raise Warning(_('Perhatian !\nPlease define Branch Setting for this branch: "%s".') % (self.company_id.name))
        account_setting_obj = branch_setting_obj.account_setting_id
        if not account_setting_obj :
            raise Warning(_('Perhatian !\nPlease define Account Setting for this branch: "%s".') % (self.company_id.name))
  
        if account_setting_obj.journal_birojasa_bbn_id :
            debit_account_id = account_setting_obj.journal_birojasa_bbn_id.default_debit_account_id.id 
            credit_account_id = account_setting_obj.journal_birojasa_bbn_id.default_credit_account_id.id  
            if not debit_account_id or not credit_account_id :
                raise Warning(_('Perhatian !\nPlease define Journal Off the road to on the road in Setup Division for this branch: "%s".') % (self.company_id.name))        
        elif not account_setting_obj.journal_birojasa_bbn_id :
            raise Warning(_('Perhatian !\nPlease define Journal Setup Division for this branch: "%s".') % (self.company_id.name)) 

        code = account_setting_obj.journal_birojasa_bbn_id.code
        prefix = self.company_id.code
        
        for record in self.process_otr_line_ids :   
            city = record.customer_stnk_id.city_id.id
            if not record.customer_stnk_id.city_id.id :
                city = record.customer_stnk_id.city_domicile_id.id 
            
            # TODO: Buat fungsi ini nanti di line, get product.pricelist.item
            price = self.env['tw.process.off.the.road.line']._get_harga_bbn_detail(record.plate_id, record.lot_id.product_id.product_tmpl_id,self.company_id) 
            if not price:
                raise Warning(_('Perhatian !\nHarga BBN tidak ditemukan, masukan setting configurasi birojasa dalam master branch !'))                 
            total = price
            # TODO: Bagaimana hande Jasa? Di Pricelist BBN apakah ada item jasa?
            # total = process_offtr_line_obj.total
            # total_jasa = process_offtr_line_obj.jasa + process_offtr_line_obj.jasa_area
            invoice_bbn = {
                'process_offtr_id':self.id,
                'name':self.env['ir.sequence'].get_sequence_code(code, prefix),
                'ref': self.name,
                'division':self.division,
                'journal_id':account_setting_obj.journal_birojasa_bbn_id.id,
                'partner_id':self.partner_id.id,
                'invoice_date':self.process_date,
                'move_type':'in_invoice', 
                # TODO: QQ dipake atau tidak?
                # 'qq_id':record.customer_stnk_id.id, 
                'invoice_origin':self.name,
                'invoice_date': fields.Date.today(),
                'invoice_line_ids':[],
                'invoice_payment_term_id': self.partner_id.property_supplier_payment_term_id.id,
                'company_id':self.company_id.id
            }
            invoice_bbn_line  = [[0,False,{
                'account_id':debit_account_id,
                'partner_id':self.partner_id.id,
                'name': 'BBN '+record.lot_id.product_id.name,
                'quantity': 1,
                'price_unit':price,
            }]]
            invoice_bbn['invoice_line_ids']=invoice_bbn_line
            invoice_bbn_create = obj_inv.create(invoice_bbn)
            invoice_bbn_create.sudo().action_post()
            record.lot_id.write({'accrue_bbn_move_id':invoice_bbn_create,'service_amount':price})
        return True
 
    @api.model
    def action_process_done(self):
        self.write({
            'state': 'done'
        })

    # 14: private methods
    def _check_invoice_duplication(self):
        invoice = self.env['account.move'].search([
            ('invoice_origin', '=', self.name),
            ('state', '!=', 'cancel')
        ],limit=1)
        if invoice:
            raise Warning(_("Perhatian !\nInvoice No \'%s\' sudah ada, tidak bisa membuat invoice lagi !")%(invoice.name))

    def _check_invoice_state(self):
        obj_inv = self.env['account.move'].search([('origin','=',self.name)]) 
        for x in obj_inv :
            if x.state == 'posted':
                raise Warning(_("Perhatian !\nInvoice No \'%s\' telah dibayar, Pengurusan STNK dan BPKB tidak bisa dicancel  !")%(x.lot_id))
            else :
                x.button_cancel() 

    def _check_available_line(self):
        for record in self:
            if not record.process_otr_line_ids:
                raise Warning(_("Perhatian !\nTidak ada data penerimaan STNK, Pengurusan STNK dan BPKB tidak bisa dicancel  !"))
