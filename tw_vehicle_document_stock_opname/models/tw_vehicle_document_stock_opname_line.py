from odoo import models, fields, api

class TwVehicleDocumentStockOpnameLine(models.Model):
    _name = "tw.vehicle.document.stock.opname.line"
    _description = "Vehicle Document Stock Opname Line"

    location_ownership = fields.Char('Lokasi BPKB')
    location_registration = fields.Char('Lokasi STNK')
    ownership_number = fields.Char('No BPKB')
    plate_number = fields.Char('No Polisi')
    date_receipt = fields.Date('Tanggal Penerimaan')
    age = fields.Char('Umur')
    over_due = fields.Char('Over Due (Hari)')
    description = fields.Char('Keterangan')

    validation_name_ownership = fields.Selection(string="Validasi Nama BPKB", selection=lambda self: self._get_selection_options('ValNamaBpkb'))
    validation_no_engine_ownership = fields.Selection(string="Validasi No Engine", selection=lambda self: self._get_selection_options('ValNoEngBpkb'))
    validation_no_ownership = fields.Selection(string="Validasi No BPKB", selection=lambda self: self._get_selection_options('ValNoBpkb'))
    validation_check_physical_ownership = fields.Selection(string="Ceklis Fisik BPKB", selection=lambda self: self._get_selection_options('CekFisikBpkb'))

    validation_name_registration = fields.Selection(string="Validasi Nama STNK", selection=lambda self: self._get_selection_options('ValNamaStnk'))
    validation_no_engine_registration = fields.Selection(string="Validasi No Engine STNK", selection=lambda self: self._get_selection_options('ValNoEngStnk'))
    validation_plate_number = fields.Selection(string="Validasi No Polisi", selection=lambda self: self._get_selection_options('ValNoPolisi'))
    validation_check_physical_registration = fields.Selection(string="Ceklis Fisik STNK", selection=lambda self: self._get_selection_options('CekFisikStnk'))

    opname_id = fields.Many2one('tw.vehicle.document.stock.opname', 'Stock Opname', ondelete='cascade')
    lot_id = fields.Many2one('stock.lot', 'No Engine')
    customer_ownership_id = fields.Many2one('res.partner', 'Customer BPKB')
    customer_registration_id = fields.Many2one('res.partner', 'Customer STNK')
    finco_id = fields.Many2one('res.partner', 'Finance Company')

    @api.onchange('validation_check_physical_ownership', 'validation_check_physical_registration')
    def onchange_check_physical(self):
        if self.validation_check_physical_ownership:
            if self.validation_check_physical_ownership != 'Fisik Ada':
                self.validation_name_ownership = '-'
                self.validation_no_engine_ownership = '-'
                self.validation_no_ownership = '-'
            else:
                self.validation_name_ownership = False
                self.validation_no_engine_ownership = False
                self.validation_no_ownership = False

        if self.validation_check_physical_registration:
            if self.validation_check_physical_registration != 'Fisik Ada':
                self.validation_name_registration = '-'
                self.validation_no_engine_registration = '-'
                self.validation_plate_number = '-'
            else:
                self.validation_name_registration = False
                self.validation_no_engine_registration = False
                self.validation_plate_number = False

    @api.onchange('validation_name_ownership')
    def _onchange_validation_name_ownership(self):
        if not self.validation_name_ownership:
            return
        if self.validation_check_physical_ownership == 'Fisik Ada' and self.validation_name_ownership == '-':
            self.validation_name_ownership = False
            return {'warning': {'title': 'Perhatian!', 'message': 'Validasi Nama BPKB tidak boleh - !'}}
        if self.validation_check_physical_ownership != 'Fisik Ada' and self.validation_name_ownership not in ('-', False):
            self.validation_name_ownership = False
            return {'warning': {'title': 'Perhatian!', 'message': 'Validasi Nama BPKB tidak boleh selain - !'}}

    @api.onchange('validation_no_ownership')
    def _onchange_validation_no_ownership(self):
        if not self.validation_no_ownership:
            return
        if self.validation_check_physical_ownership == 'Fisik Ada' and self.validation_no_ownership == '-':
            self.validation_no_ownership = False
            return {'warning': {'title': 'Perhatian!', 'message': 'Validasi No BPKB tidak boleh - !'}}
        if self.validation_check_physical_ownership != 'Fisik Ada' and self.validation_no_ownership not in ('-', False):
            self.validation_no_ownership = False
            return {'warning': {'title': 'Perhatian!', 'message': 'Validasi No BPKB tidak boleh selain - !'}}

    @api.onchange('validation_no_engine_ownership')
    def _onchange_validation_no_engine_ownership(self):
        if not self.validation_no_engine_ownership:
            return
        if self.validation_check_physical_ownership == 'Fisik Ada' and self.validation_no_engine_ownership == '-':
            self.validation_no_engine_ownership = False
            return {'warning': {'title': 'Perhatian!', 'message': 'Validasi No Engine BPKB tidak boleh - !'}}
        if self.validation_check_physical_ownership != 'Fisik Ada' and self.validation_no_engine_ownership not in ('-', False):
            self.validation_no_engine_ownership = False
            return {'warning': {'title': 'Perhatian!', 'message': 'Validasi No Engine BPKB tidak boleh selain - !'}}

    @api.onchange('validation_name_registration')
    def _onchange_validation_name_registration(self):
        if not self.validation_name_registration:
            return
        if self.validation_check_physical_registration == 'Fisik Ada' and self.validation_name_registration == '-':
            self.validation_name_registration = False
            return {'warning': {'title': 'Perhatian!', 'message': 'Validasi Nama STNK tidak boleh - !'}}
        if self.validation_check_physical_registration != 'Fisik Ada' and self.validation_name_registration not in ('-', False):
            self.validation_name_registration = False
            return {'warning': {'title': 'Perhatian!', 'message': 'Validasi Nama STNK tidak boleh selain - !'}}

    @api.onchange('validation_plate_number')
    def _onchange_validation_plate_number(self):
        if not self.validation_plate_number:
            return
        if self.validation_check_physical_registration == 'Fisik Ada' and self.validation_plate_number == '-':
            self.validation_plate_number = False
            return {'warning': {'title': 'Perhatian!', 'message': 'Validasi No Polisi tidak boleh - !'}}
        if self.validation_check_physical_registration != 'Fisik Ada' and self.validation_plate_number not in ('-', False):
            self.validation_plate_number = False
            return {'warning': {'title': 'Perhatian!', 'message': 'Validasi No Polisi tidak boleh selain - !'}}

    @api.onchange('validation_no_engine_registration')
    def _onchange_validation_no_engine_registration(self):
        if not self.validation_no_engine_registration:
            return
        if self.validation_check_physical_registration == 'Fisik Ada' and self.validation_no_engine_registration == '-':
            self.validation_no_engine_registration = False
            return {'warning': {'title': 'Perhatian!', 'message': 'Validasi No Engine STNK tidak boleh - !'}}
        if self.validation_check_physical_registration != 'Fisik Ada' and self.validation_no_engine_registration not in ('-', False):
            self.validation_no_engine_registration = False
            return {'warning': {'title': 'Perhatian!', 'message': 'Validasi No Engine STNK tidak boleh selain - !'}}

    def write(self, vals):
        if vals.get('validation_check_physical_ownership'):
            if vals['validation_check_physical_ownership'] != 'Fisik Ada':
                vals['validation_name_ownership'] = '-'
                vals['validation_no_engine_ownership'] = '-'
                vals['validation_no_ownership'] = '-'
        if vals.get('validation_check_physical_registration'):
            if vals['validation_check_physical_registration'] != 'Fisik Ada':
                vals['validation_name_registration'] = '-'
                vals['validation_no_engine_registration'] = '-'
                vals['validation_plate_number'] = '-'
        return super().write(vals)

    @api.model
    def _get_selection_options(self, type_name):
        selection_obj = self.env['tw.selection'].get_option_list(type_name)
        return selection_obj or [('-', '-')]
