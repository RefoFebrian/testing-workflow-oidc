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

class InheritNrfsWorkOrder(models.Model):
    _inherit = "tw.nrfs"
    
    # 7: defaults methods
    def _get_default_main_dealer_code(self):
        return self.env['res.company'].get_default_main_dealer_code()

    # 8: fields

    # 9: relation fields
    work_order_ids = fields.One2many('tw.work.order','nrfs_id', string='Detail Work Order')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_create_wo(self):
        wo_obj = self.env['tw.work.order'].suspend_security().search([('nrfs_id','=',self.id)],limit=1)
        if not wo_obj:
            msg = "" # warning
            penanganan_wh_part = [
                self.env.ref('tw_nrfs.nrfs_penanganan_unit_tanpa_part').id,
                self.env.ref('tw_nrfs.nrfs_penanganan_unit_repainting_vendor').id,
                self.env.ref('tw_nrfs.nrfs_penanganan_unit_repainting_gudang').id
            ]
            service_list = []
            wo_line_vals = []
            wo_branch_obj = self.env['res.company'].suspend_security().search([('partner_id','=',self.branch_partner_id.id)],limit=1)
            if not wo_branch_obj:
                raise Warning('Branch invalid: AHASS Vendor %d [%s] %s' % (self.branch_partner_id.id, self.branch_partner_id.code, self.branch_partner_id.name))
            branch_setting_obj = self.env['tw.branch.setting'].search([('company_id','=',wo_branch_obj.id)],limit=1)
            pricelist = branch_setting_obj.pricelist_sale_sparepart_id
            pricelist_service = branch_setting_obj.pricelist_service_id
            if not pricelist:
                raise Warning('Pricelist Sparepart tidak ditemukan pada Branch %s [%s] %s' % (wo_branch_obj.id, wo_branch_obj.code, wo_branch_obj.name))
            if not pricelist_service:
                raise Warning('Pricelist Service tidak ditemukan pada Branch %s [%s] %s' % (wo_branch_obj.id, wo_branch_obj.code, wo_branch_obj.name))
            for line in self.line_ids:
                line._show_part_stock_all()
                if line.vendor_handling_id.id not in penanganan_wh_part and line.total_stock < line.qty:
                    msg += "Stock product %s tidak mencukupi: Qty avb vendor %d, Qty yang dibutuhkan %d\n" % (line.product_sparepart_id.product_tmpl_id.name, line.total_stock, line.qty)
                    continue
                if line.vendor_handling_id.id not in penanganan_wh_part:
                    price = pricelist.with_company(wo_branch_obj.id)._price_get(line.product_sparepart_id, 1)[pricelist.id]
                    wo_line_vals.append([0, 0, {
                        'division': 'Sparepart',
                        'product_id': line.product_sparepart_id.id,
                        'product_uom_qty': line.qty,
                        'product_uom': line.product_sparepart_id.uom_id.id,
                        'price_unit': price,
                        'state':'draft'
                    }])
                for service in line.service_ids:
                    if service.id not in service_list:
                        price_jasa = self.env['tw.work.order.line'].suspend_security()._get_harga_jasa(service, 1, self.lot_id.product_id.product_tmpl_id.service_category_id,pricelist_service)
                        wo_line_vals.append([0, 0, {
                            'division': 'Service',
                            'product_id': service.id,
                            'product_uom_qty': 1,
                            'product_uom': service.uom_id.id,
                            'price_unit': price_jasa,
                            'state':'draft'
                        }])
                        service_list.append(service.id)                    
            if msg:
                raise Warning(msg)
            customer_id = driver_id = mobile = False
            if self.nrfs_type == 'LKUAT':
                customer_id = self.stock_inbound_id.expedition_id.id
                driver_id = self.driver_id.id
                mobile = self.driver_id.mobile if self.driver_id.mobile else False
            elif self.nrfs_type == 'LKUAS':
                md_code = self._get_default_main_dealer_code()
                search_code = md_code+'-LKUAS'
                customer_obj = self.env['res.partner'].suspend_security().search([('code','=',search_code)],limit=1)
                if customer_obj:
                    customer_id = customer_obj.id
                    driver_id = customer_obj.id
                    mobile = customer_obj.mobile if customer_obj.mobile else False

            type_id = self.env['tw.selection'].suspend_security().search([
                ('type','=','WorkOrderType'),
                ('value','=','CLA')
            ])

            claim_type_id = self.env['tw.selection'].suspend_security().search([
                ('type', '=', 'WorkOrderClaimType'),
                ('value', '=', 'Other')
            ])

            wo_vals = {
                'company_id': wo_branch_obj.id,
                'division': 'Sparepart',
                'type_id': type_id.id if type_id else False,
                'claim_type_id': claim_type_id.id if claim_type_id else False,
                'nrfs_id': self.id,
                'lot_id': self.lot_id.id,
                'chassis_number': self.lot_id.chassis_number,
                'product_id': self.lot_id.product_id.id,
                'production_year': self.lot_id.production_year,
                'purchase_date': self.lot_id.receive_date,
                'km': 1,
                'customer_stnk_id': customer_id,
                'partner_id': driver_id,
                'mobile': mobile,
                'plate_number': self.lot_id.plate_number or False,
                'order_line': wo_line_vals
            }
            wo_obj = self.env['tw.work.order'].suspend_security().create(wo_vals)
            if wo_obj:
                self.write({'state': 'in_progress'})
        form_id = self.env.ref('tw_work_order.tw_work_order_form_view').id
        return {
            'name': 'Work Order',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tw.work.order',
            'res_id': wo_obj.id,
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current'
        }

    # 14: private methods
    
    