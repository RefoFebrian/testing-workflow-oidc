# -*- coding: utf-8 -*-

# 1: imports of python lib
from collections import defaultdict

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.tools.sql import column_exists, create_column

# 5: local imports

# 6: Import of unknown third party lib


class StockMove(models.Model):
    _inherit = "stock.move"
    
    def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, svl_id, description):
        vals = super()._generate_valuation_lines_data(partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, svl_id, description)
        if self.raw_material_production_id or self.production_id:
            categ = self.product_id.categ_id
            if not categ.bundling_account_id:
                raise Warning(_("Bundling account not found for product %s") % self.product_id.name)
            
            if self.raw_material_production_id:
                debit_line = vals.get('debit_line_vals')
                if debit_line:
                    debit_line['account_id'] = categ.bundling_account_id.id
            
            if self.production_id:
                mo = self.production_id
                if getattr(mo, 'order_type', '') == 'bundling':
                    credit_line = vals.pop('credit_line_vals', None)
                    if not credit_line:
                        return vals
                        
                    portions = defaultdict(float)
                    serial_lot = self.lot_ids[:1] if self.product_id.tracking == 'serial' and self.lot_ids else False
                    
                    # 1. Serial Component
                    if serial_lot:
                        raw_ml = mo.move_raw_ids.move_line_ids.filtered(lambda ml: ml.lot_id == serial_lot)
                        if raw_ml:
                            serial_acc = raw_ml.product_id.categ_id.bundling_account_id
                            if not serial_acc:
                                 raise Warning(_("Bundling account not found for serial component %s") % raw_ml.product_id.name)
                            svl = serial_lot.stock_valuation_layer_ids.filtered(lambda l: l.stock_move_id.raw_material_production_id.id == mo.id)
                            if not svl:
                                svl = serial_lot.stock_valuation_layer_ids
                            if svl:
                                serial_unit_val = abs(svl[-1].value)
                                portions[serial_acc] += serial_unit_val * qty
                                
                    # 2. Non-serial Components
                    other_components = mo.move_raw_ids.filtered(lambda ln: ln.product_id.tracking != "serial")
                    for comp in other_components:
                        acc = comp.product_id.categ_id.bundling_account_id
                        if not acc:
                            raise Warning(_("Bundling account not found for component %s") % comp.product_id.name)
                        comp_unit_cost = sum(comp.move_line_ids.mapped(lambda ml: ml.product_id.standard_price * ml.quantity)) / max(mo.product_qty, 1.0)
                        portions[acc] += comp_unit_cost * qty
                        
                    # 3. Labour
                    for wo in mo.workorder_ids:
                        acc = wo.workcenter_id.bundling_account_id
                        if not acc:
                            raise Warning(_("Bundling account not found for workcenter %s") % wo.workcenter_id.name)
                        wo_unit_cost = wo._cal_cost() / max(mo.product_qty, 1.0)
                        portions[acc] += wo_unit_cost * qty

                    # Distribute credit_value exactly
                    total_distributed = 0.0
                    currency = self.company_id.currency_id
                    acc_list = list(portions.keys())
                    
                    if not acc_list:
                        acc_list = [categ.bundling_account_id]
                        portions[categ.bundling_account_id] = credit_value

                    for i, acc in enumerate(acc_list):
                        amt = portions[acc]
                        if i == len(acc_list) - 1:
                            amt = credit_value - total_distributed
                        else:
                            amt = currency.round(amt)
                            total_distributed += amt
                        
                        if not currency.is_zero(amt):
                            vals[f'credit_line_split_{acc.id}'] = {
                                **credit_line,
                                'balance': -amt,
                                'account_id': acc.id,
                            }
                else:
                    credit_line = vals.get('credit_line_vals')
                    if credit_line:
                        credit_line['account_id'] = categ.bundling_account_id.id
        return vals