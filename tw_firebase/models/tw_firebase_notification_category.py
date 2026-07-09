#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class FirebaseNotificationCategory(models.Model):

    _name = "tw.firebase.notification.category"
    _description = "Firebase Notification Category"
    _order = "name desc"

    # 7: defaults methods

    # 8: fields
    name = fields.Char(string='Name')
    title = fields.Char(string='Judul Notifikasi')
    jenis_reminder = fields.Selection(selection=[('harian','Harian'),('overdue','Overdue'),('reminder','Reminder'),('after_dealing','After Dealing')],  string="Jenis reminder", help="")
    sumber_data = fields.Selection(selection=[('proactive','Proactive'),('admin_crm','Admin CRM')],  string="Sumber data",  help="")
    max_jam = fields.Integer( string="Jam Overdue",  help="")
    active = fields.Boolean(string='Active',default=True)
    
    # 8: relation fields
    content_template_id = fields.Many2one(comodel_name="tw.firebase.content.template",  string="Template", help="")
    job_id = fields.Many2one(comodel_name="hr.job",  string="Job",  help="")

    # 9: constraints & sql constraints

    # 10: compute/depends & on change methods

    # 11: override methods
    # 
    # def name_get(self, context=None):
        # return super(FirebaseNotificationCategory, self).name_get(context)

    # @api.model
    # def name_search(self, name='', args=None, operator='ilike', limit=100):
        # return super(FirebaseNotificationCategory, self).name_search(name, args, operator, limit)

    # @api.model
    # def create(self, vals):
        # return super(FirebaseNotificationCategory, self).create(vals)

    # 
    # def write(self, vals):
        # return super(FirebaseNotificationCategory, self).write(vals)

    # 
    # def unlink(self):
        # for x in self:
            # if x.state != 'draft':
                # raise Warning('Perhatian!\nData tidak bisa dihapus.')
                # return super(FirebaseNotificationCategory, self).unlink()

    # 
    # def copy(self):
        # raise Warning('Perhatian!\nData tidak bisa diduplikasi.')
        # return super(FirebaseNotificationCategory, self).copy()


    # 12: action methods

    # 13: private methods

