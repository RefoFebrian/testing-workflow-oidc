# -*- coding: utf-8 -*-

# 1: imports of python lib
from collections import defaultdict
import calendar
from datetime import datetime,timedelta
import logging
_logger = logging.getLogger(__name__)


# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, Command, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.tools import float_compare, float_is_zero

# 5: local imports

# 6: Import of unknown third party lib

class TwWorkOrderInherit(models.Model):
    _inherit = "tw.work.order"

    # 7: defaults methods

    # 8: fields
    amount_accrue_tax = fields.Float(string='Amount Accrue Tax', compute="_compute_accrue_tax", store=True)

    # 9: relation fields
    accrue_tax_id = fields.Many2one('account.move', string='Accrue Tax', ondelete='restrict')
    
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('invoice_ids')
    def _compute_accrue_tax(self):
        # Check Accrue Tax from WO Line, Check Invoice already Post
        for record in self.filtered(lambda x: x.invoice_ids):
            if not record.partner_id.identification_number and not record.partner_id.no_npwp:
                accrue_tax = 0
                for line in record.order_line.filtered(lambda x: not x.claim_partner_id):
                    accrue_tax += line.price_subtotal * 0.01
                record.amount_accrue_tax = accrue_tax

    # 12: override methods

    # 13: action methods

    # 14: private methods

    def _schedulle_work_order_accrue_tax(self, company_id=False, bulan=False, tahun=False):
        try:
            msg = ""

            # Bulan Sebelumnya
            if not bulan:
                bulan = int((datetime.now().replace(day=1) - timedelta(days=1)).strftime('%m'))
            if not tahun:
                tahun = int((datetime.now().replace(day=1) - timedelta(days=1)).strftime('%Y'))

            if company_id:
                company_obj = self.env['res.company'].sudo().browse(company_id)
                data = self._process_work_order_accrue_tax(
                    company_id=company_id,
                    bulan=bulan,
                    tahun=tahun
                )
                if not data:
                    msg = (
                        f"No Work Order Accrue Tax found for Company {company_obj.name} "
                        f"[Company ID: {company_obj.id}]. Period: {bulan}/{tahun}. "
                        "To generate specific record, you can use params "
                        "(company_id=9,bulan='01',tahun='2025')\n"
                    )
            else:
                for company in self.env['res.company'].sudo().search([]):
                    data = self._process_work_order_accrue_tax(
                        company_id=company.id,
                        bulan=bulan,
                        tahun=tahun
                    )
                    if not data:
                        msg += (
                            f"No Work Order Accrue Tax found for Company {company.name} "
                            f"[Company ID: {company.id}]. Period: {bulan}/{tahun}. "
                            "To generate specific record, you can use params "
                            "(company_id=9,bulan='01',tahun='2025')\n"
                        )

            if msg:
                raise Warning(msg)

        except Exception as e:
            _logger.error(
                "Error on _schedulle_work_order_accrue_tax | "
                "company_id=%s, bulan=%s, tahun=%s | Error: %s",
                company_id, bulan, tahun, str(e),
                exc_info=True
            )

    def _process_work_order_accrue_tax(self,company_id=False ,bulan=False,tahun=False):
        company_obj = self.env['res.company'].sudo().browse(company_id)
        start_day = '01'
        end_day = calendar.monthrange(int(tahun), int(bulan))[1]
        start_date = datetime.strptime(f"{tahun}-{bulan}-{start_day}", '%Y-%m-%d').date()
        end_date = datetime.strptime(f"{tahun}-{bulan}-{end_day}", '%Y-%m-%d').date()

        wo_obj = self.env['tw.work.order'].browse()
        count_wo_obj = 0
        amount_accrue_tax_total = 0
        for record in self.search([
            ('company_id', '=', company_id),
            ('state', 'in', ['sale','done']),
            ('date', '>=', start_date),
            ('date', '<=', end_date),
            ('accrue_tax_id', '=', False),
            ('amount_accrue_tax', '>', 0)
        ]):
            wo_obj |= record
            count_wo_obj += 1
            amount_accrue_tax_total += record.amount_accrue_tax

        if not wo_obj:
            return False

        def _prepare_journal_account_accrue_tax(company_obj):
            account_setting_obj = company_obj.branch_setting_id.account_setting_id
            if not account_setting_obj:
                raise Warning(f"Account Setting for Branch {company_obj.name} is not found")
            return account_setting_obj.journal_wo_accrue_tax_id

        def _prepare_line_ids(journal_id, name, company_obj, amount_accrue_tax_total):
            return [
                Command.create({
                    'name': name,
                    'credit': amount_accrue_tax_total,
                    'debit': 0,
                    'product_id': False,
                    'discount': 0,
                    'quantity': 1,
                    'account_id': journal_id.default_credit_account_id.id,
                    'tax_ids': False
                }),
                Command.create({
                    'name': name,
                    'credit': 0,
                    'debit': amount_accrue_tax_total,
                    'product_id': False,
                    'discount': 0,
                    'quantity': 1,
                    'account_id': journal_id.default_debit_account_id.id,
                    'tax_ids': False
                }),
            ]

        def _prepare_invoice(company_obj, bulan, tahun, count_wo_obj, amount_accrue_tax_total):
            journal_id = _prepare_journal_account_accrue_tax(company_obj)
            if not journal_id:
                raise Warning(f"Journal for Work Order Accrue Tax not found.\nPlease check configuration for branch {company_obj.name}")

            if not journal_id.default_credit_account_id or not journal_id.default_debit_account_id:
                raise Warning(f"Default Credit/Debit Account for Journal {journal_id.name} not found")

            code = journal_id.code
            prefix = company_obj.code
            bulan_string = calendar.month_name[int(bulan)]

            name = self.env['ir.sequence'].get_sequence_code(code, prefix)

            prepare_invoice = {
                'name': name,
                'ref': f'Accrue Tax WO [{prefix}] {bulan_string} {tahun} ({count_wo_obj})',
                'company_id': company_id,
                'division': 'Sparepart',
                'journal_id': journal_id.id,
                'partner_id': company_obj.partner_id.id,
                'date': fields.Date.today(),
                'move_type': 'entry', 
                'line_ids': _prepare_line_ids(journal_id, name, company_obj, amount_accrue_tax_total),
            }
            return prepare_invoice

        # Create Move
        move = self.env['account.move'].suspend_security().with_company(self.company_id).create(_prepare_invoice(company_obj, bulan, tahun, count_wo_obj, amount_accrue_tax_total))
        move.suspend_security().with_company(self.company_id).action_post()
        wo_obj.write({'accrue_tax_id': move.id})

    def _get_additional_cancel_blocking_moves(self):
        moves = super()._get_additional_cancel_blocking_moves()
        self.ensure_one()

        # Accrue tax entry is generated by scheduler and can be shared by multiple WO.
        # It must be handled manually instead of being auto-reversed from WO cancel.
        if self.accrue_tax_id and self.accrue_tax_id.state == 'posted' and not self.accrue_tax_id.reversed_entry_id:
            moves |= self.accrue_tax_id
        return moves
