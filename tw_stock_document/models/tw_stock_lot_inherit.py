# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class StockLotInherit(models.Model):
    """
    Inherit stock.lot to add One2many relation to tw.stock.document
    """
    _inherit = "stock.lot"

    stock_document_ids = fields.One2many(
        comodel_name='tw.stock.document',
        inverse_name='lot_id',
        string='Stock Documents',
    )
    stock_document_count = fields.Integer(
        compute='_compute_stock_document_count',
        string='Document Count',
    )

    @api.depends('stock_document_ids')
    def _compute_stock_document_count(self):
        for rec in self:
            rec.stock_document_count = len(rec.stock_document_ids)

    def action_view_stock_documents(self):
        """Open stock documents related to this lot"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Stock Documents'),
            'res_model': 'tw.stock.document',
            'view_mode': 'list,form',
            'domain': [('lot_id', '=', self.id)],
            'context': {
                'default_lot_id': self.id,
                'default_company_id': self.company_id.id,
                'search_default_groupby_type': 1,
                'create': False,
                'edit': False,
                'delete': False,
            },
        }
