from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning, ValidationError


class FakturPajakOut(models.Model):
    _name = "tw.faktur.pajak.out"
    _description = "Faktur Pajak"

    name = fields.Char(string='Faktur Pajak')
    transaction_id = fields.Integer('Transaction ID')
    state = fields.Selection([
        ('open', 'Open'),
        ('close', 'Closed'),
        ('print', 'Printed'),
        ('cancel', 'Canceled'),
    ], default='open')
    
    date = fields.Date('Date')
    transaction_code = fields.Char(string="Transaction Code")
    ref = fields.Char(string="Reference")
    note = fields.Text(string="Note")

    is_combined_tax = fields.Boolean('Combined Tax?')
    
    printed_count = fields.Integer('Printed Count')
    release_date = fields.Date(string="Release Date")
    year = fields.Char(string="Tahun Penggunaan", size=4)

    tax_amount = fields.Float('Tax Amount')
    untaxed_amount = fields.Float('Untaxed Amount')
    amount_total = fields.Float('Total Amount')

    # Audit Trail
    cancel_date = fields.Date(string="Cancel Date")
    cancel_uid = fields.Many2one('res.users', string="Canceled by")

    faktur_pajak_id = fields.Many2one('tw.faktur.pajak', 'Generate Faktur Pajak')
    company_id = fields.Many2one('res.company', string="Branch", domain=[('parent_id', '!=', False)])

    partner_id = fields.Many2one('res.partner', string='Partner')
    model_id = fields.Many2one('ir.model', string='Model')

    _sql_constraints = [
        ('unique_faktur_pajak_name', 'unique(name)', 'Number of Faktur Pajak Has been Created!'),
    ]

    @api.constrains('year')
    def _check_year_format(self):
        for record in self:
            if record.year:
                if len(record.year) != 4 or not record.year.isdigit():
                    raise ValidationError(_("Tahun Penggunaan must be a 4-digit number (e.g. 2024)."))

    @api.depends('ref','name')
    def _compute_display_name(self):
        for record in self:
            name = record.name
            if record.ref:
                name = f"{record.ref} - {name} "
            record.display_name = name

    def name_get(self):
        if self._context is None:
            self._context = {}
        res = []
        for record in self:
            tit = "%s" % (record.name)
            if record.ref:
                tit = "[%s] - %s" % (record.ref, record.name)
            res.append((record.id, tit))
        return res


    def unlink(self):
        raise Warning("You are not Allowed to Delete This Data!")


    # Action Method
    def action_cancel(self):
        """Membatalkan Faktur Pajak."""
        for record in self:
            if record.state == 'cancel':
                raise Warning("Faktur Pajak already canceled!")
            
            record.write({
                'state': 'cancel',
                'cancel_date': fields.Date.today(),
                'cancel_uid': self._uid,
            })

    # Non Core Tax Implementation
    def get_number_of_faktur_pajak(self, object_name, transaction_id=None):
        """
        Mengambil nomor faktur pajak berdasarkan transaction id.
        Non Core Tax Implementation — assign nomor dari faktur pajak 'open'.

        :param object_name: nama model sumber (e.g., 'sale.order').
        :param transaction_id: ID dari record transaksi.
        :return: recordset tw.faktur.pajak.out yang di-assign.
        """
        transaction_id = transaction_id if transaction_id else self.transaction_id
        object = self.env[object_name].browse(transaction_id)
        release_date = object.date_order if hasattr(object, 'date_order') else object.date

        company_id = object.company_id.id if hasattr(object, 'company_id') else self.env.company.id
        company = self.env['res.company'].browse(company_id)
        company_ids = [company.id]
        if company.parent_id:
            company_ids.append(company.parent_id.id)
        
        fpo_obj = self.env['tw.faktur.pajak.out'].sudo().search([
            ('state', '=', 'open'),
            ('release_date', '<=', release_date),
            ('company_id', 'in', company_ids),
        ], limit=1, order='release_date')

        if not fpo_obj and object_name == 'tw.account.payment':
            raise Warning("Number of 'Faktur Pajak' not found, Please Generate First!")

        if fpo_obj:
            # Write to faktur_pajak_out_id (from mixin) instead of faktur_pajak_id
            object.write({'faktur_pajak_out_id': fpo_obj.id})
            model = self.env['ir.model'].search([('model', '=', object_name)], limit=1)

            fpo_obj.write({
                'model_id': model.id,
                'amount_total': object.amount_total if hasattr(object, 'amount_total') else object.amount,
                'untaxed_amount': object.amount_untaxed if hasattr(object, 'amount_untaxed') else object.untaxed_amount,
                'tax_amount': object.amount_tax if hasattr(object, 'amount_tax') else object.tax_amount,
                'state': 'close',
                'transaction_id': object.id,
                'date': release_date,
                'partner_id': object.partner_id.id if hasattr(object, 'partner_id') else object.customer_id.id,
                'ref': object.name,
                'company_id': object.company_id.id if hasattr(object, 'company_id') else False,
            })
        
        return fpo_obj
        
