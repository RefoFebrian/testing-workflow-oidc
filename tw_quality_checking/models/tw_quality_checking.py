import base64
import io
import qrcode

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError as Warning


class QualityChecking(models.Model):
    _name = "tw.quality.checking"
    _description = "Quality Checking"

    def _get_default_date(self):
        return self.env['res.company'].get_default_date()

    name = fields.Char('Name')
    date = fields.Date('Tanggal Input', default=_get_default_date)
    state = fields.Selection([('draft','Draft'),('done','Done')], default='draft')
    print_counter = fields.Integer('Jumlah Cetak')
    number_of_boxes = fields.Integer('Jumlah Kardus')
    weight_box = fields.Float('Berat Kardus', compute='_compute_weight_box', store=True)

    company_id = fields.Many2one('res.company', string="Branch")
    stockcard_ids = fields.Many2many('stock.picking', 'tw_quality_checking_stockcard_rel', 'quality_checking_id', 'picking_id', string='Stock Picking')
    cardboard_id = fields.Many2one('tw.selection', string='Dimensi Kardus', domain=[('type', '=', 'CardboardDimensions')])
    quality_checking_ids = fields.One2many('tw.quality.checking.line', 'quality_checking_id', string='Detail')

    file = fields.Binary(string='File Upload')
    file_show = fields.Binary(string='File', compute='_compute_file')
    filename = fields.Char(string='Filename')

    confirm_uid = fields.Many2one('res.users', 'Confirmed by')
    confirm_date = fields.Datetime('Confirmed on')

    @api.depends('quality_checking_ids.weight')
    def _compute_weight_box(self):
        """Menghitung total berat kardus dari semua line items (dalam kg)."""
        for rec in self:
            total_weight_gram = sum(rec.quality_checking_ids.mapped('weight'))
            rec.weight_box = total_weight_gram / 1000  # Convert gram to kg

    @api.depends('filename')
    def _compute_file(self):
        for rec in self:
            rec.file_show = False
            if rec.filename:
                rec.file_show = self.env['tw.config.files'].suspend_security().get_file(rec.filename)
        
    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if values.get('company_id') and values.get('name', 'New') == _('New'):
                branch_src = self.env['res.company'].suspend_security().search([
                    ('id', '=', values['company_id'])
                ], limit=1)
                values['name'] = self.env['ir.sequence'].get_sequence_code('CARTOON', str(branch_src.code))

            if not values.get('quality_checking_ids'):
                raise Warning(_('Peringatan! \nTidak dapat membuat transaksi tanpa detail!'))

        return super().create(vals_list)
    
    def unlink(self):
        for record in self:
            if record.state and record.state != 'draft':
                raise Warning(_('Peringatan! \nTidak dapat menghapus data dengan status selain draft!'))
        return super().unlink()

    @api.onchange('stockcard_ids')
    def _onchange_stockcard_ids(self):
        lines = []
        for picking in self.stockcard_ids:
            for move in picking.move_ids:
                lines.append((0, 0, {
                    'picking_id': picking.id,
                    'product_id': move.product_id.id,
                    'quantity': int(move.product_uom_qty),
                    'qty_supply': 0,
                    'weight': 0.0,
                }))

        self.quality_checking_ids = [(5, 0, 0)] + lines

    def action_confirm(self):
        self.ensure_one()

        # Update picking
        if self.stockcard_ids:
            for picking in self.stockcard_ids:
                picking.write({
                    'quality_checking_id': self.id
                })

        # Update quality checking
        return self.write({
            'state': 'done',
            'confirm_uid': self.env.user.id,
            'confirm_date': fields.Datetime.now(),
        })

    def action_print_thermal_report(self):
        if self.state != 'done':
            raise Warning('Cetak Thermal hanya dapat dilakukan setelah status Transaksi berubah menjadi Done.')
        
        self.ensure_one()
        return self.env.ref('tw_quality_checking.action_report_tw_quality_checking').report_action(self.id)

    def action_print_cartoon_pdf(self):
        """Generate CARTOON PDF Report dan simpan ke file storage."""
        if self.state != 'done':
            raise Warning('Cetak CARTOON PDF hanya dapat dilakukan setelah status Transaksi berubah menjadi Done.')
        
        self.ensure_one()
        
        # Generate PDF content
        report = self.env.ref('tw_quality_checking.action_report_tw_cartoon_pdf')
        pdf_content, _ = report._render_qweb_pdf(report.id, [self.id])
        
        # Save to file storage (encode ke base64 karena upload_file expects base64)
        filename = f"{self.name.replace('/', '_')}.pdf"
        pdf_base64 = base64.b64encode(pdf_content)
        self.env['tw.config.files'].suspend_security().upload_file(filename, pdf_base64)
        
        # Update filename field
        self.write({'filename': filename})
        
        # Return report action untuk display PDF
        return report.report_action(self.id)

    def _generate_qr_code(self):
        """Generate QR code untuk download PDF CARTOON transaksi ini.
        Menggunakan library qrcode (standar Odoo) untuk menghindari dependency Cairo.
        """
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        # Jika file sudah ada, gunakan URL download file
        if self.filename:
            url = (
                f"{base_url}/web/content/tw.quality.checking/"
                f"{self.id}/file_show/{self.filename}"
            )
        else:
            # Jika file belum ada, generate dan simpan dulu
            report = self.env.ref('tw_quality_checking.action_report_tw_cartoon_pdf')
            pdf_content, _ = report.suspend_security()._render_qweb_pdf(report.id, [self.id])
            
            filename = f"{self.name.replace('/', '_')}.pdf"
            pdf_base64 = base64.b64encode(pdf_content)
            self.env['tw.config.files'].suspend_security().upload_file(filename, pdf_base64)
            self.sudo().write({'filename': filename})

            url = (
                f"{base_url}/web/content/tw.quality.checking/"
                f"{self.id}/file_show/{filename}"
            )

        # Generate QR code menggunakan library qrcode (tidak butuh Cairo)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=4,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_image = buffer.getvalue()
        
        return f"data:image/png;base64,{base64.b64encode(qr_image).decode('utf-8')}"

    def _generate_simple_qr_code(self):
        self.ensure_one()
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=4,
            border=2,
        )
        qr.add_data(self.name or '')
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_image = buffer.getvalue()
        
        return f"data:image/png;base64,{base64.b64encode(qr_image).decode('utf-8')}"

