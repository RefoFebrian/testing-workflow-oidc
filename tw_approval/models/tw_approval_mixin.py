import pytz
from datetime import datetime
from ast import literal_eval
from lxml import etree
from odoo import api, fields, models, _ , SUPERUSER_ID
from odoo.exceptions import ValidationError
from odoo.tools.misc import frozendict
from odoo.exceptions import UserError as Warning


class TwApprovalMixin(models.AbstractModel):
    _name = "tw.approval.mixin"
    _description = "Approval Mixin"
    # _inherit = ['mail.thread','mail.activity.mixin']
    
    def approval_domain(self):
        return [('model_id', '=', self._name)]

    approval_state = fields.Selection(
        selection=[
            ('none', 'Belum Request'),
            ('request_for_approval', 'Request For Approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected')
        ], string='Approval State', readonly=True, default='none', copy=False
    )
    approval_ids = fields.One2many(
        comodel_name='tw.approval.line',
        inverse_name='transaction_id',
        string="Approval List",
        domain=approval_domain,
        copy=False
    )
    rfa_uid = fields.Many2one('res.users', string="RFA by")
    rfa_date = fields.Datetime('RFA on')

    def generate_matrix_approval(self,value=0,code='other', **kwargs):
        self.ensure_one()
        product_tmpl_id = kwargs.get('product_tmpl_id')
        department_id = kwargs.get('department_id')
        product_id = kwargs.get('product_id')
        categ_id = kwargs.get('categ_id')
        if self.approval_ids:
            last_approval_line_sts = self.approval_ids[-1].state
            # Generate when status is not 'Belum Approve'
            if last_approval_line_sts != 'open':
                self.env["tw.approval.matrix"].suspend_security().request_by_value(self, value=value, code=code, product_tmpl_id=product_tmpl_id, department_id=department_id, product_id=product_id, categ_id=categ_id)
                self.write({"approval_state": "request_for_approval"})
        else:
            self.env["tw.approval.matrix"].suspend_security().request_by_value(self, value=value, code=code, product_tmpl_id=product_tmpl_id, department_id=department_id, product_id=product_id, categ_id=categ_id)

    def validate_order(self):
        pass

    def get_rfa_additional_vals(self):
        self.ensure_one()
        return {'state': 'waiting_for_approval'}
    
    def get_approve_additional_vals(self):
        self.ensure_one()
        return {'state': 'approved'}

    def action_request_approval(self,value=False,code='other', **kwargs):
        self.ensure_one()
        self.validate_order()
        total = value or getattr(self, self._get_amount_field())
        if kwargs.get('product_id'):
            product_id = kwargs.get('product_id')
            product_obj = self.env['product.product'].browse(product_id)
            self.generate_matrix_approval(total,code,product_id=product_id,product_tmpl_id=product_obj.product_tmpl_id.id,categ_id=product_obj.product_tmpl_id.categ_id.id)
        elif kwargs.get('department_id'):
            department_id = kwargs.get('department_id')
            self.generate_matrix_approval(total,code,department_id=department_id)
        else:
            self.generate_matrix_approval(total,code)
        vals = {
            'approval_state': 'request_for_approval',
            'rfa_uid': self._uid,
            'rfa_date': datetime.now()
        }
        vals.update(self.get_rfa_additional_vals())
        self.write(vals)

    def action_approval(self):
        self.ensure_one()
        if self.approval_state == 'approved':
            raise Warning(f'Silakan refresh halaman browser Anda. Approval state telah pada {self._get_state_value()}')

        approval_status = self.env['tw.approval.matrix'].approve(self)
        if approval_status == 1:
            vals = {
                'approval_state': 'approved',
            }
            vals.update(self.get_approve_additional_vals())
            self.write(vals)

            activities= self.env['mail.activity'].search([('res_id', '=', self.id), ('res_model_id', '=', self._name),('activity_type_id', '=', self.env.ref('mail.mail_activity_data_todo').id),])
            if activities:
                activities.action_done()

        elif approval_status == 0:
            raise Warning("Anda tidak termasuk group Approval")
        return approval_status

    def _get_default_date_tz(self):
        return pytz.UTC.localize(fields.Datetime.now()).astimezone(pytz.timezone(self.env.user.tz or 'Asia/Jakarta'))
        
    def action_reject_or_cancel(self, update_values=None):
        """
        Open a rejection wizard for the current record.
        
        :param dict update_values: Dictionary of values to update on the record when rejected.
                                 Defaults to {'state': 'draft'} if not provided.
        :param str window_title: Title for the wizard window.
        :return: Action to open the rejection wizard.
        :rtype: dict
        """
        window_title = self._context.get('window_title')
        validate_state = ['waiting_for_approval','approved']
        
        if self.state not in validate_state:
            raise Warning(f'Silakan refresh halaman browser Anda. State sudah {self._get_state_value()}')
        
        if window_title != 'Cancel':
            self._check_groups()

        wizard_form_ref = 'tw_approval.tw_approval_reject_wizard_form_view'
        if window_title == 'Cancel':
            wizard_form_ref = 'tw_approval.tw_cancel_approval_wizard_form_view'
        
        self.ensure_one()
        form_id = self.env.ref(wizard_form_ref).id
            
        if update_values is None:
            update_values = {'state': 'draft'}
            
        # Ensure model name is in the correct format (with dots)
        model_name = self._name
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tw.approval',
            'name': f'{window_title} Approval {self._description or model_name}',
            'views': [(form_id, 'form')],
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': False,
            'target': 'new',
            'context': {
                'model_name': model_name,
                'update_value': update_values,
                'active_id': self.id,
                'active_model': model_name,
            },
        }
    
    def _check_groups(self):
        user_groups = self.env['res.users'].suspend_security().search([('id','=',self._uid)]).groups_id
        model_id = self.env['ir.model']._get(self._name).id
        approval_lines = self.env['tw.approval.line'].search([
            ('model_id','=',model_id),
            ('transaction_id','=',self.id),
            ('division','=',self.env['tw.selection'].get_division(self)),
        ],order="limit asc")
        
        approval_rejected = []
        has_open = False
        for approval_line in approval_lines:
            if approval_line.state == 'open':
                has_open = True
                if approval_line.group_id not in user_groups:
                    approval_rejected.append(True)
                else:
                    approval_rejected.append(False)

        
        if not False in approval_rejected and has_open:
            raise Warning(f"Anda tidak termasuk group Approval pada salah satu Matrix Approval")
    
    def _get_amount_field(self):
        """
        Get the field name that contains the amount to check against approval matrix.
        This method should be implemented by the inheriting model.
        replace with your amount field name if field name is different in your model inherit
        """
        return "amount_total"
    
        
    def _get_state_value(self):
        # Mengambil value yang sesuai dengan key di state
        selection = self._fields.get('approval_state') and self._fields['approval_state'].selection
        return dict(selection).get(self.approval_state, self.approval_state) if selection else self.approval_state


    def approva_all_approval(self,reason=''):
        if not reason:
            raise Warning("Reason is required")
	    
        vals = {
                'approval_state': 'approved',
            }
        vals.update(self.get_approve_additional_vals())
        self.write(vals)
        self.bypass_approve(reason)


    def bypass_approve(self,reason):
        self.env.cr.commit()
        self.approval_ids.write({
			'approver_id':SUPERUSER_ID,
            'state':'approve',
			'tanggal':datetime.now(),
			'reason':reason
		})