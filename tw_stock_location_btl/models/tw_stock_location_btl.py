# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class InheritStockLocationBTL(models.Model):
    _inherit = "stock.location"
    _rec_name = 'display_name'
    # INFO : Override from Stock Location and Connected to Activity Plan BTL
    
    # 7: defaults methods
    def get_sequence_loc_btl(self,branch_code,activity_type_code):
        """
        Get sequence for location btl
        """
        seq = self.env['ir.sequence']
        seq_name = '{0}-{1}-'.format(branch_code,  activity_type_code)
        ids = self.env['ir.sequence'].search([('name',  '=',  seq_name)])
        if not ids:
            prefix = seq_name
            ids = self.env['ir.sequence'].create(
                {
                    'name': seq_name,
                    'implementation': 'standard', 
                    'prefix': prefix,
                    'padding': 5,
                }
            )
        return ids.next_by_id()

    # 8: fields
    display_name = fields.Char(string="Display Name", compute='_compute_display_name')
    effective_start_date = fields.Date('Effective Start Date')
    effective_end_date = fields.Date('Effective End Date')

    # 9: relation fields
    btl_loc_type_id = fields.Many2one('tw.selection', "BTL Location Type", domain=[('type', '=', 'StockLocationBTL')])

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('complete_name', 'description')
    def _compute_display_name(self):
        for record in self:
            if record.btl_loc_type_id:
                record.display_name = "[%s] %s" % (record.complete_name, record.description)
            else:
                record.display_name = record.complete_name

    # 12: override methods    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            act_type_id = vals.get('act_type_id', False)
            if act_type_id:
                remove_vals = vals.pop('act_type_id')
            if vals.get('is_loc_btl'):
                branch_code = self.env['res.company'].browse(vals.get('company_id')).code
                activity_type_code = self.env['tw.master.activity.type'].browse(act_type_id).code
                vals['name'] = self.get_sequence_loc_btl(branch_code, activity_type_code)
                remove_vals = vals.pop('is_loc_btl')
        return super(InheritStockLocationBTL, self).create(vals)
    
    def write(self, vals):
        return super(InheritStockLocationBTL, self).write(vals)

    # 13: action methods

    # 14: private methods
    
