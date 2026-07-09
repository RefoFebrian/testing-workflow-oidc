# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api


# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwUploadMessageWizard(models.TransientModel):
    _name = "tw.upload.message.wizard"
    _description = "Upload Message Wizard"

    # 7: defaults methods
    @api.model
    def default_get(self, fields):
        res = super(TwUploadMessageWizard, self).default_get(fields)
        res['message'] = self.env.context.get('message', '')
        return res

    # 8: fields
    message = fields.Text('Message', readonly=True)

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_confirm(self):
        parent_id = self.env.context.get('default_parent_id')
        method_to_call = self.env.context.get('method_to_call', 'action_done')
        if parent_id:
            checklist_tool = self.env['tw.checklist.tools'].browse(parent_id)
            if checklist_tool.exists():
                if hasattr(checklist_tool, method_to_call):
                    getattr(checklist_tool, method_to_call)(confirmed=True)
        return {'type': 'ir.actions.act_window_close'}

    # 14: private methods