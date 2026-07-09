from odoo import models, fields, api, _

class SaleAccountMoveLineInherit(models.Model):	
    _inherit = "account.move.line"	

    purchase_return_line_ids = fields.Many2many(	
        'tw.purchase.return.line',	
        'tw_purchase_return_line_invoice_rel',	
        'invoice_line_id', 'order_line_id',	
        string='Purchase Return Lines', readonly=True, copy=False)	
