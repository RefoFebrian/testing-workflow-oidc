# 1: imports of python lib
from datetime import date, datetime, timedelta, time
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwVehicleDocumentStockOpname(models.Model):
    _name = "tw.vehicle.document.stock.opname"
    _description = "Vehicle Document Stock Opname"
    _inherit = ["tw.attachment.mixin"]
    _order = "id desc"

    # 7: defaults methods
    @api.model
    def _get_default_date(self):
        return self.env['res.company'].get_default_date()

    @api.model
    def _get_default_datetime(self):
        return datetime.now()

    # 8: fields
    name = fields.Char('Nama', compute='_compute_name', store=True, index=True, readonly=True)
    date = fields.Date('Tanggal SO', default=_get_default_date)
    post_date = fields.Datetime('Posted on')
    generate_date = fields.Datetime('Generate on')
    state = fields.Selection([('draft', 'Draft'), ('open', 'Open'), ('posted', 'Posted')], default="draft")
    division = fields.Selection([('Unit', 'Unit')], default="Unit")
    note_bakso = fields.Text('Note')
    is_pilot = fields.Boolean(string='Is Pilot?', compute='_compute_is_pilot', store=True)
    document_type = fields.Selection([('stnk', 'STNK'), ('bpkb', 'BPKB')], string="Document Type", required=True)

    # 9: relation fields
    company_id = fields.Many2one('res.company', 'Branch', index=True)
    post_uid = fields.Many2one('res.users', 'Posted by')
    staff_bbn_id = fields.Many2one('hr.employee','Staff BBN', domain="[('company_id', '=', company_id)]")
    adh_id = fields.Many2one('hr.employee','ADH', domain="[('job_id.name', 'in', ('ADMINISTRATION HEAD','ADMINISTRATION HEAD MD')), ('company_id', '=', company_id)]")
    soh_id = fields.Many2one('hr.employee','SOH', domain="[('job_id.name', 'in', ('SALES OPERATION HEAD', 'BRANCH HEAD')), ('company_id', '=', company_id)]")
    detail_bpkb_ids = fields.One2many('tw.vehicle.document.stock.opname.line', 'opname_id')
    detail_stnk_ids = fields.One2many('tw.vehicle.document.stock.opname.line', 'opname_id')
    other_bpkb_ids = fields.One2many('tw.vehicle.document.stock.opname.other', 'opname_id')
    other_stnk_ids = fields.One2many('tw.vehicle.document.stock.opname.other', 'opname_id')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('company_id')
    def _compute_is_pilot(self):
        for rec in self:
            is_pilot = False
            if rec.company_id:
                pilot_branches = self.env['tw.pilot.project'].sudo().search([
                    ('name', '=', 'ATTACHMENT STOCK OPNAME'),
                    ('active', '=', True),
                    ('company_ids', 'in', rec.company_id.id)
                ], limit=1)
                if pilot_branches:
                    is_pilot = True
            rec.is_pilot = is_pilot

    @api.depends('company_id', 'document_type')
    def _compute_name(self):
        for rec in self:
            if not rec.company_id or not rec.document_type:
                rec.name = False
                continue

            if hasattr(models, 'NewId') and isinstance(rec.id, models.NewId) or not rec.id:
                rec.name = 'New'
                continue

            sequence_code = 'SOBP' if rec.document_type == 'bpkb' else 'SOST'
            branch_code = rec.company_id.code or ''
            rec.name = rec.env['ir.sequence'].get_sequence_code(sequence_code, branch_code)

    @api.onchange('company_id')
    def onchange_is_pilot(self):
        self.is_pilot = False
        self.staff_bbn_id = False
        self.soh_id = False
        self.adh_id = False

        if self.company_id:
            pilot_branches = self.env['tw.pilot.project'].sudo().search([
                ('name', '=', 'ATTACHMENT STOCK OPNAME'),
                ('active', '=', True),
                ('company_ids', 'in', self.company_id.id)
            ], limit=1)
            self.is_pilot = bool(pilot_branches)

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            doc_type = vals.get('document_type') or self.env.context.get('default_document_type')

            check = self.suspend_security().search([
                ('company_id', '=', vals['company_id']),
                ('document_type', '=', doc_type),
                ('state', '!=', 'posted')
            ])
            if check:
                raise UserError(f"Perhatian! Masih ada stock opname {doc_type.upper()} yang belum selesai.")

            if 'attachment_ids' in vals:
                model_id = self.env['ir.model'].suspend_security().search([('model', '=', self._name)])
                for data in vals['attachment_ids']:
                    if isinstance(data, (list, tuple)) and len(data) >= 3 and isinstance(data[2], dict):
                        data[2]['form_id'] = model_id.id

        return super(TwVehicleDocumentStockOpname, self).create(vals_list)

    def write(self, vals):
        if 'attachment_ids' in vals:
            model_id = self.env['ir.model'].suspend_security().search([('model', '=', self._name)])
            for data in vals['attachment_ids']:
                if data[2]:
                    data[2]['form_id'] = model_id.id

        return super(TwVehicleDocumentStockOpname, self).write(vals)

    def read(self, fields=None, load='_classic_read'):
        res = super(TwVehicleDocumentStockOpname, self).read(fields=fields, load=load)
        if fields and 'is_pilot' in fields:
            for record in res:
                company_id = record.get('company_id')
                if company_id:
                    pilot_branches = self.env['tw.pilot.project'].sudo().search([
                        ('name', '=', 'ATTACHMENT STOCK OPNAME'),
                        ('active', '=', True),
                        ('company_ids', 'in', company_id)
                    ], limit=1)
                    record['is_pilot'] = bool(pilot_branches)
                else:
                    record['is_pilot'] = False
        return res

    def unlink(self):
        for data in self:
            if data.state != "draft":
                raise UserError("Tidak bisa menghapus data yang berstatus selain draft!")

        return super(TwVehicleDocumentStockOpname, self).unlink()

    # 13: action methods
    def action_generate_stock_document(self):
        if self.generate_date:
            raise UserError(f"Data Stock {self.document_type.upper()} telah terbentuk. Silahkan refresh halaman ini!")

        if not self.company_id:
            raise UserError("Silakan pilih Branch terlebih dahulu sebelum generate stock!")

        if self.document_type == 'bpkb':
            query = """
                SELECT 
                    doc.lot_id as lot_id,
                    lot.customer_stnk_id as customer_bpkb,
                    lokasi_bpkb.name as lokasi_bpkb,
                    lot.vehicle_ownership_receipt_date as tgl_terima_bpkb,
                    doc.document_number as no_bpkb,
                    lot.finco_id as finco_id,
                    age(lot.vehicle_ownership_receipt_date)::text as umur,
                    EXTRACT(day FROM now() - coalesce(lot.vehicle_ownership_receipt_date,now())) as over_due
                FROM tw_stock_document as doc
                JOIN stock_lot as lot ON lot.id = doc.lot_id
                LEFT JOIN tw_vehicle_document_location as lokasi_bpkb ON lokasi_bpkb.id = doc.location_id
                WHERE doc.type = 'bpkb'
                AND doc.state = 'stock'
                AND doc.company_id = %d
                ORDER BY lot.customer_stnk_id ASC
            """ % (self.company_id.id)
        else:
            query = """
                SELECT 
                    doc.lot_id as lot_id,
                    lot.plate_number as nopol,
                    lot.vehicle_registration_receipt_date as tgl_terima_stnk,
                    lot.customer_stnk_id as customer_stnk,  
                    lokasi_stnk.name as lokasi_stnk,
                    age(lot.vehicle_registration_receipt_date)::text as umur
                FROM tw_stock_document as doc
                JOIN stock_lot as lot ON lot.id = doc.lot_id
                LEFT JOIN tw_vehicle_document_location as lokasi_stnk ON lokasi_stnk.id = doc.location_id
                WHERE doc.type = 'stnk'
                AND doc.state = 'stock'
                AND doc.company_id = %d
                ORDER BY lot.customer_stnk_id ASC
            """ % (self.company_id.id)

        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()
        if not ress:
            raise UserError("Data Stock tidak ditemukan!")
        lines = []

        if self.document_type == 'bpkb':
            for res in ress:
                lines.append([0, False, {
                    'lot_id': res.get('lot_id'),
                    'ownership_number': res.get('no_bpkb'),
                    'customer_ownership_id': res.get('customer_bpkb'),
                    'date_receipt': res.get('tgl_terima_bpkb'),
                    'location_ownership': res.get('lokasi_bpkb'),
                    'finco_id': res.get('finco_id'),
                    'age': res.get('umur'),
                    'over_due': int(res.get('over_due'))
                }])
            self.suspend_security().write({
                'generate_date': self._get_default_datetime(),
                'detail_bpkb_ids': lines,
                'state': 'open',
            })
        else:
            for res in ress:
                lines.append([0, False, {
                    'lot_id': res.get('lot_id'),
                    'plate_number': res.get('nopol'),
                    'customer_registration_id': res.get('customer_stnk'),
                    'date_receipt': res.get('tgl_terima_stnk'),
                    'location_registration': res.get('lokasi_stnk'),
                    'age': res.get('umur')
                }])
            self.suspend_security().write({
                'generate_date': self._get_default_datetime(),
                'detail_stnk_ids': lines,
                'state': 'open',
            })

    def action_post(self):
        for rec in self:
            if rec.document_type == 'bpkb':
                line = rec.env['tw.vehicle.document.stock.opname.line'].suspend_security().search([
                    ('opname_id', '=', rec.id),
                    ('validation_check_physical_ownership', '=', False)
                ], limit=1)
                if line:
                    raise UserError('Perhatian! Ceklis Fisik BPKB masih ada yang belum diisi.')
            elif rec.document_type == 'stnk':
                line = rec.env['tw.vehicle.document.stock.opname.line'].suspend_security().search([
                    ('opname_id', '=', rec.id),
                    ('validation_check_physical_registration', '=', False)
                ], limit=1)
                if line:
                    raise UserError('Perhatian! Ceklis Fisik STNK masih ada yang belum diisi.')
            else:
                raise UserError('Tipe dokumen tidak dikenali.')

            rec.suspend_security().write({
                'post_uid': rec._uid,
                'post_date': rec._get_default_datetime(),
                'state': 'posted'
            })

    def action_print_validasi(self):
        active_ids = self.env.context.get('active_ids', [])
        user = self.env['res.users'].suspend_security().browse(self._uid).name

        detail_ids = []
        other_ids = []
        is_bpkb = self.document_type == 'bpkb'

        if is_bpkb:
            for other in self.other_bpkb_ids:
                other_ids.append({
                    'name_ownership': other.name_ownership,
                    'no_engine': other.no_engine,
                    'keterangan': other.description,
                })

            for line in self.detail_bpkb_ids:
                detail_ids.append({
                    'branch_code': self.company_id.code,
                    'name_ownership': line.customer_ownership_id.name,
                    'validasi_nama_bpkb': line.validation_name_ownership,
                    'tgl_penerimaan': line.date_receipt,
                    'lokasi_bpkb': line.location_ownership,
                    'no_engine': line.lot_id.name,
                    'validasi_no_engine': line.validation_no_engine_ownership,
                    'no_bpkb': line.ownership_number,
                    'finco': line.finco_id.name,
                    'validasi_no_bpkb': line.validation_no_ownership,
                    'validasi_ceklis_fisik_bpkb': line.validation_check_physical_ownership,
                    'keterangan': line.description,
                    'umur': line.age,
                    'over_due': line.over_due
                })

            report_ref = 'tw_vehicle_document_stock_opname.action_report_validasi_bpkb'

        else:
            for other in self.other_stnk_ids:
                other_ids.append({
                    'name_registration': other.name_registration,
                    'no_engine': other.no_engine,
                    'keterangan': other.description
                })

            for line in self.detail_stnk_ids:
                detail_ids.append({
                    'branch_code': self.company_id.code,
                    'name_registration': line.customer_registration_id.name,
                    'validasi_nama_stnk': line.validation_name_registration,
                    'tgl_penerimaan': line.date_receipt,
                    'lokasi_stnk': line.location_registration,
                    'no_engine': line.lot_id.name,
                    'validasi_no_engine': line.validation_no_engine_registration,
                    'no_polisi': line.plate_number,
                    'validasi_no_polisi': line.validation_plate_number,
                    'validasi_ceklis_fisik_stnk': line.validation_check_physical_registration,
                    'keterangan': line.description,
                    'umur': line.age
                })

            report_ref = 'tw_vehicle_document_stock_opname.action_report_validasi_stnk'

        datas = {
            'ids': active_ids,
            'user': user,
            'date': (datetime.now() + timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S'),
            'name': str(self.name),
            'company_id': str(self.company_id.display_name),
            'division': self.division,
            'tgl_so': self.date,
            'staff_bbn': self.staff_bbn_id.name,
            'soh': self.soh_id.name,
            'adh': self.adh_id.name,
            'detail_ids': detail_ids,
            'other_ids': other_ids,
            'create_uid': self.create_uid.name,
            'create_date': (self.create_date + relativedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S'),
        }

        return self.env.ref(report_ref).report_action(self, data={'ids': self.ids})

    def action_bakso(self):
            self.ensure_one()
            form_id = self.env.ref('tw_vehicle_document_stock_opname.view_tw_so_bakso_stnk_wizard').id
            res_model = 'tw.vehicle.document.bakso.registration'

            if self.document_type == 'bpkb':
                form_id = self.env.ref('tw_vehicle_document_stock_opname.view_tw_so_bakso_bpkb_wizard').id
                res_model = 'tw.vehicle.document.bakso.ownership'

            return {
                'type': 'ir.actions.act_window',
                'name': 'Berita Acara SO',
                'view_mode': 'form',
                'res_model': res_model,
                'views': [(form_id, 'form')],
                'target': 'new',
                'context': {
                    'default_opname_id': self.id,
                    'default_note_bakso': self.note_bakso,
                    'default_type_document': self.document_type,
                }
            }

    # 14: private methods