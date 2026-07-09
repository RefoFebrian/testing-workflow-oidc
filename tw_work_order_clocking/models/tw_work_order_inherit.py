# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwWorkOrder(models.Model):
    _inherit = "tw.work.order"

    # 7: defaults methods

    # 8: fields
    start_date = fields.Datetime(string='Start', readonly=True)
    start_uid = fields.Many2one('res.users', string='Start by', readonly=True)
    break_date = fields.Datetime(string='Break', readonly=True)
    break_uid = fields.Many2one('res.users', string='Break by', readonly=True)
    end_break_date = fields.Datetime(string='End Break', readonly=True)
    end_break_uid = fields.Many2one('res.users', string='End Break by', readonly=True)
    finish_date = fields.Datetime(string='Finish', readonly=True)
    finish_uid = fields.Many2one('res.users', string='Finish by', readonly=True)
    duration = fields.Float(
        'Clocking Duration (Minute)', compute='_compute_duration',
        readonly=False, copy=False)
    duration_stored = fields.Float(
        'Real Duration')
    state = fields.Selection(selection_add=[
        ('draft',),
        ('sent',),
        ('confirmed',),
        ('finished','Finished'),
        ('sale',),
        ('except_picking',),
        ('except_invoice',),
        ('done',),
        ('unused',),
        ('cancel',),
        ('rejected', 'Rejected'),
    ])

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('state')
    def _compute_is_other_module_installed(self):
        if self.env['ir.module.module'].search([('name', '=', 'tw_work_order_approval')], limit=1).state == 'installed':
            for rec in self:
                rec.is_other_module_installed = True
        else:
            for rec in self:
                rec.is_other_module_installed = False
    
    @api.depends('state','state_wo')
    def _compute_is_invisible_action_by_state(self):
        # Approval
        state = 'approved' 
        # Clocking 
        state_dict = {
            'state_list':'draft',
            'state_wo_list':''
        }    
        state_dict = self._prepare_invisible_action_start_stop_wo(state_dict)
        for rec in self:
            state_keys = [key for key, _ in rec._fields['state'].selection]            
            rec.is_invisible_action_invoice_create = rec.state != rec._prepare_invisible_action_invoice_create_state(state)
            rec.is_invisible_action_start_stop_wo = (
                rec.state != state_dict['state_list']
            ) or (rec.state_wo == 'finish')
            # TODO: Make Sure in another module
            rec.is_invisible_action_open = True

    def _convert_to_duration(self, date_start, date_stop):
        """ Convert a date range into a duration in minutes. """
        duration = (date_stop - date_start).total_seconds() / 60.0
        return round(duration, 2)

    @api.depends('start_date', 'break_date', 'end_break_date', 'finish_date')
    def _compute_duration(self):
        now = datetime.now()
        for record in self:
            # Belum mulai clocking
            if not record.start_date:
                record.duration = 0.0
                record.duration_stored = 0.0
                continue

            start = record.start_date.replace(microsecond=0)

            # Tentukan titik akhir perhitungan
            if record.finish_date:
                # Clocking selesai → hitung sampai finish
                end = record.finish_date.replace(microsecond=0)
            elif record.break_date and not record.end_break_date:
                # Sedang break → hitung sampai break dimulai (timer freeze)
                end = record.break_date.replace(microsecond=0)
            else:
                # Sedang kerja (belum break / sudah selesai break) → hitung sampai sekarang
                end = now.replace(microsecond=0)

            duration = record._convert_to_duration(start, end)

            # Kurangi durasi break jika break sudah selesai
            if record.break_date and record.end_break_date:
                break_duration = record._convert_to_duration(
                    record.break_date.replace(microsecond=0),
                    record.end_break_date.replace(microsecond=0)
                )
                duration -= break_duration

            record.duration = max(duration, 0.0)
            record.duration_stored = record.duration

    # 12: override methods
    def action_supply(self):
        """Override to block supply product if clocking hasn't started."""
        if not self.start_date:
            raise ValidationError(_("Tidak dapat Supply Product sebelum Start Clocking. Silakan klik 'Start Stop WO' terlebih dahulu."))
        supply = super(TwWorkOrder, self).action_supply()
        if not self.state_wo:
            self.write({
                'state':'approved',
                'state_wo':'in_progress',
            })
        return supply
        
        

    def action_clocking_reset(self):
        self.write({
            'state_wo':'in_progress', 
            'start_date':False,
            'break_date': False,
            'end_break_date':False,
            'finish_date':False 
        })

    def action_start_stop_wo(self):
        self.ensure_one()
        start_stop_wo_obj = self.env['tw.start.stop.wo'].search([('work_order_id', '=', self.id)], order='id desc', limit=1)
        view = self.env.ref('tw_work_order_clocking.tw_start_stop_wo_form_view')
        return {
            'name': ('Start / Stop Work Order'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'tw.start.stop.wo',
            'view_id': view.id,
            'target': 'new',
            'context': {
                'default_id': start_stop_wo_obj.id if start_stop_wo_obj else False,
                'default_company_id': start_stop_wo_obj.company_id.id if start_stop_wo_obj else self.company_id.id,
                'default_work_order_id': start_stop_wo_obj.work_order_id.id if start_stop_wo_obj else self.id,
                'default_mechanic_id': start_stop_wo_obj.mechanic_id.id if start_stop_wo_obj else self.mechanic_id.id,
            }
        }

    def _get_clocking(self):
        clocking = self.env['tw.start.stop.wo'].search([('work_order_id', '=', self.id)], order='id desc', limit=1)
        if not clocking:
            raise ValidationError("Clocking not found")
        return clocking

    def button_start(self):
        return self.action_start_stop_wo()

    def button_break(self):
        return self._get_clocking().action_break_clocking()

    def button_end_break(self):
        return self._get_clocking().action_end_break_clocking()

    def button_finish(self):
        return self._get_clocking().action_finish_clocking()

    def get_duration(self):
        return self.duration
    
    def _prepare_update_vals(self,update_vals,line):
        tgl_break = fields.Datetime.now()
        if line.division in ['Sparepart', 'Service']:
            update_vals.update({'state_wo': 'break', 'break_date': tgl_break})
        return update_vals
    
    # Invisible/Readonly/Required View
    def _prepare_invisible_action_invoice_create_state(self,state):
        if state == 'approved':
            state = 'finished'
        return state
    
    def _prepare_invisible_action_start_stop_wo(self,state_dict):
        if 'finish' not in state_dict['state_wo_list']:
            state_dict['state_wo_list'] = 'finish'

        prepare = super()._prepare_invisible_action_start_stop_wo(state_dict)
        return prepare
    
    def _update_state_wo(self):
        work_orders_to_update = []
        for wo in self:
            for line in wo.order_line:
                if int(line.product_qty) <= 0:
                    raise ValidationError("Product Qty tidak boleh 0 !")
                if line.state == 'draft' and wo.state != 'sale':
                    update_vals = {'state': 'draft'}
                    # TODO: Butuh penyesuaian jika ingin digunakan secara modular
                    # wo._prepare_update_vals(update_vals,line)
                    work_orders_to_update.append((wo, update_vals))
        return work_orders_to_update

    @api.depends('state', 'order_line.invoice_status')
    def _compute_invoice_status(self):            
        """
        Compute the invoice status of a SO. Possible statuses:
        - no: if the SO is not in status 'finished' or 'done', we consider that there is nothing to
        invoice. This is also the default value if the conditions of no other status is met.
        - to invoice: if any SO line is 'to invoice', the whole SO is 'to invoice'
        - invoiced: if all SO lines are invoiced, the SO is invoiced.
        - upselling: if all SO lines are invoiced or upselling, the status is upselling.
        """
        # TODO: Override this on another module becuase this method is chekcing finished state
        confirmed_orders = self.filtered(lambda so: so.state == 'finished')
        (self - confirmed_orders).invoice_status = 'no'
        if not confirmed_orders:
            return
        lines_domain = [('is_downpayment', '=', False), ('display_type', '=', False)]
        line_invoice_status_all = [
            (order.id, invoice_status)
            for order, invoice_status in self.env['tw.work.order.line']._read_group(
                lines_domain + [('order_id', 'in', confirmed_orders.ids)],
                ['order_id', 'invoice_status']
            )
        ]        
        for order in confirmed_orders:
            line_invoice_status = [d[1] for d in line_invoice_status_all if d[0] == order.id]
            if order.state != 'finished':
                order.invoice_status = 'no'
            elif any(invoice_status == 'to invoice' for invoice_status in line_invoice_status):
                if any(invoice_status == 'no' for invoice_status in line_invoice_status):
                    # If only discount/delivery/promotion lines can be invoiced, the SO should not
                    # be invoiceable.
                    invoiceable_domain = lines_domain + [('invoice_status', '=', 'to invoice')]
                    invoiceable_lines = order.order_line.filtered_domain(invoiceable_domain)
                    special_lines = invoiceable_lines.filtered(
                        lambda sol: not sol._can_be_invoiced_alone()
                    )
                    if invoiceable_lines == special_lines:
                        order.invoice_status = 'no'
                    else:
                        order.invoice_status = 'to invoice'
                else:
                    order.invoice_status = 'to invoice'
            elif line_invoice_status and all(invoice_status == 'invoiced' for invoice_status in line_invoice_status):
                order.invoice_status = 'invoiced'
            elif line_invoice_status and all(invoice_status in ('invoiced', 'upselling') for invoice_status in line_invoice_status):
                order.invoice_status = 'upselling'
            else:
                order.invoice_status = 'no'
