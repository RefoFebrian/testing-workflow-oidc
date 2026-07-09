from odoo import api, fields, models, _
from odoo.exceptions import UserError as Warning
from lxml import etree
from datetime import datetime


class TwVehicleDocumentOutstanding(models.Model):
    _inherit = "stock.lot"

    doc_number = fields.Char(string='No Faktur STNK', tracking=True)
    print_date = fields.Date(string='Tanggal Cetak', tracking=True)
    is_hold_cdb = fields.Boolean(string='Is hold CDB?', default=False, help='Menunda proses CDB karena ketika GC ada kemungkinan mengganti data CDB')
    cddb_state = fields.Selection(
        string='CDDB State',
        selection=[
            ('draft', 'Not Ok'),
            ('udstk', 'UDSTK OK'),
            ('cddb', 'CDDB OK')
        ], readonly=True, default='draft', tracking=True
    )
    document_state = fields.Selection(selection=[
            ('document_request', 'Permohonan Faktur'),
            ('document_receive', 'Penerimaan Faktur'),
            ('registration_process', 'Proses STNK'),
        ],string='STNK State',readonly=True, tracking=True
    )

    vehicle_document_outstanding_date = fields.Date(string='Tanggal Outstanding Faktur', tracking=True)
    vehicle_document_request_date = fields.Date(string='Tanggal Pemohonan Faktur', tracking=True)
    vehicle_document_receive_date = fields.Date(string='Tanggal Penerimaan Faktur', tracking=True)
    
    vehicle_document_request_id = fields.Many2one('tw.vehicle.document.request', string="Permohonan Faktur", readonly=True, tracking=True)
    vehicle_document_receive_id = fields.Many2one('tw.vehicle.document.receive', string="Penerimaan Faktur", readonly=True, tracking=True)

    # Audit Trail
    hold_cdb_date = fields.Datetime(string='Hold on')
    hold_cdb_uid = fields.Many2one('res.users', string='Hold by')

    def action_hold_cdb(self):
        self.write({
            'is_hold_cdb': True,
            'hold_cdb_date': fields.Datetime.now(),
            'hold_cdb_uid': self._uid
        })

    def action_unhold_cdb(self):
        self.write({
            'is_hold_cdb': False,
            'hold_cdb_date': fields.Datetime.now(),
            'hold_cdb_uid': self._uid
        })

    def action_edit_udstk(self):
        self.ensure_one()
        view = self.env.ref('tw_vehicle_document.tw_udstk_view_form')
        return {
            'name': _('Edit UDSTNK'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.lot',
            'view_mode': 'form',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'res_id': self.id,
            'target': 'new',
            'context': {   
                'default_lot_id': self.id,
            },
        }

    def action_edit_customer(self):
        self.ensure_one()
        existing_cdb_obj = self.cdb_partner_id
        cdb_obj = self.env['tw.partner.cdb'].suspend_security().search([
            ('lot_ids', 'in', self.id),
            ('company_id', '=', self.company_id.id),
            ('partner_id', '=', self.customer_stnk_id.id),
            ], limit=1)
        if cdb_obj == existing_cdb_obj: 
            cdb_obj = existing_cdb_obj
        
        if not cdb_obj:
            cdb_vals = {
                    'lot_ids': [(4, self.id)],
                    'company_id': self.company_id.id,
                    'product_id': self.product_id.id,
                }
            if existing_cdb_obj:
                cdb_vals.update({
                    'downpayment': existing_cdb_obj.downpayment,
                    'installments': existing_cdb_obj.installments,
                    'tenor': existing_cdb_obj.tenor,
                    'sales_channel_id': existing_cdb_obj.sales_channel_id.id,
                    'employee_id': existing_cdb_obj.employee_id.id,
                })
                existing_cdb_obj.write({
                    'lot_ids': [(3, self.id)]  # (3, ID) removes the relationship
                })
                # delete cdb if no lot_ids
                if not existing_cdb_obj.lot_ids:
                    existing_cdb_obj.suspend_security().unlink()
            cdb_obj = self.customer_stnk_id.sync_partner_to_cdb(**cdb_vals)

        self.suspend_security().write({
            'cdb_partner_id': cdb_obj.id,
        })
        
        view = self.env.ref('tw_partner_cdb.view_tw_partner_cdb_form')
        return {
            'name': _('Edit Customer'),
            'type': 'ir.actions.act_window',
            'res_model': 'tw.partner.cdb',
            'view_mode': 'form',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'res_id': self.cdb_partner_id.id,
            'target': 'new',
            'context': {
                'is_edit_cdb_lot': True,      # <-- ini yang dijembatani ke field
                'default_lot_id': self.id,
            },
        }

    
    def action_confirm_cdb(self):
        self.ensure_one()
        # Update the state directly
        self.env['stock.lot'].browse(self._context.get('active_id')).write({
            'cddb_state': 'cddb',
            'vehicle_document_outstanding_date': datetime.now(),
        })

    def action_confirm_udstnk(self):
        self.ensure_one()
        if not self.customer_stnk_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'message': _('Please select a customer for STNK.'),
                    'sticky': False,
                }
            }
        
        # Get the partner form view to check for required fields
        partner_form = self.env['ir.ui.view']._get('tw_partner.tw_customer_partner_form_view')
        required_fields = []
        
        # Check for required fields in the form
        for node in etree.fromstring(partner_form.arch).xpath('//field[@required="1"]'):
            field_name = node.get('name')
            if field_name and field_name not in required_fields:
                required_fields.append(field_name)
        
        # Check if required fields are set
        missing_fields = []
        partner = self.customer_stnk_id
        for field in required_fields:
            if field in partner._fields and not partner[field]:
                field_desc = partner._fields[field].string or field
                missing_fields.append(field_desc)
        
        if missing_fields:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'message': _('Please fill in the following required fields for the customer STNK:\n- %s') % 
                              "\n- ".join(missing_fields),
                    'sticky': False,
                    'message_is_html': False,
                }
            }
        
        self.suspend_security().write({
            'cddb_state': 'udstk',
        })
