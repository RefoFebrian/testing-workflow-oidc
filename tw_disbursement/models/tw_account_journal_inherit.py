# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, Command,_

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TWAccountJournalInherit(models.Model):
    _inherit = "account.journal"
    
    # 7: defaults methods

    # 8: fields
    type = fields.Selection(selection_add=[('edc', 'EDC')], ondelete={"edc": "cascade"})

    # 9: relation fields
    # Di inherit supaya include EDC sebagai eligible journal untuk payment
    inbound_payment_method_line_ids = fields.One2many(
        comodel_name='account.payment.method.line',
        domain=[('payment_type', '=', 'inbound')],
        compute='_compute_inbound_payment_method_line_ids',
        store=True,
        readonly=False,
        string='Inbound Payment Methods',
        inverse_name='journal_id',
        copy=False,
        check_company=True,
        help="Manual: Get paid by any method outside of Odoo.\n"
        "Payment Providers: Each payment provider has its own Payment Method. Request a transaction on/to a card thanks to a payment token saved by the partner when buying or subscribing online.\n"
        "Batch Deposit: Collect several customer checks at once generating and submitting a batch deposit to your bank. Module account_batch_payment is necessary.\n"
        "SEPA Direct Debit: Get paid in the SEPA zone thanks to a mandate your partner will have granted to you. Module account_sepa is necessary.\n"
    )
    outbound_payment_method_line_ids = fields.One2many(
        comodel_name='account.payment.method.line',
        domain=[('payment_type', '=', 'outbound')],
        compute='_compute_outbound_payment_method_line_ids',
        store=True,
        readonly=False,
        string='Outbound Payment Methods',
        inverse_name='journal_id',
        copy=False,
        check_company=True,
        help="Manual: Pay by any method outside of Odoo.\n"
        "Check: Pay bills by check and print it from Odoo.\n"
        "SEPA Credit Transfer: Pay in the SEPA zone by submitting a SEPA Credit Transfer file to your bank. Module account_sepa is necessary.\n"
    )
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods

    @api.depends('type', 'currency_id')
    def _compute_inbound_payment_method_line_ids(self):
        for journal in self:
            pay_method_line_ids_commands = [Command.clear()]
            payment_types = self.env['tw.account.payment']._get_available_journal_type()
            if journal.type in payment_types:
                default_methods = journal._default_inbound_payment_methods()
                pay_method_line_ids_commands += [Command.create({
                    'name': pay_method.name,
                    'payment_method_id': pay_method.id,
                }) for pay_method in default_methods]
            journal.inbound_payment_method_line_ids = pay_method_line_ids_commands

    @api.depends('type', 'currency_id')
    def _compute_outbound_payment_method_line_ids(self):
        for journal in self:
            pay_method_line_ids_commands = [Command.clear()]
            payment_types = self.env['tw.account.payment']._get_available_journal_type()
            if journal.type in payment_types:
                default_methods = journal._default_outbound_payment_methods()
                pay_method_line_ids_commands += [Command.create({
                    'name': pay_method.name,
                    'payment_method_id': pay_method.id,
                }) for pay_method in default_methods]
            journal.outbound_payment_method_line_ids = pay_method_line_ids_commands
