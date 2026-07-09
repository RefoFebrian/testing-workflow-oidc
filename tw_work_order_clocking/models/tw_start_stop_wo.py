# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, time

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwStartStopWo(models.Model):    
    _name = "tw.start.stop.wo"
    _description = "TW Start Stop Work Order"

    # 7: defaults methods
    def _get_work_order_id(self):
        return self.env.context.get('work_order_id', False)

    def _get_mechanic_id(self):
        return self.env.context.get('mechanic_id', False)

    # 8: fields
    start_date = fields.Datetime(string='Start', readonly=True)
    start_uid = fields.Many2one('res.users', string='Start by', readonly=True)
    break_date = fields.Datetime(string='Break', readonly=True)
    break_uid = fields.Many2one('res.users', string='Break by', readonly=True)
    end_break_date = fields.Datetime(string='End Break', readonly=True)
    end_break_uid = fields.Many2one('res.users', string='End Break by', readonly=True)
    finish_date = fields.Datetime(string='Finish', readonly=True)
    finish_uid = fields.Many2one('res.users', string='Finish by', readonly=True)


    # 9: relation fields
    company_id = fields.Many2one('res.company', string="Branch", default=lambda self: self.env.company)
    work_order_id = fields.Many2one(
        'tw.work.order', 
        string='Work Order', 
        domain="[('mechanic_id','in',[mechanic_id,False]), ('state','in',['sale','approved'])]",
        default=_get_work_order_id
    )
    # TODO: Domain mechanic
    mechanic_id = fields.Many2one(
        'hr.employee', 
        string='Mekanik', 
        default=_get_mechanic_id
    )
    employee_id = fields.Many2one('hr.employee', string='Employee')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('work_order_id')
    def onchange_wo(self):
        if self.work_order_id:
            self.start_date = self.work_order_id.start_date
            self.break_date = self.work_order_id.break_date
            self.end_break_date = self.work_order_id.end_break_date
            self.finish_date = self.work_order_id.finish_date
        else:
            self.start_date = False
            self.break_date = False
            self.end_break_date = False
            self.finish_date = False

    # 12: override methods

    def action_start_clocking(self):
        tgl_start = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for record in self:
            if record.work_order_id.finish_date:
                raise ValidationError("Clocking telah selesai. Silakan refresh halaman ini")
            # Confirm will trigger create picking, temporarily state 'sale' then 'approved'
            # record.work_order_id.action_confirm()
            # TODO: Sesuaikan state, jika install approval maka approved, jika tidak maka 'draft'
            state = 'approved'
            record.work_order_id.write({
                'state':state,
                'state_wo': 'in_progress',
                'start_date': tgl_start,
                'start_uid': self.env.uid,
                'mechanic_id': record.mechanic_id.id
            })
            record.write({
                'start_date': tgl_start,
                'start_uid': self.env.uid,
                'break_date': record.work_order_id.break_date,
                'break_uid': record.work_order_id.break_uid,
                'end_break_date': record.work_order_id.end_break_date,
                'end_break_uid': record.work_order_id.end_break_uid,
                'finish_date': record.work_order_id.finish_date,
                'finish_uid': record.work_order_id.finish_uid
            })
        return True

    def action_break_clocking(self):
        tgl_break = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for record in self:
            if record.work_order_id:
                if record.work_order_id.finish_date:
                    raise ValidationError('Gagal Break. Silakan refresh halaman ini karena Clocking telah selesai')
                else:
                    record.work_order_id.write({
                        'state_wo': 'break',
                        'break_date': tgl_break,
                        'break_uid': self.env.uid
                    })
                    record.write({
                        'break_date': tgl_break,
                        'break_uid': self.env.uid,
                        'start_date': record.work_order_id.start_date,
                        'start_uid': record.work_order_id.start_uid,
                        'end_break_date': record.work_order_id.end_break_date,
                        'end_break_uid': record.work_order_id.end_break_uid,
                        'finish_date': record.work_order_id.finish_date,
                        'finish_uid': record.work_order_id.finish_uid
                    })
        return True

    def action_end_break_clocking(self):
        tgl_end_break_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S') #format dari time menjadi datetime
        for record in self:
            if record.work_order_id: 
                if not record.work_order_id.break_date:
                    raise ValidationError('Gagal End Break karena Break belum dilakukan')            
                if record.work_order_id.break_date and not record.work_order_id.finish_date:
                    record.work_order_id.write({
                        'state_wo': 'in_progress',
                        'end_break_date': tgl_end_break_date,
                        'end_break_uid': self.env.uid
                    })
                    record.write({
                        'end_break_date': tgl_end_break_date,
                        'end_break_uid': self.env.uid,
                        'start_date': record.work_order_id.start_date,
                        'start_uid': record.work_order_id.start_uid,
                        'break_date': record.work_order_id.break_date,
                        'break_uid': record.work_order_id.break_uid,
                        'finish_date': record.work_order_id.finish_date,
                        'finish_uid': record.work_order_id.finish_uid
                    })
        return True

    def action_finish_clocking(self):       
        tgl_finish = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for record in self:
            if record.work_order_id:
                if record.work_order_id.finish_date and record.work_order_id.finish_date < record.work_order_id.start_date:
                    raise ValidationError("Waktu selesai pengerjaan tidak boleh lebih kecil daripada waktu mulai. Periksa kembali data Anda!")
                # Check picking state, atau jika tidak ada picking
                state = 'finished'
                record.work_order_id.write({
                    'state': state,
                    'state_wo': 'finish',
                    'finish_date': tgl_finish,
                    'finish_uid': self.env.uid
                })
                record.write({
                    'finish_date': tgl_finish,
                    'finish_uid': self.env.uid,
                    'start_date': record.work_order_id.start_date,
                    'start_uid': record.work_order_id.start_uid,
                    'break_date': record.work_order_id.break_date,
                    'break_uid': record.work_order_id.break_uid,
                    'end_break_date': record.work_order_id.end_break_date,
                    'end_break_uid': record.work_order_id.end_break_uid
                })
        return True

class TwStartStopWo(models.Model):    
    _inherit = "tw.work.order"

    # 7: defaults methods

    # 8: fields
    state_wo = fields.Selection([('in_progress','In Progress'),('break','Break'),('finish','Finish')], 'State WO', readonly=True)

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods