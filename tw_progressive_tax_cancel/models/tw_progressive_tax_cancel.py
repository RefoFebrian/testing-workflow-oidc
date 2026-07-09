from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import UserError as Warning
from odoo.fields import Command

class TwProgressiveTaxCancel(models.Model):
    _name = "tw.progressive.tax.cancel"
    _description = 'Progressive Tax Cancel'
    _inherits = {'tw.cancellation': 'cancellation_id'}
    _inherit = ['mail.thread', 'tw.approval.mixin']
    _order = 'id desc'  

    @api.model
    def _get_default_date(self):
        return datetime.now()

    @api.model
    def _get_default_date_model(self):
        return datetime.now().date()

    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options_list(['Unit']), default='Unit')

    progressive_tax_id = fields.Many2one('tw.progressive.tax', 'Pajak Progresif')
    progressive_tax_line_ids = fields.Many2many('tw.progressive.tax.line','tw_progressive_tax_cancel_pajak_progressive_rel','cancel_pajak_progressive_id','progressive_tax_line_id',domain="[('progressive_tax_id','=',progressive_tax_id),('status','=','confirmed')]",string="PPD")
    cancellation_id = fields.Many2one('tw.cancellation', required=True, ondelete='cascade')

    @api.onchange('progressive_tax_id')
    def _onchange_progressive_tax_id(self):
        if self.progressive_tax_id:
            self.transaction_name = self.progressive_tax_id.name
        else:
            self.transaction_name = False

    @api.onchange('company_id')
    def onchange_company_id(self):
        self.progressive_tax_id = False
        self.progressive_tax_line_ids = False

    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if vals.get('progressive_tax_id'):
                progressive_tax_id = self.env['tw.progressive.tax'].browse(vals['progressive_tax_id'])
                vals['transaction_name'] = progressive_tax_id.name
                name = "X" + progressive_tax_id.name
                self._check_duplicate_transaction(name)
                vals['name'] = "X" + progressive_tax_id.name
                vals['date'] = self._get_default_date()
        return super(TwProgressiveTaxCancel, self).create(vals_list)

    # tandai
    def action_confirm(self):
        self.validity_check()
        if self.progressive_tax_id:
            branch_config_obj = self.company_id.branch_setting_id
            journal_progressive_tax_cancel_id = branch_config_obj.account_setting_id.journal_progressive_tax_cancel_id.id
            if not journal_progressive_tax_cancel_id:
                raise Warning("Attention! The Progressive Tax Cancel Journal hasn't been Created. Please Set it up First.")

            self._check_validity()
            self.invoice_cancel()
            self.move_id.sudo().action_post()
            
            # Cancel Progressive Tax
            self.progressive_tax_id._action_cancel()
        
        return self.cancellation_id.action_confirm()

    def action_request_approval(self):
        self.validity_check()
        return super().action_request_approval(value=5)
  
    def unlink(self):
        if self.state != 'draft':
            raise Warning(('Invalid action !\nTidak bisa dihapus jika state bukan Draft !'))
        return super(TwProgressiveTaxCancel,self).unlink()   
    
    def cek_stock_lot(self):
        for line in self.progressive_tax_line_ids:
            lot_mesin = line.lot_id.name
            stock = self.env['stock.lot'].search([
                ('name','=',lot_mesin),
                ('inv_progressive_tax_id','!=',False),
                ('birojasa_billing_date','=',False),
                ('birojasa_billing_id','=',False),
            ])
            if not stock:
                raise Warning(("Engine %s tidak ditemukan, atau sudah melakukan proses biro jasa, cek data kembali")%(line.lot_id.name))

    def cek_penyerahan_stnk_bpkb(self):
        for line in self.progressive_tax_line_ids:
            if line.lot_id.registration_handover_id or line.lot_id.notice_handover_id or line.lot_id.plate_handover_id :
                raise Warning(("Engine %s sudah ditarik dalam penerimaan STNK, silahkan cancel terlebih dahulu!")%(line.lot_id.name))
            if line.lot_id.ownership_handover_id :
                raise Warning(("Engine %s sudah ditarik dalam penerimaan BPKB, silahkan cancel terlebih dahulu!")%(line.lot_id.name))
        
    def validity_check(self):
        if self.progressive_tax_id.state not in ('confirmed'):
            raise Warning(("Tidak bisa cancel, status Pajak Progressive selain 'Confirm' !"))
        self.cek_penyerahan_stnk_bpkb()
        self.check_invoices()
        self.cek_stock_lot()

    def _check_duplicate_transaction(self,name):
        return self.cancellation_id._check_duplicate_transaction(name)

    def invoice_cancel(self):
        for tax_line in self.progressive_tax_id.progressive_tax_line_ids:
            invoice_id = tax_line.invoice_id
            branch_config_obj = self.company_id.branch_setting_id
            journal_progressive_tax_cancel_id = branch_config_obj.account_setting_id.journal_progressive_tax_cancel_id.id
            if not journal_progressive_tax_cancel_id:
                raise Warning("Attention! The Progressive Tax Cancel Journal hasn't been Created. Please Set it up First.")
            move_reversal = self.env['account.move.reversal'].sudo().with_context(active_model='account.move', active_ids=invoice_id.ids).create({
                'date': datetime.now(),
                'journal_id': journal_progressive_tax_cancel_id,
            })
            reversal = move_reversal.sudo().reverse_moves()
            if reversal:
                self.move_id = reversal.get('res_id',False)
                # Re-Write line division
                for line in self.move_id.line_ids:
                    line.write({'division': self.progressive_tax_id.division})

    def _check_validity(self):
        for rec in self:
            rec.check_invoices()
            if not rec.progressive_tax_id:
                raise Warning(('Please select a Progressive Tax to cancel.'))
            if rec.progressive_tax_id.state != 'confirmed':
                raise Warning(('Only Confirmed Progressive Tax can be cancelled.'))
        return True

    def check_invoices(self):
        message = ""
        checked_invoices = set()
        for tax_line in self.progressive_tax_id.progressive_tax_line_ids:
            invoice_id = tax_line.invoice_id
            if invoice_id.name in checked_invoices:
                continue
            
            # Check payment_state - if already paid (partial/paid/in_payment), cannot cancel
            if invoice_id.payment_state in ('paid', 'partial', 'in_payment'):
                message += invoice_id.name + ", "
                checked_invoices.add(invoice_id.name)
                continue
        
            # Alternative: check if there are reconciled lines
            if invoice_id.line_ids:
                for line_id in invoice_id.line_ids:
                    if (line_id.reconciled or line_id.full_reconcile_id):
                        message += invoice_id.name + ", "
                        checked_invoices.add(invoice_id.name)
                        break

        return message.rstrip(", ")