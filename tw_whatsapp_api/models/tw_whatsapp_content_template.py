from odoo import models, fields, api, _
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError

class WhatsappContentTemplate(models.Model):
    _name = "tw.whatsapp.content.template"
    _description = "Whatsapp Template Message"

    name = fields.Char( required=True, string="Name")
    subject = fields.Char(string="Subject")
    content = fields.Text(string="Content")
    
    is_official = fields.Boolean(string="Is Official", default=True)

    template_type_id = fields.Many2one('tw.selection', string='Type', domain=[('type','=','TemplateWhatsapp')])
    
    _sql_constraints = [
        ('name_unique', 'unique(name)', 'name template ini sudah pernah diinput sebelumnya !')
    ]
    