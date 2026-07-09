# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date, timedelta, datetime
import select

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib



class TWActivityLead(models.Model):
    _inherit = "tw.lead"

    # 7: default methods
    
    # 8: fields
    is_btl = fields.Boolean(string='BTL?', compute='_compute_is_btl', store=True)
    is_requires_act_type = fields.Boolean(compute='_compute_channel_configuration')
    is_pos = fields.Boolean(compute='_compute_channel_configuration')
    sales_channel = fields.Char(compute='_compute_sales_channel', store=True)
    
    # 9: relation fields
    sales_channel_id = fields.Many2one(comodel_name='tw.selection', string='Jaringan Penjualan', domain=[('type', '=', 'SalesChannel')])
    act_type_id = fields.Many2one(comodel_name='tw.master.activity.type', string='Activity Type')
    activity_plan_id = fields.Many2one(comodel_name='tw.activity.atl.btl.line', string='Activity')
    activity_point_id = fields.Many2one(comodel_name='tw.titik.keramaian', string='Titik Keramaian', readonly=True)
    sales_source_location_id = fields.Many2one(comodel_name='stock.location', string='Sales Source Location')
    
    # these fields is used to domain other fields
    activity_plan_ids = fields.Many2many(comodel_name='tw.activity.atl.btl.line', compute='_compute_activity_plan', store=False)

    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    @api.depends('act_type_id')
    def _compute_is_btl(self):
        for record in self:
            if record.act_type_id:
                record.is_btl = record.act_type_id.is_btl
            else:
                record.is_btl = False

    @api.depends('sales_channel_id')
    def _compute_sales_channel(self):
        for record in self:
            if record.sales_channel_id:
                record.sales_channel = record.sales_channel_id.value.lower()
                
    @api.depends('sales_channel_id', 'sales_channel_id.context')
    def _compute_channel_configuration(self):
        for record in self:
            if record.sales_channel_id:
                record.is_requires_act_type = record.sales_channel_id.context_get('requires_act_type', False)
                record.is_pos = record.sales_channel_id.context_get('is_pos', False)
            else:
                record.is_requires_act_type = False
                record.is_pos = False

    @api.depends('company_id', 'date','sales_channel_id','act_type_id')
    def _compute_activity_plan(self):
        for record in self:
            date = record.date
            sales_channel_id = record.sales_channel_id.id
            act_type_id = record.act_type_id.id
            activity = record.env['tw.activity.atl.btl'].suspend_security().search([
                ('company_id', '=', record.company_id.id),
                ('state', 'in', ['open', 'approved']),
                ('year', '=', str(date.year)),
                ('month', '=', str(date.month))])

            if activity:
                activity_line = activity.suspend_security().activity_line_ids.filtered(lambda x: x.state in ('open', 'confirmed')
                                                                    and x.sales_channel_id.id == sales_channel_id
                                                                    and x.act_type_id.id == act_type_id
                                                                    and x.start_date <= date
                                                                    and x.end_date >= date)
                record.activity_plan_ids = activity_line.mapped('id')
            else:
                record.activity_plan_ids = []

    @api.onchange('sales_channel_id')
    def _onchange_sales_channel_id(self):
        self.act_type_id = False
        self.activity_plan_id = False
        self.activity_point_id = False
    
    @api.onchange('act_type_id')
    def _onchange_act_type_id(self):
        self.activity_plan_id = False
        self.activity_point_id = False

    @api.onchange('activity_plan_id')
    def _onchange_activity_plan_id(self):
        self.activity_point_id = False
        self.sales_source_location_id = False
        if self.activity_plan_id:
            mapping_activity_obj = self.activity_plan_id.mapping_activity_id
            self.activity_point_id = mapping_activity_obj.activity_point_id.id
            self.sales_source_location_id = self.activity_plan_id.location_id.id
    
    # 12: override methods
    
    # 13: action methods
    def action_propose(self):
        super().action_propose()
        sequence = self.env['ir.sequence'].suspend_security()
        if self.payment_type != '2' and not self.name:
            name_code = self.sales_channel_id.context_get('seq_code', '0001')
            doc_code = self.company_id.code
            self.write({'name': sequence.get_lead_partner_sequence(doc_code, name_code)})
    
    # 14: private methods
    
    def _prepare_spk_vals(self):
        spk_vals = super()._prepare_spk_vals()
        spk_vals.update({
            'sales_channel_id': self.sales_channel_id.id,
            'sales_source_location_id': self.sales_source_location_id.id,
        })
        return spk_vals

