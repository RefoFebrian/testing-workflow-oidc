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


class TwApprovalConfig(models.Model):
    _name = "tw.approval.config"
    _description = "Approval Config"
    
    # 7: defaults methods

    # 8: fields
    name = fields.Char(string="Name")
    
    code = fields.Selection([
        ('payment','Payment'),
        ('receipt','Receipt'),
        ('purchase','Purchase'),
        ('recurring','Recurring'),
        ('non_recurring','Non Recurring'),
        ('sale','Sale'),
        ('cancel','Cancel'),
        ('request','Request'),
        ('other','Other'),
        ],string="Code",default='other')
    type = fields.Selection([('biaya','Biaya'),('discount','Discount')],default="biaya")
    
    # 9: relation fields
    model_id = fields.Many2one('ir.model',string="Form",ondelete='set null')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.constrains('model_id','code','type')
    def _check_model_id_code(self):
        for record in self:
            if record.model_id and record.code and record.type:
                duplicate_config_obj = self.env['tw.approval.config'].suspend_security().search(
                    [
                        ('model_id', '=', record.model_id.id), 
                        ('code', '=', record.code), 
                        ('type', '=', record.type), 
                        ('id', '!=', record.id)
                    ], limit=1)
                if duplicate_config_obj:
                    raise Warning(_("Approval Config already exists for model %s - code %s - type %s !" % (record.model_id.name, record.code, record.type)))

    @api.onchange('model_id','code')
    def change_model_id(self):
        if self.model_id:
            name = self.model_id.name
            if self.code:
                name += ' - ' + self.code
            self.name = name
        else:
            self.name = False

    @api.onchange('type')
    def change_type(self):
        domain ={}
        if self.type == 'discount' :
            domain['model_id'] = [('model','in',('dealer.sale.order','dealer.spk'))]
            form = self.env['ir.model'].search([
                                                ('model','=','dealer.sale.order')
                                                ])
            self.model_id = form.id
        elif self.type == 'biaya' :
            domain['model_id'] = [('model','!=','dealer.sale.order')]
            self.model_id = False
        elif not self.type :
            self.model_id = False
        return {'domain':domain}

    # 12: override methods

    # 13: action methods

    # 14: private methods
    