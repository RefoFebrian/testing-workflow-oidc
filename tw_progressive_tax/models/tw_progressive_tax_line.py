# -*- coding: utf-8 -*-

# 1: imports of python lib
import difflib
import json
import os
import logging
import re

# 2: import of known third party lib
from datetime import date, timedelta, datetime

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwProgressiveTaxLine(models.Model):
    _name = "tw.progressive.tax.line"
    _description = "TW Progressive Tax Line"
   
    # 8: fields
    def _check_amount(self):
        for ppl in self:
            if ppl.progressive_tax_amount <= 0:
                return False
        return True

    name = fields.Char('Name')
    progressive_tax_id = fields.Many2one('tw.progressive.tax', 'Proses Pajak Progressive')
    lot_id = fields.Many2one('stock.lot','No Engine', required=True, domain="[('inv_progressive_tax_id','=',False),('registration_process_date','!=',False),('birojasa_billing_id','=',False),('document_state','=','registration_process'),('company_id','=',parent.company_id),('biro_jasa_id','=',parent.biro_jasa_id)]")
    customer_stnk_id = fields.Many2one(related='lot_id.customer_stnk_id',readonly=True,string='Customer STNK')
    progressive_tax_amount = fields.Float('Pajak Progresif')
    invoice_id = fields.Many2one('account.move', 'Invoice')
    status = fields.Selection([('draft','Draft'),('confirmed','Confirmed'),('cancelled','Cancelled')],'Status',default='draft')
    cancel_uid = fields.Many2one('res.users', string="Cancelled by")
    cancel_date = fields.Datetime('Cancelled on')

    @api.constrains('progressive_tax_id', 'lot_id')
    def _check_unique_progressive_tax_id(self):
        for record in self:
            if record.progressive_tax_id and record.lot_id:
                if self.search([('progressive_tax_id', '=', record.progressive_tax_id.id), ('lot_id', '=', record.lot_id.id), ('id', '!=', record.id)]):
                    raise Warning('Detail Engine tidak boleh sama, mohon dicek kembali !')

    def _check_amount(self):
        for ppl in self:
            if ppl.progressive_tax_amount <= 0:
                raise Warning('Nilai amount tidak boleh negatif (-) atau 0.00 !')
        return True

    def name_get(self, context=None):
        if context is None:
            context = {}
        res = []
        for record in self :
            name = record.name
            if record.lot_id:
                name = "[%s] %s" % (record.lot_id.name, name)
            res.append((record.id, name))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            # Be sure name_search is symetric to name_get
            args = ['|',('name', operator, name),('lot_id.name', operator, name)] + args
        categories = self.search(args, limit=limit)
        return categories.name_get()

    @api.onchange('lot_id','company_id','biro_jasa_id')
    def onchange_engine(self):
        for line in self.progressive_tax_id:
            branch = line.company_id.id
            birojasa = line.biro_jasa_id
            if not branch or not birojasa:
                raise Warning(_('No Branch Definned !\nSebelum menambahkan pajak progressive, input Branch dan Birojasa terlebih dahulu !'))  
    
    def create_invoice_line(self,name,company_id,division,tanggal):        
        if self.progressive_tax_amount > 0.00:
            invoice_vals = self._prepare_invoice()
            invoice = self.env['account.move'].with_context(
                default_move_type='in_invoice',
                skip_is_manually_modified=True
            ).with_company(self.progressive_tax_id.company_id.id).create(invoice_vals)
            invoice.sudo().action_post()
            progressive_tax_id = invoice
            
            self.lot_id.write({'inv_progressive_tax_id':progressive_tax_id.id})
        
            self.write({'name':invoice_vals.get('name'),'invoice_id': progressive_tax_id.id,'status':'confirmed'})

    def _prepare_invoice(self):
        """Prepare the dict of values to create the new invoice.
        """
        self.ensure_one()

        branch_setting_obj = self.env['tw.branch.setting'].search([('company_id', '=', self.progressive_tax_id.company_id.id)])
        if not branch_setting_obj.account_setting_id:
            raise Warning(
                "Account setting is not set for this branch.\n"
                "- Go to the Master Branch Setting.\n"
                "- Set the 'Account Setting' to proceed.\n"
                "This' configuration is required to create accounting entries."
            )
        if not branch_setting_obj.account_setting_id.journal_birojasa_progressive_id:
            raise Warning(
                    "Journal Pajak Progressive is not set for this branch.\n"
                    "- Go to the Account Setting.\n"
                    "- Set the 'Journal Pajak Progressive'.\n"
                    "This configuration is required to create Accrue Expedition."
                )

        lot_obj = self.lot_id

        if not lot_obj.registration_process_date or not lot_obj.registration_process_id:
            raise Warning(_('Perhatian !\nEngine %s, Belum melakukan proses STNK, coba periksa kembali !')%(lot_obj.name)) 

        if lot_obj.inv_progressive_tax_id:
            raise Warning(_('Perhatian !\nEngine %s sudah memiliki Invoice Pajak Progressive, coba periksa kembali !')%(lot_obj.name))

        if lot_obj.birojasa_billing_id:
            raise Warning(_('Perhatian !\nEngine %s sudah melakukan proses biro jasa, coba periksa kembali !')%(lot_obj.name))  

        customer_name = str(lot_obj.customer_stnk_id.name)
        engine_no = str(lot_obj.name)
        string = "Pajak Progressive a/n \'%s\', No Engine \'%s\' !" %(customer_name,engine_no)

        code = branch_setting_obj.account_setting_id.journal_birojasa_progressive_id.code
        prefix = self.progressive_tax_id.company_id.code
        
        invoice_vals = {
            'name': self.env['ir.sequence'].get_sequence_code(code, prefix),
            'division': self.progressive_tax_id.division,
            # TODO: qq_id belum ada
            # 'qq_id': lot_obj.customer_stnk.id,
            'ref': self.progressive_tax_id.name or '',
            'move_type': 'out_invoice',
            'currency_id': self.progressive_tax_id.company_id.currency_id.id,
            'journal_id': branch_setting_obj.account_setting_id.journal_birojasa_progressive_id.id,
            'partner_id': lot_obj.customer_stnk_id.id,
            # TODO: Check karena sebelumnya ambil dari ir.sequence (PPD bukan PPR)
            'invoice_origin': self.name,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids':[],
            'invoice_payment_term_id': lot_obj.partner_id.property_supplier_payment_term_id.id,
            'company_id': self.progressive_tax_id.company_id.id,
        }

        invoice_vals['invoice_line_ids'].append((0, 0, self._prepare_account_move_line(branch_setting_obj.account_setting_id.journal_birojasa_progressive_id,string)))
        return invoice_vals

    def _prepare_account_move_line(self, journal_obj,string):
        self.ensure_one()

        # Default to journal's default credit account if stock valuation account is not found
        account_obj = journal_obj.default_credit_account_id
        if not account_obj:
            raise Warning(f'Default Credit Account is not set for journal {journal_obj.name}.')

        res = {
            'account_id':account_obj.id,
            'partner_id': self.customer_stnk_id.id,
            'name': string,
            'quantity': 1,
            'price_unit':self.progressive_tax_amount  or 0.00,
        }
            
        return res