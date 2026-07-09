# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from validate_email import validate_email

# 3:  imports of odoo
from odoo import models, fields, api

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning, AccessError

# 5: local imports

# 6: Import of unknown third party lib

class PartnerContact(models.Model):
    _name = "tw.partner.contact"
    _description = "Partner Contacts"

    # 7: defaults methods

    # 8: fields
    name = fields.Char(string='Kontak', required=True)
    dapat_dihubungi = fields.Boolean(string='Dapat dihubungi', default=True)
    
    # 9: relation fields
    type_id = fields.Many2one('tw.selection', string='Tipe',domain=[('type','=','ContactType')], required=True)
    company_id = fields.Many2one('res.company', string="Branch", domain="[('parent_id', '!=', False)]")
    partner_id = fields.Many2one('res.partner', string='Partner')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('type_id')
    def _onchange_contact_typeId(self):
        self.name= False
    
    @api.onchange('type_id','name')
    def _onchange_name(self):
        warning = {}
        if self.type_id.name == 'Phone':
            if self.name:
                if not self.name.isdigit() or len(self.name) < 5:
                    self.name = False
                    warning = {'title': 'Perhatian', 'message':'No telp tidak boleh mengandung karakter, minimal 5 digit. \n No Telp: %s' % str(self.name)}
        elif self.type_id.name == 'Email':
            if self.name:
                check_email = validate_email(self.name)
                if not check_email:
                    self.name = False
                    warning = {'title': 'Perhatian', 'message':'Penulisan email tidak valid.'}
        return {'warning':warning}

    # 12: override methods

    def _auto_init(self):
        res = super(PartnerContact, self)._auto_init()
        self._cr.execute("SELECT indexname FROM pg_indexes WHERE indexname = 'tw_partner_contact_partner_id_company_id_index'")
        if not self._cr.fetchone():
            self._cr.execute('CREATE INDEX tw_partner_contact_partner_id_company_id_index ON tw_partner_contact (partner_id, company_id)')
        return res

   # 13: action methods

   # 14: private methods

    def check_partner_contact(self, partner_id, contact_type_id, contact):
        query_where = "WHERE 1=1 "
        
        if partner_id :
            query_where += f"AND p.id = {partner_id} "
        
        if contact_type_id:
            query_where += f"AND pct.id = {contact_type_id} "

        query_where +=  f"AND pc.name = '{contact}'"
            
        check_contact_query = f"""
            SELECT pc.name
            FROM tw_partner_contact pc
            JOIN res_partner p ON pc.partner_id = p.id
            JOIN tw_selection pct ON pc.type_id = pct.id
            {query_where}
        """
        self._cr.execute(check_contact_query)
        ress = self._cr.fetchall()
        if ress:
            return True
        return False
                