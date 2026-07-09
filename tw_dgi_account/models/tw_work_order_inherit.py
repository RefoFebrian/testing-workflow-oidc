# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _

# 4: imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwWorkOrderDgi(models.Model):
    _inherit = "tw.work.order"

    # 7: defaults methods

    # 8: fields
    dgi_invoice_status = fields.Selection([
        ('draft', 'Draft (To Sync)'),
        ('done', 'Synced'),
        ('error', 'Error Sync')
    ], string='DGI Invoice Status', tracking=True, copy=False)
    
    dgi_invoice_error_log = fields.Text(string='DGI Invoice Log', readonly=True, copy=False)
    dgi_err_count_inv = fields.Integer(string='DGI Sync Fail Count', default=0, copy=False)

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_done(self):
        res = super(TwWorkOrderDgi, self).action_done()
        for record in self:
            # Jangan override jika sudah berhasil terkirim ('done') — tidak bisa kirim ulang
            if record.dgi_invoice_status == 'done':
                continue
            # Hanya mark draft jika sudah ada invoice yang posted
            if record._is_dgi_ready_to_sync():
                record.dgi_invoice_status = 'draft'
        return res

    def action_send_dgi_invoice_h23(self):
        for record in self:
            # Guard 1: sudah terkirim — tidak bisa kirim ulang
            if record.dgi_invoice_status == 'done':
                continue
            # Guard 2: hanya kirim jika sudah ada invoice posted
            if not record._is_dgi_ready_to_sync():
                continue
            
            try:
                company = record.company_id
                branch_setting = company.branch_setting_id
                if not branch_setting or not branch_setting.dgi_config_id:
                    raise Warning(_("DGI Config not found in Branch Setting untuk cabang %s." % company.name))
                
                api_config = branch_setting.dgi_config_id
                endpoint = api_config.endpoint_config_ids.filtered(lambda e: e.code == 'inv2_add' and e.mode == 'add')
                if not endpoint:
                    endpoint = api_config.endpoint_config_ids.filtered(lambda e: e.code == 'inv2_add')

                if not endpoint:
                    raise Warning(_("Endpoint DGI 'inv2_add' (Mode: ADD) tidak ditemukan. Mohon set Endpoint di DGI Configuration."))

                # Build Payload via TwDgiAccountEngine
                payload = self.env['tw.dgi.account.engine'].build_payload_from_template(
                    record, endpoint[0].input_template
                )
                
                response_data = api_config.action_call_endpoint(
                    endpoint=endpoint[0],
                    params=payload,
                    raise_exception=False,
                    override_timeout=30
                )
                
                error_msg = ""
                is_success = False

                if isinstance(response_data, dict):
                    status = response_data.get('status') or response_data.get('http_status_code')
                    msg = response_data.get('message') or response_data.get('title') or response_data.get('error') or str(response_data)
                    
                    if status == 1 or status == 200:
                        is_success = True
                    elif msg and 'sudah lunas' in msg.lower():
                        is_success = True
                    else:
                        error_msg = msg
                else:
                    error_msg = str(response_data)

                if is_success:
                    record.write({
                        'dgi_invoice_status': 'done',
                        'dgi_invoice_error_log': "Sync Success",
                        'dgi_err_count_inv': 0
                    })
                else:
                    record.write({
                        'dgi_invoice_status': 'error',
                        'dgi_invoice_error_log': "Error: " + error_msg,
                        'dgi_err_count_inv': record.dgi_err_count_inv + 1
                    })
            except Exception as e:
                record.write({
                    'dgi_invoice_status': 'error',
                    'dgi_invoice_error_log': "Exception: " + str(e),
                    'dgi_err_count_inv': record.dgi_err_count_inv + 1
                })
        return True

    # 14: private methods
    def _is_dgi_ready_to_sync(self):
        """
        Cek apakah Work Order memiliki invoice yang sudah posted.
        Hanya WO dengan kondisi ini yang boleh dikirim ke DGI (INV2).

        Returns:
            bool: True jika ada account.move (invoice) terkait WO dengan state posted.
        """
        self.ensure_one()
        return any(
            line.invoice_lines.filtered(lambda il: il.move_id.state == 'posted')
            for line in self.order_line
        )
