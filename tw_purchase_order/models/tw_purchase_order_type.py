# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime
import calendar

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwPurchaseOrderType(models.Model):
	_name = "tw.purchase.order.type"
	_description = "Purchase Order Type"
	_rec_names_search = ['name', 'code']

    # 7: defaults methods

    # 8: fields
	name = fields.Char()
	code = fields.Char(string='Code', compute='_compute_selection_code', store=True)
	division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
	
    # 9: relation fields
	start_date_id = fields.Many2one(comodel_name='tw.selection', string="Start Date", domain=[('type', '=', 'DatePo')])
	end_date_id = fields.Many2one(comodel_name='tw.selection', string="End Date", domain=[('type', '=', 'DatePo')])
	company_id = fields.Many2one('res.company', string="Branch", default=lambda self: self.env.company)
	# Add default operation types
	default_incoming_type_id = fields.Many2one('stock.picking.type', string='Default Incoming Type',
        domain=[('code', '=', 'incoming')],
        help="Default operation type for incoming shipments")
	default_outgoing_type_id = fields.Many2one('stock.picking.type', string='Default Outgoing Type',
        domain=[('code', '=', 'outgoing')],
        help="Default operation type for outgoing shipments")
	default_internal_type_id = fields.Many2one('stock.picking.type', string='Default Internal Type',
        domain=[('code', '=', 'internal')],
        help="Default operation type for internal transfers")
    
	
    # 10: constraints & sql constraints
	
    # 11: compute/depends & on change methods
	@api.depends('division', 'name')
	def _compute_selection_code(self):
		for record in self:
			if record.division:
				record.code = f"{record.division}|{record.name}"
			else:
				record.code = record.name or ''

    # 12: override methods

	def get_date(self, date_type):
		now = datetime.today()
		year, month = now.year, now.month

		if date_type == 'now':
			return now
		elif date_type == 'end_of_month':
			return datetime(year, month, calendar.monthrange(year, month)[1])
		elif date_type in ['next_month', 'end_of_next_month', 'next_2_months', 'end_of_next_2_months']:
			months_to_add = {
				'next_month': 1,
				'end_of_next_month': 1,
				'next_2_months': 2,
				'end_of_next_2_months': 2
			}[date_type]
			year += (month + months_to_add - 1) // 12
			month = (month + months_to_add - 1) % 12 + 1

			if 'end' in date_type:
				return datetime(year, month, calendar.monthrange(year, month)[1])
			else:
				return datetime(year, month, 1)
		return now
	
	# 13: action methods
	def action_act_window_purchase_order_type(self, type):
		action = {
			'type': 'ir.actions.act_window',
			'name': 'Purchase Order Type',
			'view_mode': 'list,form',
			'res_model': 'tw.purchase.order.type',
			'context': {'default_division': 'showroom'},
		}

		if type == 'Showroom':
			action['domain'] = [('division', '=', 'Unit')]
			action['context'] = {
                'default_division': 'Unit',
            }
		elif type == 'Workshop':
			action['domain'] = [('division', '=', 'Sparepart')]
			action['context'] = {
                'default_division': 'Sparepart',
            }
		elif type == 'General':
			action['domain'] = [('division', 'in', ['Umum', 'Extras', 'Finance'])]
			action['context'] = {
                'default_division': 'Umum',
            }
		
		return action