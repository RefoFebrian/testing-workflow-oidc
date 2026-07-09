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

class TwApprovalLine(models.Model):
    _name = "tw.approval.line"
    _description = "Approval Line : Line of approvals on the transaction"

    # 7: defaults methods
        
    def _get_groups(self):
        x = self.env['res.users'].browse(self._uid)['groups_id']
        #is self.group_id in x ?
        self.is_mygroup = self.group_id in x 
    
    def _cek_groups(self,operator,value):
         
        group_ids = self.env['res.users'].browse(self._uid)['groups_id']
         
        if operator == '=' and value :
            where = [('group_id', 'in', [x.id for x in group_ids])]
        else :
            where = [('group_id', 'not in', [x.id for x in group_ids])]
 
        return where

    # 8: fields
    tanggal = fields.Datetime('Tanggal')
    transaction_id = fields.Integer('Transaction ID')
    value = fields.Float('Value',digits=(12,2))
    limit = fields.Float('Limit', digits=(12,2))
    state = fields.Selection([('open','Belum Approve'),('approve','Approve'),('reject','Reject'),('cancel','Cancel')],'Status')
    
    info = fields.Char('Other Info')
    transaction_no = fields.Char(string="Transaction No")
    view_name = fields.Char('View Name')
    approval_type = fields.Selection(string='Approval Type', selection=[('sequential', 'Sequential'), ('simultaneous', 'Simultaneous'),])
    reason = fields.Text('Reason')
    
    is_mygroup = fields.Boolean(compute='_get_groups', string="is_mygroup", search='_cek_groups')
    is_mandatory_approve = fields.Boolean(string="Mandatory Approve?", help="Jika terceklis maka Group dengan mandatory harus approve terlebih dahulu")
    is_must_approve = fields.Boolean(string="Must Approve?", help="Line minimum dalam 1 transaksi untuk dapat di approve. (Line pertama yang Limitnya lebih besar dari value)")
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())

    # 9: relation fields
    company_id = fields.Many2one('res.company','Branch', domain="[('parent_id', '!=', False)]")
    config_id = fields.Many2one('tw.approval.config','Form',ondelete='set null')
    model_id = fields.Many2one('ir.model','Model',ondelete='set null')
    group_id = fields.Many2one('res.groups','Group', index=True)
    approver_id = fields.Many2one('res.users','Pelaksana')
    product_tmpl_id = fields.Many2one('product.template',string='Product Template')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
    
    def find_one2many_fields(self, model_obj):
        one2many_fields = []
        for field_name, field in model_obj._fields.items():
            if isinstance(field, fields.One2many):
                one2many_fields.append(field_name)
        filtered_list = [item for item in one2many_fields if any(substring in item for substring in ('line', 'detail_ids', 'item'))]
        line_ids = getattr(model_obj, filtered_list[0])
        return line_ids

    
    def action_mass_approve(self):
        """Mass approve selected approval lines from portal list view."""
        approved = []
        failed = []

        # Group approval lines by transaction to avoid approving the same transaction multiple times
        processed_transactions = set()
        for line in self:
            trx_key = (line.model_id.model, line.transaction_id)
            if trx_key in processed_transactions:
                continue
            processed_transactions.add(trx_key)

            try:
                trx_obj = self.env[line.model_id.model].browse(line.transaction_id)
                if not trx_obj.exists():
                    failed.append(f"{line.transaction_no}: Transaksi tidak ditemukan")
                    continue
                trx_obj.action_approval()
                approved.append(line.transaction_no)
            except Exception as e:
                failed.append(f"{line.transaction_no}: {e}")

        message_parts = []
        if approved:
            message_parts.append(f"Berhasil approve: {', '.join(approved)}")
        if failed:
            message_parts.append(f"Gagal approve:\n" + '\n'.join(failed))

        message = '\n\n'.join(message_parts) if message_parts else 'Tidak ada transaksi yang diproses.'
        msg_type = 'success' if not failed else ('warning' if approved else 'danger')

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Mass Approval',
                'message': message,
                'type': msg_type,
                'sticky': bool(failed),
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }

    def action_open_reference(self):  
        obj_ir_view = self.env["ir.ui.view"]
        if self.view_name :
            obj_ir_view_browse = obj_ir_view.search([("name", "=", self.view_name), ("model", "=", self.model_id.model)])       
        else:
            obj_ir_view_browse = obj_ir_view.search([("model", "=", self.model_id.model),('type','=','form')],order="priority", limit=1)
        return {
            'name': self.model_id.name,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self.model_id.model,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'res_id': self.transaction_id,
            'view_id':obj_ir_view_browse.id
        }