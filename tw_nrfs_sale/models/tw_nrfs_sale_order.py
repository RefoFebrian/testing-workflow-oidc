# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class InheritNrfsSaleOrder(models.Model):
    _inherit = "tw.nrfs"
    
    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    sale_order_id = fields.Many2one('tw.sale.order', string='Sale Order')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_validate(self):
        if self.claim_type == 'money':
            self.create_sale_order()
        return super(InheritNrfsSaleOrder,self).action_validate()

    def action_open_sale_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tw.sale.order',
            'view_mode': 'form',
            'view_id': self.env.ref('tw_sale.tw_sale_order_form_view').id,
            'res_id': self.sale_order_id.id
        }

    # 14: private methods
    def _prepare_sale_order_line(self):
        sale_order_lines = []
        for line in self.line_ids:
            sale_order_lines.append((0, 0, {
                'product_id': line.product_sparepart_id.id,
                'product_uom_qty': line.qty,
                'tax_id': [(6, 0, [tax.id for tax in line.product_sparepart_id.taxes_id])],
            }))
        return sale_order_lines

    def create_sale_order(self,partner_obj=False):
        self.ensure_one()  # Pastikan hanya satu record yang diproses

        warehouse = self.env['stock.warehouse']._get_company_warehouse(self.company_id)
        if not warehouse:
            raise Warning(f"Warehouse {self.company_id.name} not found!")

        location_obj = self.env['stock.location'].suspend_security().search([
            ('type_id.value', 'in', ['NRFS', 'nrfs']),
            ('company_id', '=', self.company_id.id),
            ('division', '=', self.division),
        ], limit=1)
        if not location_obj:
            raise Warning(f"Location NRFS for branch {self.company_id.name} and division {self.division} not found!")
        
        if not partner_obj:
            search_domain = []
            if self.claim_to == 'Expedisi':
                search_domain = [('id','=',self.stock_inbound_id.expedition_id.id)]
            else:
                ahm_code = self.env['res.company'].get_default_main_dealer().default_supplier_id.code
                search_domain = [('code', '=', ahm_code)]

            partner_obj = self.env['res.partner'].suspend_security().search(search_domain, limit=1)
            if not partner_obj:
                raise Warning(f"Partner {ahm_code}/{self.stock_inbound_id.expedition_id.name} not found!")
        
        try:
            sale_order_vals = {
                'company_id': self.company_id.id,
                'division': 'Sparepart',
                'user_id': self.env.user.id,
                'date_order': self.nrfs_date,
                'partner_id': partner_obj.id,
                'state': 'draft',
                'warehouse_id': warehouse.id,
                'payment_term_id': partner_obj.property_payment_term_id.id,
                'note': f"{self.claim_to} - {self.nrfs_date.strftime('%B')} - {self.nrfs_date.strftime('%Y')}",
                'order_line': self._prepare_sale_order_line(),
                'nrfs_id': self.id,
                'location_id': location_obj.id
            }

            so_obj = self.env['tw.sale.order'].with_company(self.company_id.id).suspend_security().create(sale_order_vals)
            so_obj.onchange_company_id()
            so_obj.order_line._onchange_product_id_warning()
            if not getattr(self, 'approval_ids', False):
                so_obj.action_request_approval()
        except Exception as e:
            raise Warning(f"Error creating sale order: {str(e)}")
        
        self.write({'sale_order_id': so_obj.id})
    
    