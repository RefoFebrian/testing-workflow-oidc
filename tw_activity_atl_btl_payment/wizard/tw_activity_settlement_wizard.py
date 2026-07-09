# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class ActivitySettlementWizard(models.TransientModel):
    _name = "tw.activity.settlement.wizard"
    _description = "Settlement Wizard for ATL/BTL Activity"

    activity_line_id = fields.Many2one('tw.activity.atl.btl.line', readonly=True)
    line_ids = fields.One2many(
        'tw.activity.settlement.wizard.line',
        'wizard_id',
        string='AVP Lines'
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id:
            activity_line = self.env['tw.activity.atl.btl.line'].browse(active_id)
            lines = []
            for avp in activity_line.advance_payment_ids:
                lines.append((0, 0, {
                    'advance_payment_id': avp.id,
                    'avp_amount': avp.amount,
                    'actual_amount': 0,  # default 0 for actual amount
                }))
            res['activity_line_id'] = active_id
            res['line_ids'] = lines
        return res

    def action_create_settlement(self):
        self.ensure_one()
        self.activity_line_id.with_context(
            settlement_wizard_id=self.id
        ).action_create_settlement_from_wizard(self)

class ActivitySettlementWizardLine(models.TransientModel):
    _name = "tw.activity.settlement.wizard.line"
    _description = "Settlement Wizard Line per AVP"

    avp_amount = fields.Float('AVP Amount', readonly=True)
    actual_amount = fields.Float('Actual Amount', required=True)

    # Computed to drive visibility/required on journal
    stl_type = fields.Selection([
        ('kembali', 'Kembali'),
        ('tambah', 'Tambah'),
    ], compute='_compute_stl_type', string='Settlement Type')

    wizard_id = fields.Many2one('tw.activity.settlement.wizard', ondelete='cascade')
    advance_payment_id = fields.Many2one('tw.advance.payment', string='AVP', readonly=True)
    return_journal_id = fields.Many2one('account.journal', string='Journal Kembali', domain="[('company_id', 'parent_of', company_id), ('type', 'in', ('bank', 'cash'))]")
    company_id = fields.Many2one('res.company', compute='_compute_company_id', store=True)

    attachment_ids = fields.Many2many(
        'ir.attachment',
        'settlement_wizard_line_attachment_rel',
        'wizard_line_id', 'attachment_id',
        string='Attachments'
    )

    @api.depends('wizard_id.activity_line_id.company_id')
    def _compute_company_id(self):
        for rec in self:
            rec.company_id = rec.wizard_id.activity_line_id.company_id

    @api.depends('actual_amount', 'avp_amount')
    def _compute_stl_type(self):
        for rec in self:
            if rec.actual_amount and rec.avp_amount:
                if rec.actual_amount < rec.avp_amount:
                    rec.stl_type = 'kembali'
                elif rec.actual_amount > rec.avp_amount:
                    rec.stl_type = 'tambah'
                else:
                    rec.stl_type = False
            else:
                rec.stl_type = False
    