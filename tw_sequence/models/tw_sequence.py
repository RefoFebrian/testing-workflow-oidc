from odoo import models, fields, api
from datetime import date, datetime

class Sequence(models.Model):
    _inherit = "ir.sequence"

    def _next(self, sequence_date=None):
        sequence = self.with_context(tz='Asia/Jakarta')
        if not sequence.use_date_range:
            return sequence._next_do()

        dt = sequence_date or self._context.get('ir_sequence_date')
        if not dt:
            dt = fields.Date.context_today(sequence)

        seq_date = self.env['ir.sequence.date_range'].search([
            ('sequence_id', '=', self.id),
            ('date_from', '<=', dt),
            ('date_to', '>=', dt),
        ], limit=1)
        if not seq_date:
            seq_date = self._create_date_range_seq(dt)

        return seq_date.with_context(
            tz='Asia/Jakarta',
            ir_sequence_date_range=seq_date.date_from,
        )._next()

    def get_sequence_code(self, code, prefix, sequence_date=None):
        company_id = self.env.company.id
        seq_name = '{0}/{1}'.format(code,prefix)
        seq_id = self.search([('name', '=', seq_name), ('company_id', 'in', [company_id, False])], limit=1, order='company_id')
        if not seq_id:
            prefix = '/%(y)s/%(month)s/'
            prefix = seq_name + prefix
            vals = {
                'name': seq_name,
                'implementation': 'no_gap',
                'prefix': prefix,
                'padding': 5,
                'use_date_range': True,
                'company_id': False
            }
            seq_id = self.sudo().create(vals)
        return seq_id._next(sequence_date=sequence_date)

    def get_sequence_code_with_date(self, code, prefix, sequence_date=None):
        company_id = self.env.company.id
        year = sequence_date.strftime('%y')
        month = sequence_date.strftime('%m')
        sequence = '{0}/{1}/{2}/{3}/'.format(code,prefix,year,month)
        seq_id = self.search([('name', '=', sequence), ('company_id', 'in', [company_id, False])], limit=1, order='company_id')
        if not seq_id:
            vals = {
                'name': sequence,
                'implementation': 'no_gap',
                'prefix': sequence,
                'padding': 5,
                'use_date_range': True,
                'company_id': False
            }
            seq_id = self.sudo().create(vals)
        return seq_id._next(sequence_date=sequence_date)

    def get_sequence_code_only(self, code, sequence_date=None):
        company_id = self.env.company.id
        seq_name = code
        seq_id = self.search([('name', '=', seq_name), ('company_id', 'in', [company_id, False])], limit=1, order='company_id')
        if not seq_id:
            suffix = '%(y)s'
            prefix = seq_name + suffix
            vals = {
                'name': seq_name,
                'implementation': 'no_gap',
                'prefix': prefix,
                'padding': 5,
                'use_date_range': True,
                'company_id': False
            }
            seq_id = self.sudo().create(vals)
        return seq_id._next(sequence_date=sequence_date)
