#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime,date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib
try:
    from pyfcm import FCMNotification
except:
    FCMNotification = None
from lxml.html import fromstring, tostring
from lxml.html import builder as E


class FirebaseUser(models.Model):

    _name = "tw.firebase.user"
    _description = "Firebase User"
    _order = "name desc"

    # 7: defaults methods

    # 8: fields
    name = fields.Char(string='Device Name')
    firebase_id = fields.Char(string="Firebase",  help="")
    firebase_token = fields.Char(string="Firebase token",  help="")
    access_token = fields.Char(string="Access token",  help="")
    device_id = fields.Char(string="Device",  help="")
    device_name = fields.Char(string="Device name",  help="")
    version = fields.Char(string="Version",  help="")
    version_code = fields.Char(string="Version code",  help="")
    version_name = fields.Char(string="Version name",  help="")
    active = fields.Boolean(string="Active",  help="")

    # 8: relation fields
    user_id = fields.Many2one(comodel_name='res.users',  string="User",  help="")

    # 9: constraints & sql constraints

    # 10: compute/depends & on change methods

    # 11: override methods
    # 
    # def name_get(self, context=None):
        # return super(FirebaseUser, self).name_get(context)

    # @api.model
    # def name_search(self, name='', args=None, operator='ilike', limit=100):
        # return super(FirebaseUser, self).name_search(name, args, operator, limit)

    # @api.model
    # def create(self, vals):
        # return super(FirebaseUser, self).create(vals)

    # 
    # def write(self, vals):
        # return super(FirebaseUser, self).write(vals)

    # 
    # def unlink(self):
        # for x in self:
            # if x.state != 'draft':
                # raise Warning('Perhatian!\nData tidak bisa dihapus.')
                # return super(FirebaseUser, self).unlink()

    # 
    # def copy(self):
        # raise Warning('Perhatian!\nData tidak bisa diduplikasi.')
        # return super(FirebaseUser, self).copy()


    # 12: action methods
    def action_activate(self):
        for x in self:
            x.active = True

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_deactivate(self):
        for x in self:
            x.active = False

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    # 13: private methods
    def _get_firebase_configuration(self, config_name):
        config = self.env['tw.api.configuration'].suspend_security().search([('api_type_id.value', '=', 'Firebase'),
                                                                              ('name', '=', config_name)],
                                                                              limit=1)
        if not config:
            raise Warning(f"No Firebase configuration named {config_name} found!")
        
        return config

    def notify_multiple_devices(self, to_regids, message_title, message_body, data=False, config_name='Tunas-Honda'):
        config = self._get_firebase_configuration(config_name)
        push_service = FCMNotification(service_account_file=config.get_creds_file_path(),
                                       project_id=config.project_id)
        
        notification = data.get('notification')
        notification['id'] = str(notification.get('id')) # the pyfcm format have to be string
        result = push_service.notify(fcm_token=to_regids,
                                     notification_title=notification.get('title'),
                                     notification_body=notification.get('body'),
                                     notification_image=notification.get('icon'),
                                     data_payload=notification)
        return result

    def notify_single_device(self, to_regids, data=False, config_name='Tunas-Honda'):
        config = self._get_firebase_configuration(config_name)
        push_service = FCMNotification(service_account_file=config.get_creds_file_path(),
                                       project_id=config.project_id)
        
        notification = data.get('notification')
        notification['id'] = str(notification.get('id')) # the pyfcm format have to be string
        result = push_service.notify(fcm_token=to_regids,
                                     notification_title=notification.get('title'),
                                     notification_body=notification.get('body'),
                                     notification_image=notification.get('icon'),
                                     data_payload=notification)
        
        return result
