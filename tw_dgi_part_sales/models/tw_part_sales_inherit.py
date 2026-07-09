# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwPartSalesInherit(models.Model):
    _name = "tw.part.sales"
    _inherit = ["tw.part.sales", "tw.dgi.info.mixin"]

    # 7: defaults methods

    # 8: fields

    # From TEDS Existing
    state_dgi = fields.Char(string='Status DGI')
    md_reference_ps = fields.Char('MD Reference PS',help="ID PS Main Dealer")
    note_log = fields.Text('Note Log')
    dgi_err_count_inv = fields.Integer(string='DGI-INV Error Count', default=0)
    dgi_status_inv = fields.Selection([
        ('draft','Draft'),
        ('error','Error'),
        ('done','Done')
    ], string='DGI-INV Status', default='draft')
    # End of From TEDS Existing
    
    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    def action_open_dgi_wizard(self):
        """Open DGI wizard dari list view"""
        return {
            'name': 'Get Data from DGI',
            'type': 'ir.actions.act_window',
            'res_model': 'tw.dgi.part.sales.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_company_id': self.env.company.id,
            }
        }

    def action_show_dgi_info(self):
        """Override to pass Part Sales-specific references to DGI Info popup."""
        res = super().action_show_dgi_info()
        res['context'].update({
            'default_md_reference_ps': self.md_reference_ps,
        })
        return res
    
    # def action_dgi_inv2_add(self):
    #     branch_setting_id = self.company_id.branch_setting_id
    #     if branch_setting_id and branch_setting_id.config_dgi_h23_id:
    #         self._all_push_inv2_methods(branch_setting_id.config_dgi_h23_id)
    #     else:
    #         error = 'Branch config DGI untuk code %s belum di-setting!' % self.company_id.code
    #         raise Warning(error) 

    # # 14: private methods
    # def _all_push_inv2_methods(self, config_dgi_obj):
    #     raise Warning('There is no push method for this config!')
