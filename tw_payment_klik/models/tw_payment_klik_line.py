
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

class ReportPaymentKlikLine(models.Model):
    _name = "tw.payment.klik.line"
    _description = "Payment Klik line"

    
    name = fields.Char(string='Name')
    state = fields.Selection(string='State', selection=[
        ('draft', 'Draft'),
        ('verify', 'Verify'),
        ('approve_1', 'Approved (1 of 2)'),
        ('approve', 'Approved (2 of 2)'),
        ('reject', 'Rejected'),
        ('done', 'Done'),
    ],default='draft')
    model_name = fields.Char(string='Model name')
    paid_amount = fields.Char(string='Paid Amount')
    rek_tujuan = fields.Char(string='Rek Tujuan')
    bank_tujuan = fields.Char(string='Bank Tujuan')
    transaction_id = fields.Integer(string='id')
    to_post = fields.Boolean('Scheduled to Post')
    payment_klik_uid = fields.Many2one('res.users','Payment Klik by')
    is_single_click = fields.Boolean('Single Click')
    failure_note = fields.Text('failure_note')

    # * Fields used as History Monitoring Payment Klik
    verify_date = fields.Datetime('Verified on', help='The time this record been Verified in Monitoring menu')
    verify_uid = fields.Many2one('res.users', 'Verified by', help='The user whom Verified this record in Monitoring menu')
    approve_1_date = fields.Datetime('#1 Approval on', help='The time this record been Approved in Monitoring menu')
    approve_1_uid = fields.Many2one('res.users', '#1 Approval by', help='The user whom Approved this record in Monitoring menu')
    approve_date = fields.Datetime('#2 Approval on', help='The time this record been Approved in Monitoring menu')
    approve_uid = fields.Many2one('res.users', '#2 Approval by', help='The user whom Approved this record in Monitoring menu')
    reject_date = fields.Datetime('Rejected on', help='The time this record been Rejected in Monitoring menu')
    reject_uid = fields.Many2one('res.users', 'Rejected by', help='The user whom Rejected this record in Monitoring menu')
    reject_reason = fields.Char('Reject Reason')
    process_date = fields.Datetime('Processed on', help='The time this record been Processed in Monitoring menu')
    process_uid = fields.Many2one('res.users', 'Processed by', help='The user whom Processed this record in Monitoring menu')

    bank_id = fields.Many2one('res.bank', string='Bank')
    payment_klik_id = fields.Many2one(comodel_name='tw.payment.klik', string='Payment')
    journal_id = fields.Many2one("account.journal","Payment Method")
    bank_account_id = fields.Many2one("res.partner.bank", "Bank Asal")
    bank_account_dest_id = fields.Many2one("res.partner.bank", "Bank Tujuan")

    # * Transactions (must only be filled one of these at any given time)
    supplier_payment_id = fields.Many2one('tw.account.payment', 'Supplier Payment')
    advance_payment_id = fields.Many2one('tw.advance.payment', 'Advance Payment')
    settlement_advance_payment_id = fields.Many2one('tw.settlement', 'Settlement Advance Payment')
    bank_transfer_id = fields.Many2one('tw.bank.transfer', 'Bank Transfer')

    def post_transactions(self, limit=False, id=False):
        """ Args usage example for search with limit of 50: (None,50).
            Example for search by id of 123: (None,False,123) """
        datas = self
        if not datas:
            dom = [('to_post','=',True)]
            if id:
                dom.append(('id','=',int(id)))
            datas = self.search(dom,limit=limit)
        if not datas:
            _logger.error('post_transactions: No available data to execute!')
            return False
        for each in datas:
            if each.supplier_payment_id and each.supplier_payment_id.state != 'paid':
                try:
                    each.supplier_payment_id.action_validate()
                    self._cr.commit()
                except Exception as e:
                    self._cr.rollback()
                    each.write({
                        'to_post':False,
                        'failure_note':'Supplier Payment : '+str(e),
                    })
            elif each.advance_payment_id:
                try:
                    if each.advance_payment_id.state not in ('confirm','done'):
                        each.advance_payment_id.action_confirm()
                    elif each.advance_payment_id.state == 'done':
                        each.advance_payment_id.write({'state':'confirm'})
                    self._cr.commit()
                except Exception as e:
                    self._cr.rollback()
                    each.write({
                        'to_post':False,
                        'failure_note':'Advance Payment : '+str(e),
                    })
            elif each.settlement_advance_payment_id and each.settlement_advance_payment_id.state != 'done':
                try:
                    each.settlement_advance_payment_id.action_confirm()
                    self._cr.commit()
                except Exception as e:
                    self._cr.rollback()
                    each.write({
                        'to_post':False,
                        'failure_note':'Settlement Advance Payment : '+str(e),
                    })
            elif each.bank_transfer_id and each.bank_transfer_id.state != 'posted':
                try:
                    each.bank_transfer_id.action_confirm()
                    self._cr.commit()
                except Exception as e:
                    self._cr.rollback()
                    each.write({
                        'to_post':False,
                        'failure_note':'Bank Transfer : '+str(e),
                    })
            else:
                if each.model_name and each.transaction_id:
                    try:
                        model = each.model_name
                        # * Why not use browse instead? because browse literally just returns the object
                        # * with the designated ID regardless of the object/record is actually exists or not
                        trx_id = self.env[model].sudo().search([('id','=',each.transaction_id)])
                        if not trx_id:
                            _logger.error('post_transactions: Record %s with ID %s does not found!' % (
                                model,each.transaction_id
                            ))
                            continue
                        if model == 'tw.account.payment':
                            if trx_id.state != 'paid':
                                trx_id.action_validate()
                        elif model == 'tw.advance.payment':
                            if trx_id.state not in ('paid','done'):
                                trx_id.action_confirm()
                            elif trx_id.state == 'done':
                                trx_id.write({'state':'confirm'})
                        elif model == 'tw.settlement':
                            if trx_id.state != 'done':
                                trx_id.action_confirm()
                        elif model == 'tw.bank.transfer':
                            if trx_id.state != 'approved':
                                trx_id.action_confirm()
                        else:
                            _logger.error('post_transactions: Model %s is not Payment Klik!' % model)
                        self._cr.commit()
                    except Exception as e:
                        self._cr.rollback()
                        each.write({
                            'to_post':False,
                            'failure_note':'Else : '+str(e),
                        })
                else:
                    _logger.error('post_transactions: ID %s has No transactions!' % each.id)
            each.write({'to_post': False})
            