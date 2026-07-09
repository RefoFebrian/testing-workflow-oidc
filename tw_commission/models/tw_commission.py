# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime
import math

# 2: import of known third party lib
import xlrd
import base64
from datetime import datetime, timedelta

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwCommission(models.Model):
    _name = "tw.commission"
    _description = "Hutang Komisi"
    _order = "id asc"
    
    # 7: defaults methods
    @api.depends('commission_line_ids.amount')
    def _get_max_hc(self):
        for record in self:
            nilai_max = 0.0
            if not record.commission_line_ids:
                record.amount_commission = nilai_max
            for line in record.commission_line_ids:
                if nilai_max < line.amount:
                    nilai_max = line.amount
                record.amount_commission = nilai_max

    def _get_default_branch(self):
        company_ids = False
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1 :
            return company_ids[0].id
        return False

    # 8: fields
    name = fields.Char("Name", size=30, required=True)
    date_start = fields.Date("Date Start", required=True)
    date_end = fields.Date("Date End", required=True)
    description = fields.Text("Keterangan")
    
    commission_type = fields.Selection([('fix', 'Fix'), ('non', 'Non Fix')], "Tipe Komisi", change_default=True, required=True)                  
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm','Confirmed'),
                              ('rejected', 'Rejected'),
                              ('editable', 'Editable'),
                              ('on_revision', 'On Revision')], 'State', default='draft', readonly=True)
    division = fields.Selection([('Unit', 'Unit')], 'Division', change_default=True, required=True, default='Unit')                     
    
    active = fields.Boolean('Active', default=True)
    amount_commission = fields.Float(string='Nilai Hutang Komisi', compute="_get_max_hc")

    # Audit Trail
    confirm_uid = fields.Many2one('res.users', string="Approved by")
    confirm_date = fields.Datetime('Approved on')
    cancel_uid = fields.Many2one('res.users', string="Cancelled by")
    cancel_date = fields.Datetime('Cancelled on')    
    

    # 9: relation fields
    company_id = fields.Many2one('res.company', 'Branch', required=True, default=_get_default_branch)
    commission_line_ids = fields.One2many('tw.commission.line', 'commission_id')
    area_id = fields.Many2one('res.area', string='Area')

    # 10: constraints & sql constraints


    # 11: compute/depends & on change methods

    def copy(self, default=None):
        if default is None:
            default = {}
        
        start_date = datetime.strptime(self.date_start, '%Y-%m-%d') + timedelta(days=1)
        end_date = datetime.strptime(self.date_start, '%Y-%m-%d') + timedelta(days=2)
        default.update({
            'company_id': self.company_id.id,
            'division': self.division,
            'area_id': self.area_id.id,
            'name': self.name,
            'date_start': start_date,
            'date_end': end_date,
            'keterangan': self.keterangan,
            'commission_type': self.commission_type,              
            'state': 'draft',
            'active': True,
        })
        commission_line_ids = []
        for lines in self.commission_line_ids:
            commission_line_ids.append([0, False, {
                'product_template_id': lines.product_template_id.id,
                'amount': lines.amount,
            }])
        default.update({'commission_line_ids': commission_line_ids})
                
        return super(TwCommission, self).copy(default=default)
    # 12: override methods
    def unlink(self):
        for item in self:
            if item.state != 'draft':
                raise Warning('Hutang Komisi sudah diproses, data tidak bisa didelete!')
        return super(TwCommission, self).unlink()
    
    # 13: action methods
    def action_confirm(self):
        self.ensure_one()
        self.write({
            'confirm_uid': self._uid,
            'confirm_date': datetime.now(),
            'state': 'confirm'
        })
  
    # 14: private methods
    def _get_amount_hc(self,partner_id,product_tmpl_id):
        
        commission_obj = self.search([('partner_id', '=', partner_id.id),('active', '=', True),('state', 'in', ['approved', 'confirm', 'editable'])])
        
        if not commission_obj:
            raise Warning('Tidak ada hutang komisi yang aktif! dengan partner %s' % partner_id.name)

        if len(commission_obj) > 1:
            raise Warning('Terdapat lebih dari 1 hutang komisi yang aktif! dengan partner %s' % partner_id.name)
        
        amount_commission = 0
        for comm in commission_obj:
            for line in comm.commission_line_ids:
                if line.product_template_id.id == product_tmpl_id:
                    amount_commission = line.amount
                    break

        return amount_commission
