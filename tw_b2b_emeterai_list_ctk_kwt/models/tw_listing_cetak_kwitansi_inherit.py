# 1: imports of python lib
from datetime import datetime, timedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwListingCetakKwitansiInherit(models.Model):
    _inherit = "tw.listing.cetak.kwitansi"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    emeterai_id = fields.Many2one(comodel_name='tw.b2b.emeterai', string='e-Meterai')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_process_stamp(self):
        model_obj = self.env['ir.model'].sudo().search([('model','=',self._name)], limit=1)
        report_obj = self.env.ref('tw_listing_cetak_kwitansi.tw_listing_cetak_kwitansi_print_pdf_action_report')
        vals = {
            'transaction_id': self.id,
            'transaction_name': self.name,
            'company_id': self.company_id.id,
            'amount': self.total,
            'model_id': model_obj.id,
            'report_id': report_obj.id
        }
        emet_model = self.env['tw.b2b.emeterai'].suspend_security()
        try:
            emet_obj = emet_model.create_emeterai_stamp_report(vals)
            self.suspend_security().write({'emeterai_id': emet_obj.id})
            emet_obj.process_stamp_emeterai()
        except Exception as err:
            raise Warning(f'Failed to stamp e-Meterai {model_obj.name} !\nError: {err}')
        
        return emet_obj
    
    def action_open_emeterai(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tw.b2b.emeterai',
            'view_mode': 'form',
            'view_id': self.env.ref('tw_b2b_emeterai.tw_b2b_emeterai_form_view').id,
            'res_id': self.emeterai_id.id
        }

    # 14: private methods