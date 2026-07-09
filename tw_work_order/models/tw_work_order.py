# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime
import io

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError as Warning, UserError
from odoo.tools import float_compare, float_is_zero
from odoo.fields import Command

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib
import base64
import qrcode
try:
    import phonenumbers
    from phonenumbers import PhoneNumberFormat
except ImportError:
    phonenumbers = None
    PhoneNumberFormat = None

class TwWorkOrder(models.Model):
    _name = "tw.work.order"
    _inherit = "sale.order"
    _description = "TW Work Order"
    _order = "date desc, id desc"

    # 7: defaults methods
    def _get_year(self):
        current_year = datetime.now().year
        start_year = 1970
        years_available = []

        for x in reversed(range(start_year, current_year + 1)):
            elem = ("{}".format(x), "{}".format(x))
            years_available.append(elem)

        return years_available
    
    def _get_default_branch(self):
        if self.env.company.parent_id:
            return self.env.company.id
        else:
            company_ids = self.env.companies.filtered(lambda x: x.parent_id)
            if company_ids:
                return company_ids[0].id
        
        if not self.id:
            return self.env.company.id
            
        raise Warning(_('Please choose another branch / company other than %s on the top right of the screen.'%self.env.company.name))
        
    def _get_default_date(self):
        return datetime.now()

    # 8: fields
    date = fields.Date(string='Date', required=True, default=fields.Date.today())
    is_invisible_action_open = fields.Boolean(help="A Flag to Invisible Button Open", default=True, compute="_compute_is_invisible_action_by_state")
    is_invisible_action_invoice_create = fields.Boolean(help="A Flag to Invisible Button Action Create Invoice", default=True, compute="_compute_is_invisible_action_by_state")
    is_invisible_action_start_stop_wo = fields.Boolean(help="A Flag to Invisible Button Start Stop WO", default=True, compute="_compute_is_invisible_action_by_state")
    is_other_module_installed = fields.Boolean(string='Is Other Module Installed', compute='_compute_is_other_module_installed')
    is_supply = fields.Boolean(string='Is Supply', compute='_compute_is_supply')
    
    plate_number = fields.Char(string='No Polisi')
    km = fields.Integer(string='Km')
    note = fields.Text(string='Keluhan')
    type_motorcycle = fields.Char(string='Type Motorcycle')    
    order_id = fields.Char(string='Order ID')
    is_shipped = fields.Boolean(string='Received', help="It indicates that a picking has been done", compute='_compute_is_shipped')
    purchase_date = fields.Date(string='Tanggal Pembelian',  default=_get_default_date, help="Tanggal pembelian unit")
    chassis_number = fields.Char(string='Chassis Number', related='lot_id.chassis_number', readonly=True)
    days = fields.Integer(string='Hari',compute='_compute_days')
    is_type_wo = fields.Boolean(string='Type WO', readonly=True, copy=False,default=False)
    is_invoiced = fields.Boolean(string='Invoice Received', compute='_compute_is_invoiced', store=True)
    is_cancelled = fields.Boolean(string='Cancelled?')
    reason_unused = fields.Char(string='Reason Unused')
    production_year = fields.Selection(_get_year,'Tahun Produksi', help='Tahun Produksi Kendaraan')
    notification = fields.Char(string='Notifikasi')
    qr_code_base64 = fields.Text(string="QR Code (Base64)")
    mechanic_advice = fields.Char(string='Saran Mekanik')
    type = fields.Char(string='Tipe', related='type_id.value', readonly=True)
    mobile = fields.Char(string='Mobile')
    qr_code = fields.Char(string='QR Code')
    lot_state = fields.Selection(related='lot_id.state', string="Status Engine Number")
    reason_to_ahass_value = fields.Char(string='Value Alasan Ke Ahass', related='reason_to_ahass_id.value', readonly=True)
    
    # Selection
    state = fields.Selection(selection_add=[
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('sale', 'Open'),
        ('except_picking', 'Shipping Exception'),
        ('except_invoice', 'Invoice Exception'),
        ('done', 'Done'),
        ('unused', 'Unused'),
        ('cancel', 'Cancelled')
    ], string='State', readonly=True, copy=False, default='draft')
    
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options('Sparepart'),string='Division',default='Sparepart',required=True,readonly=True)
    fuel = fields.Selection([
        ('0', '0'),
        ('25', '25'),
        ('50', '50'),
        ('75', '75'),
        ('100', '100')
    ], string='Bensin')
    #Field ini tidak dipakai dimana-mana, di TEDS 1.0 juga sama
    invoice_method = fields.Selection([
        ('manual', 'Based on Purchase Order lines'),
        ('order', 'Based on generated draft invoice'),
        ('picking', 'Based on incoming shipments')
    ], string='Invoicing Control', required=True, readonly=True, default='manual')
    is_all_location = fields.Boolean(string='All Locations?')
    is_washing_the_motorbike = fields.Selection([
        ('ya', 'Ya'),
        ('tidak', 'Tidak'),
    ], default="tidak", string='Cuci Motor')
    payment_type = fields.Selection([
        ('cash', 'Cash'),
        ('credit', 'Credit')]
    , string='Tipe Pembayaran', default='cash')
    oil_type = fields.Selection([('MPX', 'MPX'), ('SPX', 'SPX')], string='Jenis Oli')
    customer_type = fields.Selection([
        ('AHASS','AHASS'),
        ('Perorangan','Perorangan'),
        ('Non AHASS','Non AHASS')
    ],string="Type Customer")

    # 9: relation fields
    type_id = fields.Many2one('tw.selection', string='Type', ondelete='set default',required=True, domain=[('type','=','WorkOrderType')])
    company_id = fields.Many2one('res.company', "Branch", required=True, index=True, default=_get_default_branch, domain="[('parent_id', '!=', False)]")
    customer_stnk_id = fields.Many2one('res.partner', string='Pemilik (STNK)', required=True, check_company=False)
    is_same_customer = fields.Boolean(string="Sama dengan Pemilik (STNK)")
    partner_id = fields.Many2one('res.partner', string='Customer', check_company=False)
    mechanic_id = fields.Many2one('hr.employee', string='Mechanic', domain="[('company_id','=',company_id),('job_id.sales_force_id.value','=','mechanic')]")
    product_id = fields.Many2one('product.product', string='Product',domain=[('division','=','Unit')])
    picking_ids = fields.One2many('stock.picking', string='Picking List')
    work_order_history_ids = fields.One2many('tw.work.order', string='History Service', compute='_compute_get_history_service')
    history_story_html = fields.Html(compute='_compute_history_story_html', string='Highlight History')
    location_id = fields.Many2one('stock.location', string='Location')
    lot_id = fields.Many2one('stock.lot', string='Engine No')
    reason_to_ahass_id = fields.Many2one('tw.selection', string='Alasan Ke Ahass', domain=[('type', '=', 'AlasanKeAHASS'), ('active', '=', True)])
    customer_payment_id = fields.Many2one(comodel_name='tw.account.payment', string='Customer Payment (AR)')
    journal_entry_count = fields.Integer(compute='_compute_journal_entry_count', string='Journal Entry Count')

    transaction_ids = fields.Many2many(comodel_name='payment.transaction',relation='tw_work_order_tw_transaction_rel', column1='order_id', column2='transaction_id',string="Transactions")
    order_line = fields.One2many(comodel_name='tw.work.order.line',inverse_name='order_id',string="Order Lines")
    tag_ids = fields.Many2many(comodel_name='crm.tag',relation='tw_work_order_tw_tag_rel', column1='order_id', column2='tag_id',string="Tags")

    # Audit Trail
    confirm_uid = fields.Many2one('res.users', string='Confirmed by')
    confirm_date = fields.Datetime(string='Confirmed on')
    open_uid = fields.Many2one('res.users', string='Open by')
    open_date = fields.Datetime(string='Open on')
    done_uid = fields.Many2one('res.users', string='Done by')
    done_date = fields.Datetime(string='Done on')
    cancelled_date = fields.Datetime(string='Cancelled on')
    cancelled_uid = fields.Many2one('res.users', string='Cancelled by')

    # 10: constraints & sql constraints
    @api.constrains('name')
    def _check_unique_name(self):
        for rec in self:
            if self.search([('name', '=', rec.name), ('id', '!=', rec.id)]):
                raise UserError("Nama WO harus unik!")

    # 11: compute/depends & on change methods   
    @api.depends('state')
    def _compute_is_other_module_installed(self):
        for rec in self:
            rec.is_other_module_installed = False
    
    @api.depends(
        'order_line.product_uom_qty',
        'order_line.division',
        'order_line.product_id',
        'picking_ids.move_ids.product_uom_qty',
        'picking_ids.move_ids.state',
    )
    def _compute_is_supply(self):
        for rec in self:
            sparepart_lines = rec.order_line.filtered(lambda l: l.division == 'Sparepart')
            # Jika tidak ada line Sparepart, tidak perlu supply
            if not sparepart_lines:
                rec.is_supply = True
                continue

            sparepart_moves = rec.picking_ids.move_ids.filtered(
                lambda m: m.division == 'Sparepart' and m.state not in ['cancel', 'draft']
            )
            # Jika ada move yang partially_available, berarti supply belum selesai
            if any(m.state == 'partially_available' for m in sparepart_moves):
                rec.is_supply = False
                continue

            # Bandingkan total QTY di Line WO vs total QTY demand di Picking
            total_qty = sum(sparepart_lines.mapped('product_uom_qty'))
            total_moves_qty = sum(sparepart_moves.mapped('product_uom_qty'))
            # Jika QTY sama, maka sudah fully supplied
            rec.is_supply = total_qty == total_moves_qty and total_moves_qty > 0

    @api.depends('order_line.qty_delivered','order_line.product_uom_qty','order_line.division')
    def _compute_is_shipped(self):
        for work_order in self:
            sparepart_lines = work_order.order_line.filtered(lambda l: l.division == 'Sparepart')
            if sparepart_lines:
                work_order.is_shipped = all(line.product_uom_qty - line.qty_delivered == 0 for line in sparepart_lines)
            else:
                # If else, Service Only
                work_order.is_shipped = True
    
    @api.depends('lot_id', 'date')
    def _compute_get_history_service(self):
        for record in self:
            history_ids = self.search([
                ('company_id', '=', record.company_id.id),
                ('lot_id', '=', record.lot_id.id),
                ('id', '!=', record._origin.id if record._origin else False),
                ('date', '<=', record.date),
                ('state', '=', 'done')
            ]).ids
            record.work_order_history_ids = [(6, 0, history_ids)]

    @api.depends('lot_id', 'work_order_history_ids', 'type_id')
    def _compute_history_story_html(self):
        for record in self:
            try:
                if not record.lot_id:
                    record.history_story_html = False
                    continue

                # Ambil history yang bukan draft/cancel dan sort dari yang terbaru
                valid_history = record.work_order_history_ids.filtered(lambda w: w.state not in ['draft', 'cancel'] and w.id != (record._origin.id if record._origin else False)).sorted(key=lambda w: w.date or fields.Date.context_today(record), reverse=True)

                last_wo = valid_history[:1]
                if not last_wo:
                    record.history_story_html = "<div style='font-size: 14px;'><p class='mb-0'><i class='fa fa-hand-paper-o text-primary'></i> <b>Halo!</b> Sepertinya ini belum ada record service yang selesai untuk unit ini di jaringan bengkel kami. Mari berikan pelayanan dan pengecekan menyeluruh agar performa motor tetap prima!</p></div>"
                else:
                    last_date = last_wo.date.strftime('%d %b %Y') if last_wo.date else ''
                    branch_name = last_wo.company_id.name or 'Bengkel Kami'
                    km_last = f"{last_wo.km:,}".replace(',', '.') if last_wo.km else '0'
                    mechanic_advice = last_wo.mechanic_advice or 'Tidak ada saran'
                    keluhan = last_wo.note or 'Tidak ada keluhan khusus'
                    
                    days_ago = 0
                    if last_wo.date:
                        days_ago = (fields.Date.context_today(record) - last_wo.date).days
                    time_ago = f"{days_ago} hari" if days_ago < 30 else f"{days_ago // 30} bulan"
                    
                    cust_name = record.partner_id.name or 'Bpk/Ibu'

                    if record.type_id and record.type_id.value == 'KPB':
                        kpb_info = f" KPB {record.kpb_ke}" if hasattr(record, 'kpb_ke') and record.kpb_ke else " KPB"
                        story = f"<i class='fa fa-star text-warning'></i> <b>Halo {cust_name}, ini waktunya{kpb_info} ya!</b><br/>" \
                                f"Servis terakhir dilakukan <b>{time_ago} yang lalu ({last_date})</b> di KM <b>{km_last}</b>. " \
                                f"Saat itu keluhan tercatat adalah: <i>'{keluhan}'</i>, dan saran dari mekanik sebelumnya: <i>'{mechanic_advice}'</i>. " \
                                f"Mari pastikan performanya tetap terjaga di KPB kali ini!"
                    else:
                        story = f"<i class='fa fa-wrench text-info'></i> <b>Halo {cust_name}!</b> Unit ini terakhir servis sekitar <b>{time_ago} lalu ({last_date})</b> di cabang <b>{branch_name}</b>.<br/>" \
                                f"Saat itu kilometer di angka <b>{km_last}</b> dengan keluhan: <i>'{keluhan}'</i>. " \
                                f"Saran mekanik waktu itu: <i>'{mechanic_advice}'</i>.<br/>" \
                                f"Untuk menjaga kenyamanan dan keselamatan, mari pastikan servis berkalanya hari ini tercover semua!"

                    record.history_story_html = f"<div style='font-size: 14px;'><p class='mb-0'>{story}</p></div>"
            except Exception as e:
                record.history_story_html = f"<div style='font-size: 14px;' class='text-danger'><p class='mb-0'><i class='fa fa-warning'></i> Terjadi error saat menarik cerita: {str(e)}</p></div>"

    def _compute_days(self):
        for wo in self:
            if wo.purchase_date and wo.date:
                date_format = "%Y-%m-%d"
                a = datetime.strptime(str(wo.date), date_format)
                b = datetime.strptime(str(wo.purchase_date), date_format)
                timedelta = a - b
                wo.days = timedelta.days
            else:
                wo.days = 0

    def _compute_is_invoiced(self):
        res = {}
        for work_order in self:
            res[work_order.id] = all(line.is_invoiced for line in work_order.order_line)
        return res

    def _compute_journal_entry_count(self):
        for rec in self:
            rec.journal_entry_count = self.env['account.move'].search_count([
                ('move_type', '=', 'entry'),
                '|', '|',
                ('invoice_origin', '=', rec.name),
                ('ref', '=', rec.name),
                ('ref', 'in', rec.picking_ids.mapped('name') if rec.picking_ids else ['_xxx_']),
            ])


    @api.depends('state', 'order_line.invoice_status')
    def _compute_invoice_status(self):
        """
        Compute the invoice status of a WO. Possible statuses:
        - no: if the WO is not in status 'sale' or 'done', we consider that there is nothing to
          invoice. This is also the default value if the conditions of no other status is met.
        - to invoice: if any WO line is 'to invoice', the whole WO is 'to invoice'
        - invoiced: if all WO lines are invoiced, the WO is invoiced.
        - upselling: if all WO lines are invoiced or upselling, the status is upselling.
        """
        confirmed_orders = self.filtered(lambda wo: wo.state == 'sale')
        (self - confirmed_orders).invoice_status = 'no'
        if not confirmed_orders:
            return
        lines_domain = [('is_downpayment', '=', False), ('display_type', '=', False)]
        line_invoice_status_all = [
            (order.id, invoice_status)
            for order, invoice_status in self.env['tw.work.order.line']._read_group(
                lines_domain + [('order_id', 'in', confirmed_orders.ids)],
                ['order_id', 'invoice_status']
            )
        ]
        for order in confirmed_orders:
            line_invoice_status = [d[1] for d in line_invoice_status_all if d[0] == order.id]
            if order.state != 'sale':
                order.invoice_status = 'no'
            elif any(invoice_status == 'to invoice' for invoice_status in line_invoice_status):
                if any(invoice_status == 'no' for invoice_status in line_invoice_status):
                    # If only discount/delivery/promotion lines can be invoiced, the SO should not
                    # be invoiceable.
                    invoiceable_domain = lines_domain + [('invoice_status', '=', 'to invoice')]
                    invoiceable_lines = order.order_line.filtered_domain(invoiceable_domain)
                    special_lines = invoiceable_lines.filtered(
                        lambda sol: not sol._can_be_invoiced_alone()
                    )
                    if invoiceable_lines == special_lines:
                        order.invoice_status = 'no'
                    else:
                        order.invoice_status = 'to invoice'
                else:
                    order.invoice_status = 'to invoice'
            elif line_invoice_status and all(invoice_status == 'invoiced' for invoice_status in line_invoice_status):
                order.invoice_status = 'invoiced'
            elif line_invoice_status and all(invoice_status in ('invoiced', 'upselling') for invoice_status in line_invoice_status):
                order.invoice_status = 'upselling'
            else:
                order.invoice_status = 'no'
    
    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty', 'state')
    def _compute_qty_to_invoice(self):
        """
        Compute the quantity to invoice. If the invoice policy is order, the quantity to invoice is
        calculated from the ordered quantity. Otherwise, the quantity delivered is used.
        """
        for line in self:                        
            if line.state == 'sale' and not line.display_type:
                if line.product_id.invoice_policy == 'order':
                    line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
                else:
                    line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

    @api.depends('state')
    def _compute_type_name(self):
        for record in self:
            if record.state in ('draft', 'sent', 'cancel'):
                record.type_name = _("Quotation")
            else:
                record.type_name = _("Work Order")

    # Work Order Approval, Clocking
    @api.depends('state')
    def _compute_is_invisible_action_by_state(self):
        state = 'finished'
        for rec in self:
            rec.is_invisible_action_invoice_create = rec.is_type_wo == False
            rec.is_invisible_action_start_stop_wo = True
            rec.is_invisible_action_open = rec.state != 'draft'

    # Work Order CRM
    @api.onchange('is_same_customer', 'customer_stnk_id')
    def _onchange_is_same_customer(self):
        for rec in self:
            rec.partner_id = False
            rec.mobile = False
            rec.relationship_with_the_owner_id = False
            if rec.is_same_customer and rec.customer_stnk_id:
                rec.partner_id = rec.customer_stnk_id.id
                rec.mobile = rec.customer_stnk_id.mobile
                if 'relationship_with_the_owner_id' in rec._fields:
                    sendiri_id = self.env['tw.selection'].search([('type', '=', 'HubunganDenganPemilik'), ('name', '=', 'Sendiri')], limit=1).id
                    if sendiri_id:
                        rec.relationship_with_the_owner_id = sendiri_id


    @api.onchange('chassis_number')
    def _onchange_chassis_number(self):
        if self.chassis_number:
            self.chassis_number = self.chassis_number.replace(' ', '').upper()

    @api.onchange('plate_number')
    def _onchange_plate_number(self):
        if self.plate_number:
            self.plate_number = self.plate_number.replace(' ', '').upper()

    @api.onchange('previous_work_order_id')
    def _onchange_previous_work_order_id(self):
        if self.previous_work_order_id:
            self.lot_id = self.previous_work_order_id.lot_id.id
        else:
            self.lot_id = False

    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.lot_id = False
        self.product_id = False
        self.customer_stnk_id = False
        self.plate_number = False
        self.warranty = False
        self.chassis_number = False
        self.production_year = False
        self.purchase_date = False
        self.reason_to_ahass_id = False
        self.reason_to_ahass_value = False
        self.fuel = False
        self.km = False
        self.is_same_customer = False
        self.partner_id = False
        self.order_line = [(Command.clear())]

    @api.onchange('mobile')
    def _onchange_mobile(self):
        mobile_config_parameter = self.env['ir.config_parameter'].sudo().get_param(
            'mobile_length')
        if self.mobile:
            normalize_mobile = self._normalize_with_lib(self.mobile)
            if not normalize_mobile.isdigit():
                raise UserError(_("Nomor Handphone harus berupa angka!"))
            # Check length
            if len(normalize_mobile) < int(mobile_config_parameter):
                raise UserError(_("Nomor Handphone minimal " + mobile_config_parameter + " digit!"))

    @api.onchange('qr_code')
    def _onchange_qr_code(self):
        if self.qr_code:
            lot_obj = self.env['stock.lot'].sudo().search([('qr_code', '=', self.qr_code)], limit=1)
            if lot_obj:
                self.lot_id = lot_obj.id

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        self.customer_stnk_id = False
        self.product_id = False
        self.purchase_date = False
        self.plate_number = False
        self.chassis_number = False
        self.production_year = False
        self.purchase_date = False
        self.km = False
        self.is_same_customer = False
        if self.lot_id:
            self.product_id = self.lot_id.product_id.id
            self.customer_stnk_id = self.lot_id.partner_id.id if self.lot_id.partner_id else False
            self.plate_number = self.lot_id.plate_number
            self.chassis_number = self.lot_id.chassis_number
            self.production_year = self.lot_id.production_year
            self.purchase_date = self.lot_id.invoice_date
    
    @api.onchange('production_year', 'date')
    def _onchange_production_year(self):
        if self.production_year:
            if self.production_year.isdigit():
                current_year = int(str(self.date)[:4]) if self.date else datetime.now().year
                if int(self.production_year) <= 1969 or int(self.production_year) >= current_year + 1:
                    raise UserError(_(f"Tahun perakitan minimal 1970 dan maksimal tahun {current_year}"))
            else:
                raise UserError(_("Tahun perakitan harus berupa angka"))

    @api.onchange('is_all_location', 'company_id', 'division')
    def _onchange_internal_location(self):
        domain = {}
        if self.is_all_location:
            domain['location'] = [('usage', '=', 'internal'), ('company_id', '=', self.company_id.id)]
        else:
            domain['location'] = [('usage', '=', 'internal'), ('company_id', '=', self.company_id.id), ('division', '=', self.division)]
        return {'domain': domain}

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.mobile = False
        self.gender_id = False
        self.job_id = False
        if self.partner_id:
            self.mobile = self.partner_id.mobile
            self.gender_id = self.partner_id.gender_id.id
            self.job_id = self.partner_id.occupation_id.id

    
    @api.onchange('type_id')
    def _onchange_type_id(self):
        if self.type_id:
            self.payment_term_id = self._prepare_payment_term()


    @api.onchange('location_id')
    def _onchange_location_id(self):
        if self.location_id:
            for line in self.order_line:
                line.qty_available = 0
                
    def _generate_qr_code(self):
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
        qr.add_data('kodesa'+self.name)
        qr.make()
        img = qr.make_image(fill='black', back_color='white')

        # Save QR image as base64
        qr_buffer = io.BytesIO()
        img.save(qr_buffer, 'PNG')
        qr_buffer.seek(0)
        self.write({
            'qr_code_base64': base64.b64encode(qr_buffer.read()).decode()
        })


    # 12: override methods
    def copy(self):
        raise Warning('Tidak bisa duplikat data.')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._check_km(vals)
            self._check_purchase_date(vals)
            if vals.get('company_id'):
                branch_src = self.env['res.company'].suspend_security().search([('id','=',vals['company_id'])],limit=1)
                seq_name = self.env['ir.sequence'].with_company(branch_src).get_sequence_code('WO', branch_src.code)
                vals['name'] = seq_name

            self._prepare_vals_before_create(vals)            

            # Set the payment term
            self._override_payment_term_id(vals)

        # CREATE SEKALI SAJA
        work_orders = super(TwWorkOrder, self).create(vals_list)

        # POST CREATE PROCESS
        for work_order, vals in zip(work_orders, vals_list):
            if vals.get('lot_id'):
                obj_lot = self.env['stock.lot'].browse(vals['lot_id'])
                if obj_lot.state != 'stock':
                    obj_lot.sudo().write({
                        'plate_number': vals.get('plate_number'),
                        'chassis_number': vals.get('chassis_number'),
                        'product_id': vals.get('product_id'),
                        'partner_id': vals.get('customer_stnk_id'),
                    })

            work_order._update_partner(vals)

        return work_orders
    
    def write(self, vals):     
        self._check_km(vals)
        self._check_purchase_date(vals)  

        if 'company_id' in vals:
            for rec in self:
                if rec.name and rec.company_id.id != vals['company_id']:
                    raise UserError(_("Anda tidak bisa mengganti Cabang jika Nama Work Order sudah terbentuk!"))

        if 'pricelist_id' in vals and any(so.state == 'sale' for so in self):
            raise UserError(_("You cannot change the pricelist of a confirmed part sales !"))
        
        if vals.get('partner_id'):
            self.filtered(lambda so: so.state in ('sent', 'sale')).message_subscribe(
                partner_ids=[vals['partner_id']],
            )
        self._get_combined_tax(vals)
        self._override_payment_term_id(vals)        

        if vals.get('date') and self.date:
            vals.pop('date')
        
        res = super(TwWorkOrder, self).write(vals)

        work_orders_to_update = self._update_state_wo()

        # Update work orders sekali saja
        for wo, update_vals in work_orders_to_update:
            
            super(TwWorkOrder, wo).write(update_vals)

        return res

    def unlink(self):
        for record in self:
            if record.state and record.state != 'draft':
                raise Warning('Warning! \nCannot delete records with a State other than draft!')
            else:
                raise Warning('Warning! \nCannot delete records! Use unused button')
        return super(TwWorkOrder, self).unlink()

    # 13: action methods

    def action_print_wo_thermal(self,user=False):
        if not self.qr_code_base64:
            self._generate_qr_code()
            
        return self.env.ref('tw_work_order.action_print_wo_thermal').report_action(self)

    def action_print_picking_wo_thermal(self,user=False):
        if not self.qr_code_base64:
            self._generate_qr_code()
            
        return self.env.ref('tw_work_order.action_print_picking_wo_thermal').report_action(self)
    
    def _print_invoice(self, xml_id, thermal=False):
        if thermal:
            doc_name = "Print Thermal Invoice"
            if not self.qr_code_base64:
                self._generate_qr_code()
        else:
            doc_name = "Print Invoice WO"
            
        self.ensure_one()
        if self.invoice_ids and self.invoice_count > 0:
            try:
                report = self.env.ref(xml_id).report_action(self)
            except Exception as err:
                raise UserError(_(f'Gagal {doc_name} : {self.name} karena {err}!'))
            
            # * auto create Customer Payment (AR)
            self.action_auto_create_customer_payment()
            
            return report
        else:
            raise UserError(_(f'Gagal {doc_name} : {self.name} karena WO belum create invoice!'))
        
    def action_print_wo_thermal_invoice(self):
        self.ensure_one()
        return self._print_invoice('tw_work_order.action_print_wo_thermal_invoice', thermal=True)
    
    def action_print_wo_invoice(self):
        self.ensure_one()
        return self._print_invoice('tw_work_order.action_print_wo_invoice')

    def action_print_wo(self):
        self.ensure_one()
        return self.env.ref('tw_work_order.action_print_wo').report_action(self)
    
    def action_view_journal_entries(self):
        self.ensure_one()
        moves = self.env['account.move'].search([
            ('move_type', '=', 'entry'),
            '|', '|',
            ('invoice_origin', '=', self.name),
            ('ref', '=', self.name),
            ('ref', 'in', self.picking_ids.mapped('name') if self.picking_ids else ['_xxx_']),
        ])
        return {
            'name': _('Journal Entries'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': [('id', 'in', moves.ids)],
            'context': dict(self.env.context, create=False, default_move_type='entry', default_ref=self.name),
        }

    def action_forced_unused(self):
        action_forced_unused = self.env.user.has_group('tw_work_order.group_button_forced_unused_wo')
        if not action_forced_unused:
            raise UserError(_('Anda tidak termasuk ke dalam group untuk melakukan unused'))
        for obj in self :
            if obj.state in ('unused','done','cancel'):
                raise UserError(_('Gagal Unused WO : %s Karena Berstatus %s!' % (obj.name,obj.state)))
        
        query = """
            UPDATE tw_work_order 
            SET state ='unused'
            WHERE id in %s
            """ % str(tuple(self.ids)).replace(',)', ')')
        self._cr.execute (query)

        for line in obj.order_line:
            if line.state == 'draft':
                line.write({'state': 'confirmed'})

        ids_picking = obj._get_ids_picking()
        picking_ids = obj.env['stock.picking'].browse(ids_picking)
        if picking_ids:
            for picking in picking_ids:
                picking.action_cancel()

    def action_tidak_digunakan(self):
        self.ensure_one()
        view = self.env.ref('tw_work_order.tw_work_order_unused_wizard_form_view')
        return {
            'name': ('Reason'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'tw.work.order',
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
        }

    def action_button_confirm_reason_unused(self):
        for line in self.order_line:
            if line.state != 'draft':
                raise Warning('Gagal unused, Jasa/Sparepart telah di supply')
            else:
                line.write({'state': 'confirmed'})
        self.write({
            'state': 'unused',
            'reason_unused': self.reason_unused
            })
        
        for picking in self._get_ids_picking():
            picking.action_cancel()
        return True

    def action_confirm(self):
        pass

    # NRFS Work Order
    def action_confirm_order(self):
        pass

    # Work Order Cancel
    def _action_cancel(self):
        work_order_cancel = super(TwWorkOrder,self)._action_cancel()
        self.write({
            'cancelled_uid': self.env.uid,
            'cancelled_date': datetime.now()
        })
        return work_order_cancel

    # Work Order Clocking
    def action_start_stop_wo(self):
        pass
    def action_unused(self):
        self.write({ 'state':'unused' })

    def action_create_invoice(self):
        self._validate_order()
        if any(line.division=='Sparepart' and (line.qty_delivered == 0 or not line.order_id.picking_ids) for line in self.order_line):
            raise UserError("Sparepart belum dilakukan picking. Silahkan selesaikan picking terlebih dahulu.")
        if not self.is_shipped:
            raise UserError("Picking belum selesai. Silahkan selesaikan picking terlebih dahulu sebelum menyelesaikan work order.")
        invoice = self.with_context(skip_date_sequence_check=True)._create_invoices()
        invoice.sudo().action_post()
        self.action_open()

    def action_supply(self):
        self._validate_order()
        current_state = self.state
        
        # Make sure that action_confirm() is triggered only once.
        if not self.confirm_date:
            self.action_confirm()
            self.action_confirm_order()
        for line in self.order_line:
            # Check if there is an additional sparepart
            if line.division == 'Sparepart' and line.qty_delivered < line.product_uom_qty:
                line.state = 'sale'
                line._action_launch_stock_rule()

        """
        After action_confirm() is triggered, header state will be 'sale'.
        Therefore we have to replace again the state.
        """
        self.write({
            'state':current_state,
        })

    def action_open(self):
        self._validate_order()
        self.write({
            'state': 'sale',
            'open_uid': self.env.uid,
            'open_date': datetime.now(),
        })

    def action_done(self):
        for line in self.order_line:
            for inv in line.invoice_lines:
                if inv.move_id.state != 'posted':
                    raise UserError(_('You cannot set a Work Order to Done if the invoice is not posted.'))
        self.write({
            'state':'done',
            'done_uid': self.env.uid,
            'done_date': datetime.now()
        })

    def action_auto_create_customer_payment(self):
        result_validation, datas = self._check_validation_auto_create_ar()
        if not result_validation:
            values = self._prepare_values_auto_create_ar(datas)
            try:
                ar_obj = self.env['tw.account.payment'].suspend_security().with_company(self.company_id).create(values)
                self.suspend_security().write({'customer_payment_id': ar_obj.id})
                return ar_obj
            except Exception as err:
                raise UserError(_(f'Gagal create Auto Customer Payment (AR) setelah Print Invoice WO : {self.name} karena {err}!'))
            
        return False
    
    def action_view_customer_payment(self):
        self.ensure_one()
        if not self.customer_payment_id:
            raise Warning(_('No customer payment (AR) transaction found.'))
        
        form_id = self.env.ref('tw_payment.tw_account_payment_form_view').id

        return {
            'name': _('Customers Payment'),
            'view_mode': 'form',
            'views': [(form_id, 'form')],
            'res_model': 'tw.account.payment',
            'res_id': self.customer_payment_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current'
        }

    # 14: private methods
    def _prepare_confirmation(self):
        self.write({
            'date_order': datetime.now(),
            'confirm_uid': self.env.uid,
            'confirm_date': datetime.now()
        })

        total_qty = 0
        qty = {}
        
        if self.state == 'approved' :
            for sol in self.order_line :
                qty[sol.product_id] = qty.get(sol.product_id,0) + sol.product_uom_qty

        for sol in self.order_line:
            if sol.division == 'Sparepart':
                self.env['stock.quant'].compare_stock_on_transaction( self.company_id.id, self.division, sol.product_id.id, sol.product_uom_qty, sol.location_id.id )
                total_qty += sol.product_uom_qty

        self.state = 'sent'

    def _normalize_with_lib(self, s: str, default_region='ID') -> str:
        try:
            num = phonenumbers.parse(s, default_region)
            if not phonenumbers.is_valid_number(num):
                raise UserError("Nomor tidak valid. Contoh Nomor yang Valid (+62 812-3456-7890 / 081234567890)")
            return phonenumbers.format_number(num, PhoneNumberFormat.E164).lstrip('+')
        except phonenumbers.NumberParseException:
            raise UserError("Gagal parse nomor")

    def _get_ids_picking(self):
        picking_obj = self.env['stock.picking']
        ids_picking = picking_obj.search([
            ('origin','=', self.name),
            ('state', '!=', 'cancel')
        ])
        return ids_picking

    def _prepare_payment_term(self):
        if self.partner_id:
            return self.partner_id.property_payment_term_id.id

    def _check_km(self,vals):
        if vals.get('km') or vals.get('km') == 0:
            if vals.get('km') <= 0:
                raise UserError("KM tidak boleh 0 atau negatif!")

    def _get_partner_id(self, type, partner_id, company_id):
        return partner_id

    def _get_location_wo(self, company_id):
        picking_type = self.env['stock.picking.type'].search([
            ('company_id', '=', company_id),
            ('code', '=', 'outgoing')
        ], limit=1)
        
        if not picking_type or not picking_type.default_location_dest_id:
            raise UserError(_('Location destination Belum di Setting'))
        
        return {
            'picking_type_id': picking_type.id,
            'source': picking_type.default_location_src_id.id,
            'destination': picking_type.default_location_dest_id.id,
        }

    def _test_moves_done(self):
        if not self.picking_ids :
            return False
        for picking in self.picking_ids:
            if picking.state != 'done':
                return False
        return True
    
    def _check_purchase_date(self, vals):
        if vals.get('purchase_date'):
            purchase_date = fields.Date.from_string(vals['purchase_date'])
            if purchase_date > fields.Date.today():
                raise UserError(_("Tanggal Pembelian tidak boleh lebih dari hari ini!"))

      # Work Order Account, Claim, KPB
    def _check_payment_term_id_fields(self):
        if 'payment_term_id' in self._fields:
            return True

    # Work Order Clocking
    def _update_state_wo(self):
        return []

    # Work Order CRM
    def _update_partner(self, vals):
        pass

    # Work Order Claim, KPB
    def _override_combined_tax(self,vals):
        return vals
    
    # Work Order Account
    def _override_payment_term_id(self,vals):
        return True

    # Work Order Account
    def _get_branch_or_wo_obj(self,vals):
        if vals.get('company_id'):
            branch = self.env['res.company'].search([('id', '=', vals['company_id'])], limit=1)
            return branch
        else:
            return self

    def _prepare_invoice(self):
        journal_id = self._prepare_journal_account()
        if not journal_id:
            raise UserError(f"Journal for Work Order {self.type_id.name} not found.\nPlease check configuration for branch {self.company_id.name}")

        self.suspend_security().write({
            'journal_id': journal_id.id,
        })
        
        prepare_invoice = super()._prepare_invoice()

        code = journal_id.code
        prefix = self.company_id.code
        
        prepare_invoice.update({
            'name': self.env['ir.sequence'].get_sequence_code(code, prefix),
            'company_id': self.company_id.id,
            'partner_id': self._get_partner_id(self.type_id.value, self.partner_id.id, self.company_id.id),
            'ref': self.name,
            'division': self.division,
            'invoice_date': self.date_order
        })

        return prepare_invoice

    # Work Order Account
    def _prepare_journal_account(self):
        account_setting_obj = self.company_id.branch_setting_id.account_setting_id
        if not account_setting_obj:
            raise UserError("Account Setting for Branch {} is not found")
        return account_setting_obj.wo_reg_journal_id
    

    # Work Order Claim, KPB
    def _prepare_type_onchange_customer_stnk_id(self, wo_type=[]):
        return wo_type

    # Work Order Approval, Clocking
    def _prepare_invisible_action_invoice_create_state(self,state):
        return state

    # Work Order Approval, Clocking
    def _prepare_invisible_action_start_stop_wo(self,state_list):
        return state_list

    # Work Order Claim, CRM, KPB
    def _prepare_vals_before_create(self,vals):
        vals['date'] = datetime.now().strftime('%Y-%m-%d')
        if 'order_line' in vals:            
            for line in vals.get('order_line', []):
                if 'product_uom_qty' in line[2]:
                    line[2]['product_uom_qty'] = round(line[2]['product_uom_qty'], 0)
        return vals
    
    # Work Order Claim, KPB
    def _prepare_type_wo(self,wo_type=[]):
        return wo_type
    
    def _validate_order(self):
        if not self.order_line:
            raise UserError("Detail Transaksi Belum di Isi")
            
        has_service = False
        for line in self.order_line:
            if line.product_id and line.product_id.categ_id:
                # Cek apakah kategori produk atau parent-nya adalah 'Service'
                service_category = self.env['product.category'].search([
                    ('name', '=', 'Service'),
                    ('id', 'parent_of', line.product_id.categ_id.id)
                ], limit=1)
                if service_category:
                    has_service = True
                    break # Sudah ketemu service, tidak perlu cek yang lain
        
        if not has_service:
            raise UserError("Minimal harus ada 1 (satu) produk dengan kategori Service pada Work Order.")
        return True

    # Work Order Job Return, CRM
    def _prepare_previous_work_order(self):
        self.mechanic_advice = self.previous_work_order_id.mechanic_advice
        self.customer_stnk_id = self.previous_work_order_id.customer_stnk_id.id
        self.partner_id = self.previous_work_order_id.partner_id.id
    
    def _show_cancel_wizard(self):
        return False

    def _create_invoices(self, grouped=False, final=False, date=None):                
        moves = super()._create_invoices(grouped=grouped, final=final, date=date)
        # Update Invoice Values, because creating is not use create() method
        for line in moves.line_ids:
            line.company_id = moves.company_id.id
        return moves
    
    def _get_report_base_filename(self):
        self.ensure_one()
        return f'{self.type_name} {self.name}'
    
    def _get_invoiceable_lines(self, final=False):
        """Return the invoiceable lines for order `self`."""
        down_payment_line_ids = []
        invoiceable_line_ids = []
        pending_section = None
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        for line in self.order_line:            
            if line.display_type == 'line_section':
                # Only invoice the section if one of its lines is invoiceable
                pending_section = line
                continue
            if line.display_type != 'line_note' and float_is_zero(line.qty_to_invoice, precision_digits=precision):
                continue
            if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final) or line.display_type == 'line_note':
                if line.is_downpayment:
                    # Keep down payment lines separately, to put them together
                    # at the end of the invoice, in a specific dedicated section.
                    down_payment_line_ids.append(line.id)
                    continue
                if pending_section:
                    invoiceable_line_ids.append(pending_section.id)
                    pending_section = None
                invoiceable_line_ids.append(line.id)   

        return self.env['tw.work.order.line'].browse(invoiceable_line_ids + down_payment_line_ids)
    
    def _check_validation_auto_create_ar(self):
        datas = {}
        wo_invoice_obj = self.env['account.move.line'].sudo().search([
            ('ref','=',self.name),
            ('debit','!=',0),
            ('division','=',self.division),
            ('partner_id','=',self.partner_id.id),
            ('reconciled','=',False),
            ('full_reconcile_id','=',False)
        ], limit=1)
        if not wo_invoice_obj:
            raise UserError(_(f'Account move tidak ditemukan!'))
        
        ar_obj = self.env['tw.account.payment.line'].sudo().search([
            ('move_line_id','=',wo_invoice_obj.id),
            ('company_id','=',self.company_id.id),
            ('partner_id','=',self.partner_id.id)
        ], limit=1)
        if not ar_obj:
            reconciled = wo_invoice_obj._check_reconciled()
            if reconciled:
                raise UserError(_(f'Account move sudah reconciled!'))

            # TODO: journal penerimaan workshop
            payment_method = 'cash'
            journal_obj = self.env['account.journal'].sudo().search([
                '|',
                ('company_id','=',self.company_id.id),
                ('company_id','=',self.company_id.parent_id.id),
                ('type','=',payment_method),
                # ('name','=like','%WS%')
                ('name','=ilike','%kas penerimaan%')
            ], limit=1)
            if not journal_obj:
                raise UserError(_(f'Journal tipe {payment_method} pada {self.company_id.name} tidak ditemukan!'))
            
            method = 'manual payment'
            payment_method_obj = self.env['account.payment.method'].sudo().search([
                ('payment_type','=','inbound'),
                ('name','=ilike','%manual payment%')
            ], limit=1)
            if not payment_method_obj:
                raise UserError(_(f'Payment Method {method.title()} tidak ditemukan!'))
            
            datas.update({
                'wo_invoice_obj': wo_invoice_obj,
                'journal_obj': journal_obj,
                'payment_method_obj': payment_method_obj
            })

            return False, datas
        else:
            return True, datas
        
    def _prepare_values_auto_create_ar(self, datas):
        wo_invoice_obj = datas.get('wo_invoice_obj')
        journal_obj = datas.get('journal_obj')
        payment_method_obj = datas.get('payment_method_obj')

        remaining_amount = self.amount_total
        currency = self.env.user.company_id.currency_id or journal_obj.company_id.currency_id
        
        if wo_invoice_obj.currency_id and currency == wo_invoice_obj.currency_id:
            amount_original = abs(wo_invoice_obj.amount_currency)
            amount_unreconciled = abs(wo_invoice_obj.amount_residual)
        else:
            #always use the amount booked in the company currency as the basis of the conversion into the voucher currency
            amount_original = currency.round(wo_invoice_obj.credit or wo_invoice_obj.debit or 0.0)
            amount_unreconciled = currency.round(abs(wo_invoice_obj.amount_residual))
    
        line_cr_ids = [
            Command.create({
                'move_line_id': wo_invoice_obj.id,
                'account_id': wo_invoice_obj.account_id.id,
                'amount_original': amount_original,
                'amount_unreconciled': amount_unreconciled,
                'is_reconciled': True,
                'amount': wo_invoice_obj and min(abs(remaining_amount), amount_unreconciled) or 0.0
            })
        ]

        values = {
            'company_id': self.company_id.id,
            'partner_id': self.partner_id.id,
            'division': self.division,
            'type': 'customer_payment',
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'memo': f'Auto Customer Payment for WO Reguler [{self.customer_stnk_id.name}]',
            'payment_method_id': payment_method_obj.id,
            'journal_id': journal_obj.id,
            'amount': wo_invoice_obj and min(abs(remaining_amount), amount_unreconciled) or 0.0,
            'line_cr_ids': line_cr_ids
        }

        return values

    # Product Catalog Mixin
    def _get_action_add_from_catalog_extra_context(self):
        context = super()._get_action_add_from_catalog_extra_context()
        if self.warehouse_id:
            context['warehouse_id'] = self.warehouse_id.id
        return context

    def _get_product_catalog_domain(self):
        return super()._get_product_catalog_domain() + [('division', 'in', ['Sparepart', 'Service'])]

    def _default_order_line_values(self, product_id=None, quantity=0, **kwargs):
        vals = {'order_id': self.id, 'company_id': self.company_id.id,}
        if product_id:
            vals['product_id'] = product_id
            product = self.env['product.product'].browse(product_id)
            vals['division'] = product.division or self.division
            if 'warranty' in self.env['tw.work.order.line']._fields:
                vals['warranty'] = getattr(product.categ_id, 'warranty', 0.0)
        else:
            vals['division'] = self.division

        if quantity:
            vals['product_uom_qty'] = quantity
        return vals

    def _get_price_from_catalog(self, product):
        return product.list_price

    def _get_product_catalog_order_line_info(self, product_ids, **kwargs):
        products = self.env['product.product'].browse(product_ids)
        product_lines = {
            line.product_id.id: {'quantity': line.product_uom_qty, 'price': line.price_unit, 'readOnly': False, 'productType': line.product_id.type,}
            for line in self.order_line.filtered(lambda l: l.product_id.id in product_ids)
        }
        for product in products:
            if product.id not in product_lines:
                product_lines[product.id] = {'quantity': 0, 'price': self._get_price_from_catalog(product), 'readOnly': False, 'productType': product.type,}
        return product_lines

    def _update_order_line_info(self, product_id, quantity, **kwargs):
        line = self.order_line.filtered(lambda l: l.product_id.id == product_id)
        if line:
            if quantity != 0:
                line.write({'product_uom_qty': quantity})
                return line.price_unit
            else:
                line.unlink()
        elif quantity > 0:
            vals = self._default_order_line_values(product_id, quantity, **kwargs)

            product = self.env['product.product'].browse(product_id)
            vals['price_unit'] = self._get_price_from_catalog(product)

            if vals.get('division') == 'Sparepart':
                quants = self.env['stock.quant'].sudo().search([('product_id', '=', product_id),('company_id', '=', self.company_id.id),('location_id.usage', '=', 'internal'),('quantity', '>', 0)], order='quantity desc', limit=1)
                if quants:
                    vals['location_id'] = quants[0].location_id.id
                    vals['qty_available'] = self.env['stock.quant'].compare_stock_on_transaction(self.company_id.id,vals.get('division'),product_id,quantity,vals['location_id'])

            line = self.env['tw.work.order.line'].create(vals)
            return line.price_unit
        
        product = self.env['product.product'].browse(product_id)
        return self._get_price_from_catalog(product)
