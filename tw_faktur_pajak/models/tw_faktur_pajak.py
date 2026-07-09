from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning, ValidationError

from datetime import date

class FakturPajak(models.Model):
    _name = "tw.faktur.pajak"
    _description = "Generate Faktur Pajak"
    _order = "id asc"
         
    def _get_default_date(self):
        return date.today().strftime("%Y-%m-%d")

    def _get_company_domain(self):
        parent_id = self.env.company.parent_id.id or self.env.company.id
        return [('id', 'child_of', parent_id)]

    name = fields.Char(string='Faktur Pajak', compute='_compute_name', store=True)
    prefix = fields.Char(string='Prefix', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
    ], default='draft')

    counter_start = fields.Integer(string='Counter Start', required=True, default=1)
    counter_end = fields.Integer(string='Counter End', required=True, default=2)
    padding = fields.Integer(string='Padding', required=True, default=8)
    
    date = fields.Date(string='Date', required=True, default=_get_default_date)
    release_date = fields.Date(string="Release Date")
    year = fields.Char(string="Tahun Penggunaan", size=4)

    company_id = fields.Many2one('res.company', string='Branch', required=True, default=lambda self: self.env.company, domain=_get_company_domain)
    confirm_uid = fields.Many2one('res.users', string="Posted by")

    @api.constrains('year')
    def _check_year_format(self):
        for record in self:
            if record.year:
                if len(record.year) != 4 or not record.year.isdigit():
                    raise ValidationError(_("Tahun Penggunaan must be a 4-digit number (e.g. 2024)."))

    confirm_date = fields.Datetime('Posted on')
    
    faktur_pajak_ids = fields.One2many('tw.faktur.pajak.out', 'faktur_pajak_id', 'Faktur Pajak Out', readonly=True)
    origin = fields.Char('Origin')

    def _compute_name(self):
        for record in self:
            seq_name = self.env['ir.sequence'].with_company(self.env.user.company_id).get_sequence_code('FP', 'TH')
            record.name = seq_name
        
    @api.onchange('counter_start', 'counter_end')
    def counter_start_change(self):
        warning_msg = None
        if self.counter_start <= 0:
            self.counter_start = 1
            self.counter_end = self.counter_start + 1
            warning_msg = 'Counter Start Must Greater Then 0'
        
        if self.counter_end <= self.counter_start:
            self.counter_end = self.counter_start + 1
        
        if self.padding <= 0:
            warning_msg = 'Padding Must Greater Then 0.'
        
        if warning_msg:
            raise Warning(f"Attention!, {warning_msg}")
    
    @api.model_create_multi
    def create(self, vals_list):
        return super().create(vals_list)

    def unlink(self):
        for item in self:
            if item.state != 'draft':
                raise Warning("Failed to Delete data because the 'Faktur Pajak' has been Processed or Generated.")
        return super(FakturPajak, self).unlink()
    
    def action_post(self):
        padding = "{0:0" + str(self.padding) + "d}"
        vals = []
        for number in range(self.counter_start,self.counter_end+1):
            vals.append([0,0,{
                'name': self.prefix + padding.format(number),
                'state': 'open',
                'release_date': self.release_date,
                'company_id': self.company_id.id,
                'year': self.year
            }])

        self.sudo().write({
            'faktur_pajak_ids': vals,
            'date':self._get_default_date(),
            'state':'posted',
            'confirm_uid':self._uid,
            'confirm_date':self._get_default_date()
        })