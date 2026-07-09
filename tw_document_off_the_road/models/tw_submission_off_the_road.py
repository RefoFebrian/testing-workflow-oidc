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


class TwSubmissionOffTheRoad(models.Model):
    _name = "tw.submission.off.the.road"
    _description = "TW Submission Off The Road"
    _order = "date desc"

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
    name = fields.Char('No Reference',size=20, readonly=True)
    customer_name = fields.Char('Penerima')
    description = fields.Char('Keterangan')
    date = fields.Date('Tanggal',default=_get_default_date)
    engine_number = fields.Char('No Engine', compute='_compute_engine_number')
    confirm_uid = fields.Many2one('res.users',string="Posted by")
    confirm_date = fields.Datetime('Posted on')
    division = fields.Selection([
        ('Unit','Unit')
    ], 'Division', default='Unit')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted','Posted'),
        ('cancel','Canceled')
    ], 'State', default='draft',readonly=True)

    # 9: relation fields
    company_id = fields.Many2one('res.company', string='Branch', required=True, default=_get_default_branch)
    partner_id = fields.Many2one('res.partner','Customer',domain=[('category_id.name','in',['Customer'])])
    customer_stnk_id = fields.Many2one('res.partner', 'Customer STNK', compute='_compute_customer_stnk_id')
    submission_otr_line_ids = fields.One2many('tw.submission.off.the.road.line','submission_otr_id',string="Penyerahan STNK")

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('partner_id')
    def _compute_customer_stnk_id(self):
        for record in self:
            record.customer_stnk_id = False
            partner = record.partner_id
            if partner and partner.customer_stnk_id:
                record.customer_stnk_id = partner.customer_stnk_id


    @api.onchange('partner_id')
    def onchange_partner_id(self):
        self.customer_name = False
        if self.partner_id:
            res_partner = self.env['res.partner'].search([
                ('id','=',self.partner_id.id)
            ])
            self.customer_name = res_partner.name 

    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            branch_src = self.env['res.company'].suspend_security().search([('id','=',vals['company_id'])],limit=1)
            vals['name'] = self.env['ir.sequence'].with_company(branch_src).get_sequence_code('PFK', branch_src.code)
            vals['date'] = self._get_default_date()

            line_commands = vals.pop('submission_otr_line_ids', [])
            if not line_commands :
                raise Warning(_("Perhatian!\nTidak ada detail penyerahan. Data tidak bisa di save."))
            submission_otr_id = super(TwSubmissionOffTheRoad, self).create(vals)
            return submission_otr_id

    def write(self, vals):
        line_commands = vals.pop('submission_otr_line_ids', False)
        result = super(TwSubmissionOffTheRoad, self).write(vals)
        return result

    def unlink(self):
        for submission in self:
            if submission.state != 'draft':
                raise Warning(_("Perhatian!\nPenyerahan Faktur Off The Road sudah di validate ! tidak bisa didelete !"))

        for submission in self:
            for submission_line in submission.submission_otr_line_ids :
                lot_obj = self.env['stock.lot'].search([
                    ('id','=',submission_line.lot_id.id)
                ])
                if lot_obj :
                    lot_obj.write({
                        'vehicle_document_submission_date':False,
                    })
        return super(TwSubmissionOffTheRoad, self).unlink()

    # 13: action methods
    def action_post_submission(self):
        self._check_available_line()
        date = self._get_default_date()
        self.write({
            'state':'posted',
            'date':date,
            'confirm_uid':self.env.user.id,
            'confirm_date':datetime.now()
        })
 
        for line in self.submission_otr_line_ids :
            lot_obj = self.env['stock.lot'].search([
                ('id','=',line.lot_id.id)
            ])
            lot_obj.write({
                'vehicle_document_submission_date':line.vehicle_document_take_date,
                'vehicle_document_submission_id':self.id
            })

    # 14: private methods
    def _check_available_line(self):
        for record in self:
            if not record.submission_otr_line_ids:
                raise Warning(_("Perhatian !\nTidak ada data penyerahan STNK, Pengurusan STNK dan BPKB tidak bisa dicancel  !"))
