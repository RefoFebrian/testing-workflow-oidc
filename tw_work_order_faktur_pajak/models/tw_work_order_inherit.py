# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, timedelta
import pytz

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwWorkOrder(models.Model):
    """
    Inherit Work Order untuk menambahkan fitur Faktur Pajak.
    Field is_combined_tax dan faktur_pajak_out_id sudah ada dari mixin.
    """
    _name = "tw.work.order"
    _inherit = ["tw.work.order", "tw.faktur.pajak.mixin"]

    # 7: defaults methods

    # 8: fields
    # Override is_combined_tax dengan nama field yang berbeda untuk backward compat
    combined_tax = fields.Boolean(string='Faktur Pajak Gabungan', copy=False, readonly=True)
    state_fpo = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('error', 'Error')
    ], string='State Faktur Pajak WO', help='Untuk Handle Proses Generate Faktur Pajak WO', default='draft')

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    def get_faktur_pajak_for_wo(self, state_fpo='draft', limit=5):
        """
        Batch process untuk generate faktur pajak untuk Work Orders.
        """
        domain = [
            ('state', 'in', ('sale', 'done')),
            ('faktur_pajak_out_id', '=', False),
            ('combined_tax', '=', False),
        ]
        
        if state_fpo == 'draft':
            domain.append('|')
            domain.append(('state_fpo', '=', 'draft'))
            domain.append(('state_fpo', '=', False))
        elif state_fpo == 'error':
            domain.append(('state_fpo', '=', 'error'))
        
        work_orders = self.search(domain, limit=limit, order='id desc')
        if not work_orders:
            return False
        
        success_ids, error_ids = [], []
        for wo in work_orders:            
            fpo = wo.get_number_faktur_pajak()
            if fpo:
                success_ids.append(wo.id)
            else:
                error_ids.append(wo.id)
        
        if success_ids:
            self.browse(success_ids).write({'state_fpo': 'done'})
        if error_ids and state_fpo != 'error':
            self.browse(error_ids).write({'state_fpo': 'error'})
        
        return True
    
    # This method is overrided in TW Work Order KPB and Claim (should depend on this module)
    def _get_combined_tax(self, vals):
        workorder_type_obj = self.env['tw.selection'].browse(vals.get('type_id'))
        if workorder_type_obj:  
            if workorder_type_obj.value in ('REG', 'WAR', 'SLS'):
                vals['combined_tax'] = False
            elif workorder_type_obj.value in ('KPB', 'CLA', 'PDI'):
                vals['combined_tax'] = True
    
    def action_register_faktur_pajak(self):
        """
        Manual action untuk register faktur pajak pada Work Order.
        """
        wo_id = self
        if wo_id.state in ('sale', 'done') and not wo_id.faktur_pajak_out_id and not wo_id.combined_tax and (wo_id.state_fpo == 'draft' or not wo_id.state_fpo):
            obj_faktur = wo_id.get_number_faktur_pajak()
            if obj_faktur:
                wo_id.write({'state_fpo': 'done'})
        return True

    def action_generate_faktur_pajak_wo_current_month(self):
        message = []
        today = date.today()
        wo_ids = self.env['tw.work.order'].sudo().search([
            ('state', 'in', ('sale','done')),
            ('faktur_pajak_out_id', '=', False),
            ('is_combined_tax', '=', False),
            ('date', '>=', today.replace(day=1))
        ], limit=30)
        
        if not wo_ids:
            raise Warning('WO tanpa faktur pajak tidak ditemukan!')

        for wo in wo_ids:
            faktur = wo.get_number_faktur_pajak()
            if faktur:
                message.append('Faktur pajak untuk WO %s berhasil!' % wo.name)
            else:
                message.append('Faktur pajak untuk WO %s gagal!' % wo.name)
        
        return '\n'.join(message)
