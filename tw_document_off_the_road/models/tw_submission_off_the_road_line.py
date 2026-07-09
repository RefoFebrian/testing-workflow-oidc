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


class TwSubmissionOffTheRoadLine(models.Model):
    _name = "tw.submission.off.the.road.line"
    _description = "TW Submission Off The Road Line"

    # 7: defaults methods
    def _get_default_date(self):
        return datetime.now().strftime('%Y-%m-%d')

    # 8: fields
    print_date = fields.Date('Tgl Cetak Faktur',compute='_compute_print_date')
    vehicle_document_take_date = fields.Date('Tgl Ambil Faktur')
    doc_number = fields.Char('No Faktur STNK',compute='_compute_doc_number')

    # 9: relation fields
    lot_id = fields.Many2one('stock.lot','No Engine')
    available_lot_ids = fields.Many2many('stock.lot', string='Domain Lot', compute='_compute_available_lot_ids')
    submission_otr_id = fields.Many2one('tw.submission.off.the.road','Penyerahan Faktur Off The Road')
    customer_stnk_id = fields.Many2one('res.partner','Customer STNK',compute='_compute_customer_stnk_id')

    # 10: constraints & sql constraints
    @api.constrains('lot_id','submission_otr_id')
    def _check_unique_name_submission_otr_id(self):
        for x in self :
            if x.lot_id and x.submission_otr_id :
                existing = self.search([
                    ('lot_id','=',x.lot_id.id),
                    ('submission_otr_id','=',x.submission_otr_id.id),
                    ('id','!=',x.id)
                ])
                if existing :
                    raise Warning(_("Detail Engine duplicate pada Penyerahan Faktur Off The Road %s, silahkan cek kembali !")%(x.submission_otr_id.name))

    # 11: compute/depends & on change methods
    @api.depends('lot_id')
    def _compute_customer_stnk_id(self):
        for record in self :
            record.customer_stnk_id = False
            if record.lot_id :
                lot_obj = self.env['stock.lot'].search([
                    ('id','=',record.lot_id.id)
                ])
                if lot_obj.customer_stnk_id :
                    record.customer_stnk_id = lot_obj.customer_stnk_id.id

    @api.depends('lot_id')
    def _compute_print_date(self):
        for record in self :
            record.print_date = False
            if record.lot_id :
                lot_obj = self.env['stock.lot'].search([
                    ('id','=',record.lot_id.id)
                ])
                if lot_obj.print_date :
                    record.print_date = lot_obj.print_date

    @api.depends('lot_id')
    def _compute_doc_number(self):
        for record in self :
            record.doc_number = False
            if record.lot_id :
                lot_obj = self.env['stock.lot'].search([
                    ('id','=',record.lot_id.id)
                ])
                if lot_obj.doc_number :
                    record.doc_number = lot_obj.doc_number

    @api.depends('submission_otr_id')
    def _compute_available_lot_ids(self):
        for record in self :
            record.available_lot_ids = False
            if record.submission_otr_id.partner_id:
                record.available_lot_ids = self.env['stock.lot'].search([
                    ('vehicle_document_receive_id','!=',False),
                    ('doc_number','!=',False),
                    ('document_state','=','document_receive'),
                    ('company_id','=',record.submission_otr_id.company_id.id),
                    ('customer_stnk_id','=',record.submission_otr_id.partner_id.id),
                    ('vehicle_document_submission_date','=',False),
                    '|',('state','=','sold_offtr'),
                    ('state','=','paid_offtr')
                ])
            elif not record.submission_otr_id.partner_id:
                record.available_lot_ids = self.env['stock.lot'].search([
                    ('vehicle_document_receive_id','!=',False),
                    ('doc_number','!=',False),
                    ('document_state','=','document_receive'),
                    ('company_id','=',record.submission_otr_id.company_id.id),
                    ('vehicle_document_submission_date','=',False),
                    '|',
                    ('state','=','sold_offtr'),
                    ('state','=','paid_offtr')
                ])

    # 12: override methods

    # 13: action methods

    # 14: private methods