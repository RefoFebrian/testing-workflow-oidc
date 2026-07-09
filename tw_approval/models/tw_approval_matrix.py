# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning,ValidationError
from psycopg2 import OperationalError

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib


class TwApprovalMatrix(models.Model):
    _name = "tw.approval.matrix"
    _inherit = ['mail.thread']
    _description = 'Approval Matrix'

    # 7: defaults methods
    def get_default_datetime(self):
        return datetime.now()
    
    # 8: fields
    name = fields.Char(string="Name")
    date = fields.Date(string="Date",default=get_default_datetime)
    config_type = fields.Char('Form Code')
    applied_on = fields.Selection([
        ('all', 'All'),
        ('product', 'Product'),
        ('product_category', 'Product Category'),
    ],string="Applied On", default="all")
    approval_type = fields.Selection([
        ('sequential', 'Harus Urutan'),
        ('simultaneous', 'Bisa Loncat')
    ],string="Approval Type", default="simultaneous")
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())

    # 9: relation fields
    company_id = fields.Many2one(comodel_name='res.company', string="Branch")
    form_id = fields.Many2one(comodel_name='tw.approval.config', string="Form")
    product_tmpl_id = fields.Many2one('product.template',string='Product Template')
    approval_line = fields.One2many('tw.approval.matrix.line', 'header_id', string="Approval Lines")
    department_id = fields.Many2one('hr.department', string='Departemen')
    product_id = fields.Many2one('product.product', string='Product')
    categ_id = fields.Many2one('product.category', string='Category')
    
    # 10: constraints & sql constraints
    @api.constrains('division','company_id','form_id','product_tmpl_id','department_id','product_id','categ_id')
    def _check_unique_approval_matrix(self):
        for record in self:
            domain = [
                ('division', '=', record.division),
                ('company_id', '=', record.company_id.id),
                ('form_id', '=', record.form_id.id),
                ('id', '!=', record.id)
            ]
            if record.product_tmpl_id:
                domain += [('product_tmpl_id', '=', record.product_tmpl_id.id)]
            else:
                domain += [('product_tmpl_id', '=', False)]

            if record.department_id:
                domain += [('department_id', '=', record.department_id.id)]
            else:
                domain += [('department_id', '=', False)]
            
            if record.product_id:
                domain += [('product_id', '=', record.product_id.id)]
            else:
                domain += [('product_id', '=', False)]
            
            if record.categ_id:
                domain += [('categ_id', '=', record.categ_id.id)]
            else:
                domain += [('categ_id', '=', False)]
            
            if self.search_count(domain) > 0:
                raise ValidationError(
                    _("An approval matrix with the same 'division, branch, form, categ, variant, and product' combination already exists.")
                )

    # 11: compute/depends & on change methods
    @api.onchange('form_id')
    def _onchange_form_id(self):
        if self.form_id:
            self.config_type = self.form_id.type
        else:
            self.config_type = False

    @api.onchange('division')
    def _onchange_division(self):
        if self.division != 'Unit':
            self.applied_on = 'all'

    @api.onchange('applied_on')
    def _onchange_applied_on(self):
        self.product_tmpl_id = False
        self.product_id = False
        self.categ_id = False

    @api.onchange('product_tmpl_id')
    def _onchange_product_tmpl_id(self):
        if self.product_tmpl_id:
            self.product_id = False

    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list):
        create = super(TwApprovalMatrix, self).create(vals_list)
        return create 

    def write(self,vals):
        approval = super(TwApprovalMatrix,self).write(vals)
        self.sudo().message_post(body="Approval updated ") 
        return approval

    # 13: action methods

    # 14: private methods

    # 14: private methods
    def request(self,trx, subject_to_approval,code='other',view_name=None):
        try:
            field_test = trx[subject_to_approval]
        except:
            raise Warning("Perhatian ! Transaksi ini tidak memiliki field %s. Cek kembali Matrix Approval.")%(subject_to_approval)
        return self.request_by_value(trx,trx[subject_to_approval],code,view_name)
    
    def request_by_value(self,trx,value,code='other', **kwargs):
        company_id = kwargs.get('company_id') or trx.company_id if 'company_id' in trx.read()[0] else False 
        if not company_id:
            company_id = trx.company_id if 'company_id' in trx.read()[0] else False
        if not company_id:
            company_id = self.env.company
        config_obj = self.env['tw.approval.config'].search([('model_id','=',trx.__class__.__name__),('code','=',code)])
        if not config_obj :
            raise Warning("Perhatian ! Transaksi %s (%s) dengan code %s tidak memiliki Approval Configuration !"%(trx._description, trx.__class__.__name__,code.strip() or '-'))
        if config_obj.type == 'discount' and not kwargs.get('product_tmpl_id'):
            raise Warning("Perhatian ! Pilih produk terlebih dahulu untuk mencari matrix approval.")
        
        if not 'name' in trx.read()[0]:
            raise Warning("Perhatian ! Transaksi ini tidak memiliki field nama, silahkan hubungi IT Support atau Helpdesk.")

        division = self.env['tw.selection'].get_division(trx)
        domain = [
            '|',('department_id','=',kwargs.get('department_id')),
            ('department_id','=',False),
            ('division','=',division),
            ('form_id','=',config_obj.id),
            '|',
            ('company_id','=',company_id.id),
            ('company_id','=',company_id.parent_id.id)
        ]

        # DSO Discount, prioritizing product, template, then category matrix approval
        # Build search priorities dynamically: only include a priority if the
        # corresponding kwarg was actually provided, so that a missing value
        # does not accidentally match generic (False) records.
        search_priorities = []

        if kwargs.get('product_id'):
            search_priorities.append([('product_id', '=', kwargs['product_id'])])

        if kwargs.get('product_tmpl_id'):
            """
            Prioritaskan yang punya product_id dulu, 
            kalau tidak ada, maka cari yang product_id False
            Misal: 
            Unit Beat CBS (BK-Red) tidak ada pada Matrix Approval,
            maka approval line yang digenerate nantinya dari product_tmpl_id Beat CBS
            walaupun pada Matrix Approval terdapat product_id Beat CBS (BK)
            """
            search_priorities.append([
                ('product_tmpl_id', '=', kwargs['product_tmpl_id']),
                '|',
                ('product_id','=',kwargs['product_id']),
                ('product_id','=',False)
            ])

        if kwargs.get('categ_id'):
            search_priorities.append([('categ_id', 'child_of', kwargs['categ_id'])])

        # Fallback: no product/template/category filter (generic matrix)
        search_priorities.append([
            ('product_id', '=', False),
            ('product_tmpl_id', '=', False),
            ('categ_id', '=', False),
        ])

        header_matrix = False

        for priority in search_priorities:
            header_matrix = self.search(domain + priority, order="product_tmpl_id,company_id", limit=1)
            if header_matrix:
                break
        data = self.env['tw.approval.matrix.line'].search([
            ('header_id','=',header_matrix.id),
        ],order="limit,id asc")
        
        if not data:
            raise Warning(
                (f"""Perhatian !\n\nTransaksi ini tidak memiliki matrix approval. Cek kembali data Cabang & Divisi.
                 \nMohon Buat Matrix Approval Dengan Detail:
                 \nDivision : {division}
                 \nForm : {config_obj[0].name}
                 \nCode : {config_obj.code}"""
                )
            )

        is_must_approve = 0
        user_limit = 0
        for record in data :
            state = 'open'
            approver_id = False
            tanggal = False
            reason = False
            
            if record.is_retain_approval:
                prev_line = self.env['tw.approval.line'].search([
                    ('transaction_id', '=', trx.id),
                    ('model_id', '=', record.header_id.form_id.model_id.id),
                    ('division', '=', record.header_id.division),
                    ('group_id', '=', record.group_id.id),
                    ('state', '=', 'approve')
                ], limit=1, order='id desc')
                
                if prev_line:
                    state = 'approve'
                    approver_id = prev_line.approver_id.id
                    tanggal = datetime.now()
                    reason = "Auto Approved (Retained from previous approval)"

            # Jika simultaneous, maka line dengan limit cukup pertama yg jadi must approve yang masih open
            if record.header_id.approval_type == 'simultaneous':
                if not is_must_approve and value <= record.limit and state == 'open':
                    is_must_approve = record.id
            # Jika sequential, maka line pertama yg jadi must approve yang masih open
            elif record.header_id.approval_type == 'sequential':
                if not is_must_approve and state == 'open':
                    is_must_approve = record.id

            vals =  {
                'transaction_no': trx.name,
                'value': value,
                'approval_type': record.header_id.approval_type,
                'config_id': config_obj.id,
                'group_id': record.group_id.id,
                'transaction_id': trx.id,
                'division': record.header_id.division,
                'model_id': record.header_id.form_id.model_id.id,
                'limit': record.limit,
                'state': state,
                'is_must_approve': True if record.id == is_must_approve else False,
                'is_mandatory_approve': record.is_mandatory_approve,
                'view_name': kwargs.get('view_name')
                }
            
            if approver_id:
                vals['approver_id'] = approver_id
            if tanggal:
                vals['tanggal'] = tanggal
            if reason:
                vals['reason'] = reason

            if company_id:
                vals['company_id'] = company_id.id

            self.env['tw.approval.line'].create(vals)

            if config_obj.type == 'biaya':
                user_limit = max(user_limit, record.limit)
            elif config_obj.type == 'discount':
                user_limit = min(user_limit, record.limit)
            
            # Jika limit master approval
            if record.limit >= value:
                if record.header_id.approval_type == 'sequential':
                    break
        
        is_limit_sufficient = True
        if self.config_type == 'biaya':
            if user_limit < value:
                is_limit_sufficient = False
        elif self.config_type == 'discount':
            if user_limit > value:
                is_limit_sufficient = False
        if not is_limit_sufficient:
            raise Warning((f"Nilai transaksi {value}. Nilai terkecil di matrix approval: {user_limit}. Cek kembali Matrix Approval."))

        return True
    
    def approve(self, trx, user_id=None):
        uid = user_id if user_id else self._uid
        user_groups = self.env['res.users'].browse(uid)['groups_id']
        config = self.env['tw.approval.config'].search([('model_id','=',trx.__class__.__name__),],limit=1)
        if not config :
            raise Warning("Perhatian ! Form ini tidak memiliki approval configuration")
        division = self.env['tw.selection'].get_division(trx)
        # Get transaction Approval lines
        approval_ids = self.env['tw.approval.line'].search([
            ('division','=',division),
            ('model_id','=',config.model_id.id),
            ('transaction_id','=',trx.id),
            ('state', '=', 'open')
        ],order="limit asc")
        
        outstanding_approval_ids = approval_ids
        # Jika tidak ada outstanding approval, padahal state blm approve, pastikan dulu tidak ada yang janggal
        if not outstanding_approval_ids:
            # recheck approval line (In case approval line not generated)
        
            outstanding_approval_ids = self.env['tw.approval.line'].search([
                ('division','=',division),
                ('model_id','=',config.model_id.id),
                ('transaction_id','=',trx.id),
            ],order="limit desc")
            if not outstanding_approval_ids:
                raise Warning('Perhatian ! Transaksi ini tidak memiliki detail approval. Cek kembali Matrix Approval.')
            # Else, it was all approved. GJ :)
            else:
                # All approval lines Approved
                return 1
        
        # Jika sudah approve 1x, tidak bisa approve lagi (Cek by create_date approval line nya, jika sama maka berarti sudah pernah approve)
        approved_by_user_lines = approval_ids.filtered(lambda  apl : apl.approver_id.id == uid and apl.state == 'approve')
        if approved_by_user_lines:
            dates = [app.create_date for app in outstanding_approval_ids]
            max_date = max(dates)
            for approved_line in approved_by_user_lines:
                if approved_line.create_date == max_date:
                    return 0

        to_approve_line = self.env['tw.approval.line']
        # Check approval type, since the behavior is different
        if outstanding_approval_ids[0].approval_type == 'sequential':
            for approval_line in outstanding_approval_ids:
                # Check if User have Group in Approval Line
                if approval_line.group_id in user_groups:
                    to_approve_line += approval_line
                    next_approvals = outstanding_approval_ids.filtered(lambda  apl : apl.state == 'open' and apl.id != approval_line.id)
                    if next_approvals:
                        next_approval = next_approvals[0]
                        next_approval.is_must_approve = True
                    break
        elif outstanding_approval_ids[0].approval_type == 'simultaneous':
            # Urutkan dulu berdasarkan limit tertinggi supaya bisa approve semua langsung
            outstanding_approval_ids = outstanding_approval_ids.sorted(
                key=lambda a: a.limit,
                reverse=True
            )
            exclude_mandatory_approve = outstanding_approval_ids.filtered(lambda  apl : apl.is_mandatory_approve and apl.state == 'open')
            ex_outstanding_approval_ids = outstanding_approval_ids - exclude_mandatory_approve
            for approval_line in outstanding_approval_ids:
                if approval_line.group_id in user_groups:
                    # Jika limit nya sudah lebih besar dari value yang akan di approve, approve semua
                    if exclude_mandatory_approve:
                        # Check if User have Group in Mandatory Approve
                        for data in exclude_mandatory_approve:
                            if data.group_id in user_groups:
                                to_approve_line += data
                    if approval_line.limit >= approval_line.value:
                        to_approve_line += ex_outstanding_approval_ids
                    else:
                        # Get all approval line that the limit lower than current looped line
                        to_approve_line += ex_outstanding_approval_ids.filtered(lambda  apl : apl.limit <= approval_line.limit)
                    break  
        
        # If none of the approvals match the user groups, return 0 (No approval line can be processed).
        if not to_approve_line:
            return 0
        
        # Write Approve to all
        to_approve_line.suspend_security().write({
            'state':'approve',
            'approver_id':uid,
            'tanggal':datetime.now(),
        })

        # Check if all lines are approved
        approval_open = [app.id for app in outstanding_approval_ids if app.state == 'open']
        if not approval_open:
            # All approval lines Approved
            return 1
        else:
            # Approved Partialy
            return 2

    
    def reject(self, trx, reason,user_id=None):
        uid = user_id if user_id else self._uid
        user_groups = self.env['res.users'].suspend_security().search([('id','=',uid)]).groups_id
        config_brw = self.env['tw.approval.config'].search([('model_id','=',trx.__class__.__name__)])
        if not config_brw :
            raise Warning("Perhatian ! Form ini tidak memiliki approval configuration")   

        division = self.env['tw.selection'].get_division(trx)

        approval_lines = self.env['tw.approval.line'].search([
            ('division','=',division),
            ('model_id','=',config_brw[0].model_id.id),
            ('transaction_id','=',trx.id),
        ],order="limit asc")
            
        if not approval_lines:
            raise Warning("Perhatian ! Transaksi ini tidak memiliki detail approval. Cek kembali Matrix Approval.")
        reject_all = False
        for approval_line in approval_lines:
            if approval_line.state == 'open':
                if approval_line.group_id in user_groups:
                    reject_all = True
                    approval_line.write({
                        'state':'reject',
                        'reason':reason,
                        'approver_id':self.env['res.users'].browse(uid),
                        'tanggal':datetime.now(),
                        })
                    break
        if reject_all:
            for approval_line in approval_lines:
                if approval_line.state == 'open':
                    approval_line.write({
                        'state':'reject',
                        'approver_id':self.env['res.users'].browse(uid),
                        'reason':reason,
                        'tanggal':datetime.now(),
                        })
            return 1
        return 0
    
    def cancel_approval(self, trx, reason,user_id=None):
        uid = user_id if user_id else self._uid
        config_brw = self.env['tw.approval.config'].search([('model_id','=',trx.__class__.__name__)])
        if not config_brw :
            raise Warning("Perhatian ! Form ini tidak memiliki approval configuration")
        division = self.env['tw.selection'].get_division(trx)
        approval_lines_ids = self.env['tw.approval.line'].search([
            ('division','=',division),
            ('model_id','=',config_brw[0].model_id.id),
            ('transaction_id','=',trx.id),
        ],order="limit asc")
    
        if not approval_lines_ids:
            raise Warning("Perhatian ! Transaksi ini tidak memiliki detail approval. Cek kembali Matrix Approval.")
        cancel_all = False
        for approval_line in approval_lines_ids:
            if approval_line.state in ('open','approve'):
                cancel_all = True
                approval_line.write({
                    'state':'cancel',
                    'reason':reason,
                    'approver_id':uid,
                    'tanggal':datetime.now(),
                    })
        if cancel_all:
            return 1
        return 0  


class TwApprovalMatrixLine(models.Model):
    _name = "tw.approval.matrix.line"
    _description = "Approval Matrix Line"

    # 7: defaults methods

    # 8: fields
    limit = fields.Float(digits=(8,2), string="Limit", required=True)
    is_mandatory_approve = fields.Boolean(string="Mandatory approve?",help="Jika di ceklist, maka approval line untuk group ini tidak bisa di loncat (Veto)")
    is_retain_approval = fields.Boolean(string="Retain Previous Approval?",help="Jika approval untuk Group A sudah di approve, lalu Group B me-reject, maka pada approval selanjutnya di transaksi ini Group A tidak perlu approve lagi jika ceklis ini di aktifkan.")

    # 9: relation fields
    header_id = fields.Many2one(comodel_name='tw.approval.matrix', string="Header", ondelete="cascade")
    group_id = fields.Many2one(comodel_name='res.groups', string="Group", required=True, domain="[('category_id.name','=','TW Job')]")


    # 10: constraints & sql constraints
    @api.constrains('limit')
    def _check_limit_not_negative(self):
        for record in self:
            if record.header_id.config_type != 'discount' and record.limit <= 0:
                raise ValidationError(_("Limit cannot be negative or zero."))

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
