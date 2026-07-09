#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

STATES = [('draft', 'Draft'),('send', 'Send'),('unread', 'Unread'), ('read', 'Read')]

class FirebaseMessageLine(models.Model):

    _name = "tw.firebase.message.line"
    _description = "Firebase Message Line"
    _order = "send_date desc"

    # 7: defaults methods

    # 8: fields
    state = fields.Selection(selection=STATES, readonly=True, default=STATES[0][0],  string="State",  help="")
    send_date = fields.Datetime( string="Tgl kirim",  readonly=True,  help="")
    message_id = fields.Char( string="Message",  readonly=True,  help="")

    # 8: relation fields
    firebase_message_id = fields.Many2one(comodel_name="tw.firebase.message",  string="Firebase message",  readonly=True,  help="")
    employee_receiver_id = fields.Many2one(comodel_name="hr.employee",  string="Penerima",  readonly=True,  help="")

    # 9: constraints & sql constraints

    # 10: compute/depends & on change methods

    # 11: override methods
    # 
    # def name_get(self, context=None):
        # return super(FirebaseMessageLine, self).name_get(context)

    # @api.model
    # def name_search(self, name='', args=None, operator='ilike', limit=100):
        # return super(FirebaseMessageLine, self).name_search(name, args, operator, limit)

    # @api.model
    # def create(self, vals):
        # return super(FirebaseMessageLine, self).create(vals)

    # 
    # def write(self, vals):
        # return super(FirebaseMessageLine, self).write(vals)

    # 
    # def unlink(self):
        # for x in self:
            # if x.state != 'draft':
                # raise Warning('Perhatian!\nData tidak bisa dihapus.')
                # return super(FirebaseMessageLine, self).unlink()

    # 
    # def copy(self):
        # raise Warning('Perhatian!\nData tidak bisa diduplikasi.')
        # return super(FirebaseMessageLine, self).copy()


    # 12: action methods
    def action_confirm(self):
        self.state = STATES[1][0]

    def action_done(self):
        self.state = STATES[2][0]

    def action_draft(self):
        self.state = STATES[0][0]


    # 13: private methods

