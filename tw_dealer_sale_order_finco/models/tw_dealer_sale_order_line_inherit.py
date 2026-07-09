# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning, ValidationError

# 5: local imports

# 6: Import of unknown third party lib

class TwSaleOrder(models.Model):
    _inherit = "tw.dealer.sale.order.line"

    # 7: defaults methods

    # 8: fields
    finco_incentive = fields.Float()
    finco_incentive_tax = fields.Boolean(string="Incentive Finco Tax")
    finco_po_date = fields.Date(string="Tanggal PO")
    finco_po_number = fields.Char(string="No. PO")
    tenor = fields.Integer(string="Tenor")
    installment = fields.Integer(string="Cicilan")

    # 9: relation fields

    # 10: constraints & sql constraints
    @api.constrains('downpayment')
    def _check_downpayment(self):
        for record in self:
            if record.order_id.finco_id and record.downpayment <= 0:
                raise ValidationError(_("Silahkan masukkan jumlah Uang Muka/DP yang valid untuk penjualan kredit."))
            
    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
    def _get_incentive_finco_amount(self):
        company = self.order_id.company_id
        finco = self.order_id.finco_id
        
        if not finco or not company:
            return False
        
        today = date.today()
        pricelist_incentives = finco.incentive_partner_ids.filtered(lambda x:
            x.active == True and
            x.start_date < today < x.end_date)
        if not pricelist_incentives:
            raise Warning(_("Master incentive finco belum di set atau sudah expired!"))

        # incentive_value = pricelist_incentives.incentive_finco_detail_ids.filtered(lambda x: x.company_id == branch)
        incentive_value = pricelist_incentives.incentive_finco_detail_ids.filtered(lambda x: x.company_id == company)
        if not incentive_value:
            raise Warning(_("Master incentive finco untuk cabang %s tidak ditemukan di finco %s!"%(company.name, finco.name)))
        
        self.finco_incentive = incentive_value.amount
        
        return incentive_value
    
    def _prepare_update_lot(self):
        self.ensure_one()
        vals = super()._prepare_update_lot()
        vals.update({
            'finco_id': self.order_id.finco_id.id,
            'tenor': self.tenor,
            'installment': self.installment,
        })
        return vals
        