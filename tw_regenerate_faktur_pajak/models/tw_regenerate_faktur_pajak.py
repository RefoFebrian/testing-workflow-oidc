# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, timedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwRegenerateFakturPajakGabungan(models.Model):
    _name = "tw.regenerate.faktur.pajak.gabungan"
    _description = "Regenerate Faktur Pajak Gabungan"
    _order = "date desc,id desc"

    # 7: defaults methods
    def _get_default_date(self):
        return self.env['res.company'].get_default_date()

    # 8: fields
    name = fields.Char('Regenerate No')
    date = fields.Date('Date', default=_get_default_date)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('post', 'Posted'),
    ], default='draft')
    # Audit Trail
    confirm_uid = fields.Many2one('res.users', string="Posted by")
    confirm_date = fields.Datetime('Posted on')

    # 9: related fields
    regenerate_line = fields.One2many(
        'tw.regenerate.faktur.pajak.gabungan.line', 'regenerate_id',
        string="Regenerate Line"
    )
    model_id = fields.Many2one(
        'ir.model', string="Form Name",
        domain="[('model','in',('tw.asset.disposal','tw.dealer.sale.order','account.move','tw.work.order'))]"
    )

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('model_id')
    def onchange_generate_line(self):
        for rec in self:
            rec.regenerate_line = [(5, 0, 0)]  # Clear existing lines

            if not rec.model_id:
                continue

            # Konfigurasi pencarian per model
            model_config = {
                'tw.dealer.sale.order': {
                    'domain': [('faktur_pajak_out_id', '=', False), ('state', 'in', ('progress', 'done'))],
                    'order': 'date_order',
                    'name_field': 'name',
                    'date_field': 'date_order',
                    'partner_field': 'partner_id',
                },
                'tw.account.payment': {
                    'domain': [('faktur_pajak_out_id', '=', False), ('type', '=', 'sale'), ('state', '=', 'posted')],
                    'order': 'date',
                    'name_field': 'name',
                    'date_field': 'date',
                    'partner_field': 'partner_id',
                },
                'account.move': {
                    'domain': [('faktur_pajak_out_id', '=', False), ('ref', '!=', False), ('state', '=', 'posted')],
                    'order': 'date',
                    'name_field': 'name',
                    'date_field': 'date',
                    'partner_field': 'partner_id',
                },
                'tw.work.order': {
                    'domain': [('faktur_pajak_out_id', '=', False), ('state', 'in', ('open', 'done'))],
                    'order': 'date',
                    'name_field': 'name',
                    'date_field': 'date',
                    'partner_field': 'partner_id',
                },
                'tw.asset.disposal': {
                    'domain': [('faktur_pajak_out_id', '=', False), ('state', '=', 'confirm')],
                    'order': 'date',
                    'name_field': 'name',
                    'date_field': 'date',
                    'partner_field': 'partner_id',
                },
            }

            config = model_config.get(rec.model_id.model)
            if not config:
                continue

            records = self.env[rec.model_id.model].search(
                config['domain'], order=config['order'], limit=100
            )

            if not records:
                rec.model_id = False
                raise UserError(_('Tidak ada data transaksi yang belum memiliki no faktur pajak !'))

            transaction = []
            for x in records:
                # Khusus tw.account.payment: hitung untaxed & tax manual
                if rec.model_id.model == 'tw.account.payment':
                    total = sum(line.amount for line in x.line_cr_ids)
                    tax = x.amount - total
                    vals = {
                        'name': getattr(x, config['name_field'], ''),
                        'untaxed_amount': total,
                        'tax_amount': tax,
                        'amount_total': x.amount,
                        'date': getattr(x, config['date_field'], False),
                        'partner_id': getattr(x, config['partner_field']).id if getattr(x, config['partner_field'], False) else False,
                        'transaction_id': x.id,
                        'model_id': rec.model_id.id,
                    }
                else:
                    partner = getattr(x, config['partner_field'], False)
                    vals = {
                        'name': getattr(x, config['name_field'], ''),
                        'untaxed_amount': x.amount_untaxed,
                        'tax_amount': x.amount_tax,
                        'amount_total': x.amount_total,
                        'date': getattr(x, config['date_field'], False),
                        'partner_id': partner.id if partner else False,
                        'transaction_id': x.id,
                        'model_id': rec.model_id.id,
                    }
                transaction.append((0, 0, vals))

            rec.regenerate_line = transaction

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].get_sequence_code_only('RFP')
            vals['date'] = self._get_default_date()
        return super(TwRegenerateFakturPajakGabungan, self).create(vals_list)

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("Regenerate Faktur Pajak sudah diproses, data tidak bisa didelete !"))
        return super(TwRegenerateFakturPajakGabungan, self).unlink()

    # 13: action methods
    def action_post(self):
        self.date = self._get_default_date()
        self.state = 'post'
        dso = self.env['tw.dealer.sale.order']
        ap = self.env['tw.account.payment']
        wo = self.env['tw.work.order']
        da = self.env['tw.asset.disposal']
        am = self.env['account.move']
        value = False

        for x in self.regenerate_line:
            no_faktur = self.get_regenerate_faktur_pajak(x.date)
            no_faktur.write({
                'model_id': x.model_id.id,
                'amount_total': x.amount_total,
                'untaxed_amount': x.untaxed_amount,
                'tax_amount': x.tax_amount,
                'state': 'close',
                'transaction_id': x.transaction_id,
                'date': x.date,
                'ref': x.name,
                'partner_id': x.partner_id.id,
                'company_id': self.env.company.id,
            })
            if not no_faktur:
                raise UserError(_("Nomor faktur pajak tidak tersedia !"))

            # cek every object
            if self.model_id.model == 'tw.dealer.sale.order':
                value = dso.browse(x.transaction_id)
            elif self.model_id.model == 'tw.account.payment':
                value = ap.browse(x.transaction_id)
            elif self.model_id.model == 'account.move':
                value = am.browse(x.transaction_id)
            elif self.model_id.model == 'tw.work.order':
                value = wo.browse(x.transaction_id)
            elif self.model_id.model == 'tw.asset.disposal':
                value = da.browse(x.transaction_id)

            # cek existence
            if not value:
                raise UserError(_("No %s tidak ditemukan !") % x.name)
            if value.faktur_pajak_out_id:
                raise UserError(_("No %s sudah memiliki faktur pajak !") % x.name)

            # write value
            value.write({'faktur_pajak_out_id': no_faktur.id, 'is_combined_tax': False})
            x.write({'faktur_pajak_out_id': no_faktur.id})

    # 14: private methods
    def get_regenerate_faktur_pajak(self, release_date):
        faktur_pajak = self.env['tw.faktur.pajak.out']
        thn_penggunaan = int(str(release_date)[:4])

        no_fp = faktur_pajak.search([
            ('state', '=', 'open'),
            # ('thn_penggunaan', '=', thn_penggunaan), # field tidak ada
            ('release_date', '<=', release_date)
        ], limit=1, order='release_date')

        if not no_fp:
            raise UserError(_("Nomor faktur pajak tidak ditemukan, silahkan Generate terlebih dahulu !"))
        return no_fp