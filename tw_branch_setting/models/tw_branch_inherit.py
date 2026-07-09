from odoo import models, fields, api


class BranchInherit(models.Model):
    _inherit = "res.company"

    branch_setting_id = fields.Many2one('tw.branch.setting', string='Branch Setting')
    
    @api.model_create_multi
    def create(self,vals_list):
        creates = super(BranchInherit, self).create(vals_list)
        auto_create = self.env['ir.config_parameter'].sudo().get_param('tw_branch_setting.auto_create', 'True')
        if auto_create and auto_create.lower() == 'true':
            for create in creates:
                if create.parent_id:
                    create._create_branch_setting()
        return creates

    def _create_branch_setting(self):
        branch_setting_obj = self.env['tw.branch.setting'].suspend_security().create({'company_id':self.id})
        self.branch_setting_id = branch_setting_obj.id

    def _link_existing_branch_setting(self):
        existing_setting = self.env['tw.branch.setting'].suspend_security().search([('company_id', '=', self.id)], limit=1)
        if existing_setting:
            self.branch_setting_id = existing_setting.id
            return True
        return False

    def action_open_branch_setting(self):
        """ Utility method used to add an "Open Branch Setting" button in Branch views """
        if not self.branch_setting_id:
            if not self._link_existing_branch_setting():
                self._create_branch_setting()   
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tw.branch.setting',
            'view_mode': 'form',
            'res_id': self.branch_setting_id.id,
        }
