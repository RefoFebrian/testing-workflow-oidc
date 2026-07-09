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

class TwApprovalCopy(models.TransientModel):
    _name = "tw.approval.copy"
    _description = "Copy Approval"
    _rec_name = "approval_type"

    def _get_form(self):
        form_ids = self.env['tw.approval.config'].search([], order='name')
        selection = [('all','All')]
        for form_id in form_ids :
            selection.append((str(form_id.id),form_id.name))
        return selection

    approval_type = fields.Selection([('all', 'All'), ('matrix_biaya', 'Approval Matrix Biaya'), ('matrix_discount', 'Approval Matrix Discount')], default='all', string='Approval Type')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())

    branch_from_id = fields.Many2one(comodel_name='res.company', domain="[('parent_id', '!=', False)]", string="Branch from")
    branch_to_id = fields.Many2one(comodel_name='res.company', domain="[('parent_id', '!=', False)]", string="Branch to")
    form_id = fields.Selection(_get_form, string='Form')

    _defaults = {
        'approval_type': 'all',
        'form_id': 'all',
        'division': 'all'
    }

    def create_approval_matrix(self, biaya_header_ids, division, branch_to_id):
        if biaya_header_ids:
            obj_biaya_header = self.env['tw.approval.matrix']
            search_division = ('division', '!=', False)
            if division != 'all':
                search_division = ('division', '=', division)

            for biaya_header_id in biaya_header_ids:
                # Unlink old approval in the target branch
                obj_biaya_header.search([
                    ('company_id', '=', branch_to_id.id),
                    ('form_id', '=', biaya_header_id.id), 
                    search_division
                ]).unlink()
                
                # Search matrices from the source branch
                check_approval = obj_biaya_header.search([
                    ('company_id', '=', self.branch_from_id.id),
                    ('form_id', '=', biaya_header_id.id), 
                    search_division
                ])

                if check_approval:
                    for approval in check_approval:
                        # Prepare lines manually
                        line_values = []
                        for line in approval.approval_line:
                            line_values.append((0, 0, {
                                'limit': line.limit,
                                'is_mandatory_approve': line.is_mandatory_approve,
                                'is_retain_approval': line.is_retain_approval,
                                'group_id': line.group_id.id,
                            }))
                        
                        # Copy matrix and its lines explicitly
                        approval.sudo().copy({
                            'company_id': branch_to_id.id,
                            'approval_line': line_values
                        })
                else:
                    raise Warning("Perhatian! \n Tidak ditemukan Approval Matrix untuk Form dan Division yang dipilih!")

    def action_copy(self):
        search_form_id = ('model_id','!=',False)
        if self.form_id != 'all' :
            search_form_id = ('id','=',int(self.form_id))

        if self.approval_type == 'matrix_biaya' or self.approval_type == 'all' :
            obj_biaya_header = self.env['tw.approval.config']
            biaya_header_ids = obj_biaya_header.search([search_form_id,('type','=','biaya')])
            self.create_approval_matrix(biaya_header_ids, self.division, self.branch_to_id)
        if self.approval_type == 'matrix_discount' or self.approval_type == 'all' :
            obj_disc_header = self.env['tw.approval.config']
            disc_header_ids = obj_disc_header.search([search_form_id,('type','=','discount')])
            self.create_approval_matrix(disc_header_ids, self.division, self.branch_to_id)
