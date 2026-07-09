# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class TwFakturPajakGabunganLine(models.Model):
    _name = "tw.faktur.pajak.gabungan.line"
    _description = "Faktur Pajak Gabungan Line"

    # 8: Fields
    model = fields.Char(string='Object Name', readonly=True)
    name = fields.Char(string="Transaction No", readonly=True)
    date = fields.Date(string='Date', readonly=True)
    total_amount = fields.Float(string="Total Amount", readonly=True)
    untaxed_amount = fields.Float(string="Untaxed Amount", readonly=True)
    tax_amount = fields.Float(string="Tax Amount", readonly=True)
    
    # 9: Relation Fields
    source_doc_id = fields.Reference(
        string='Source Document',
        selection='_get_source_doc_models',
        compute='_compute_source_doc_id',
        readonly=True,
    )
    pajak_gabungan_id = fields.Many2one(
        'tw.faktur.pajak.gabungan', 
        string="Faktur Pajak Gabungan", 
        ondelete='cascade'
    )

    # 10: Compute Methods
    @api.model
    def _get_source_doc_models(self):
        # Ambil model dari master list
        records = self.env['tw.master.model.pajak'].search([])
        return [(r.model_name, r.name) for r in records]

    @api.depends('model', 'name')
    def _compute_source_doc_id(self):
        for line in self:
            line.source_doc_id = False
            if line.model and line.name:
                doc_id = self.env[line.model].search([('name', '=', line.name)], limit=1)
                if doc_id:
                    line.source_doc_id = f"{line.model},{doc_id.id}"