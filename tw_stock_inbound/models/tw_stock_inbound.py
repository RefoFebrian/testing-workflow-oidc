from odoo import models, fields, api
from odoo.exceptions import UserError as Warning
from datetime import datetime

class StockInbound(models.Model):
    _name = "tw.stock.inbound"
    _description = "Stock Inbound"
    _order = 'write_date desc'
    _rec_names_search = ['name', 'booking_number', 'vehicle_id.plate_number']

    def _get_default_datetime(self):
        return datetime.now()
    
    name = fields.Char(string="Name", index='trigram', compute='_compute_name', store=True)
    booking_number = fields.Char(string="Booking/DO Number")
    amount_of_load = fields.Integer(string="Amount of Load")
    amount_receipt = fields.Integer(string="Amount of Receipt", default=0)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('done', 'Done'),
    ], string="Status",default='draft')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
    rope_condition = fields.Selection([
        ('good', 'Good'),
        ('not_good', 'Not Good'),
        ], string="Kondisi Tali Pengikatan", help="condition of the binding rope")
    amount_of_load_uom = fields.Selection([
        ('unit', 'Unit'),
        ('package', 'Kardus'),
        ], string="Satuan")
    sponge_count = fields.Integer(string="Total Spons", help="count of sponge")
    steel_count = fields.Integer(string="Total Besi", help="count of steel")
    saddle_count = fields.Integer(string="Total Pelana", help="count of saddle")
    date = fields.Datetime(string="Date", default=_get_default_datetime)
    
    confirm_uid = fields.Many2one('res.users','Confirm By')
    confirm_date = fields.Datetime('Confirm On')
    done_uid = fields.Many2one('res.users','Done By')
    done_date = fields.Datetime('Done On')
    
    expedition_id = fields.Many2one('res.partner', string="Expedition", domain=[('category_id.name','=','Expedition')])
    vehicle_id = fields.Many2one('tw.vehicle', string='Vehicle Number', help='Vehicle Number')
    driver_id = fields.Many2one('res.partner', string="Driver", domain=[('category_id.name','=','Driver')])
    stock_inbound_ids = fields.One2many('tw.stock.inbound.line', 'stock_inbound_id', string="Stock Inbound Line", readonly=True)
    picking_count = fields.Integer(
        string="Pickings",
        compute="_compute_picking_count",
    )

    @api.depends('expedition_id')
    def _compute_picking_count(self):
        """Count related stock.picking records linked to this inbound."""
        for record in self:
            record.picking_count = self.env['stock.picking'].suspend_security().search_count([
                ('stock_inbound_id', '=', record.id),
            ])

    @api.depends('expedition_id')
    def _compute_name(self):
        for inbound in self:
            inbound.name = False
            if inbound.id:
                code = inbound.expedition_id.code or 'E'
                prefix = 'SI'
                inbound.name = inbound.env['ir.sequence'].get_sequence_code(prefix,code)

    @api.onchange('vehicle_id')
    def onchange_vehicle_id(self):
        if self.vehicle_id:
            date = self.date.strftime("%Y-%m-%d")
            data_expedition = self.get_number_plate_expedition(self.vehicle_id.plate_number, date)
            if data_expedition:
                expedition_obj = self.get_expedition(data_expedition['name'])
                self.expedition_id = expedition_obj.id
    
    @api.onchange('expedition_id')
    def onchange_expedition_id(self):
        self.driver_id = False

    @api.onchange('division')
    def onchange_division(self):
        if self.division == 'Unit':
            self.amount_of_load_uom = 'unit'
        elif self.division == 'Sparepart':
            self.amount_of_load_uom = 'package'

    @api.depends('name', 'booking_number', 'vehicle_id', 'vehicle_id.plate_number')
    def _compute_display_name(self):
        """Display name as 'plate_number-booking_number [name]'."""
        for record in self:
            plate_number = record.vehicle_id.plate_number if record.vehicle_id else ''
            booking = record.booking_number or ''
            name = record.name or ''
            record.display_name = f"{plate_number} | {booking} [{name}]".strip()
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self.check_amount_of_load(vals['amount_of_load'])
        return super(StockInbound, self).create(vals_list)
    
    def write(self, vals):
        expidition = super(StockInbound, self).write(vals)
        for record in self:
            amount_of_load = vals.get('amount_of_load')
            if amount_of_load is None:
                amount_of_load = record.amount_of_load
            record.check_amount_of_load(amount_of_load)
            if amount_of_load < record.amount_receipt:
                raise Warning(f"Amount of Load ({amount_of_load}) cannot be less than Amount of Receipt ({record.amount_receipt})!")
        return expidition 
    
    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise Warning('Attention!\nData cannot be deleted.')
        return super(StockInbound, self).unlink()
            
    def action_process(self):
        if self.state != 'draft':
            raise Warning("Expedition Has Passed the Unloading Process!")
        self.write({'state': 'open'})

    def action_done(self):
        if self.amount_of_load != self.amount_receipt:
            return True
        self.write(({
                'state':'done',
                'done_uid': self.env.user.id,
                'done_date': datetime.now()
            }))

    def action_view_pickings(self):
        """Open related stock pickings.

        Opens form view directly if only one picking exists,
        otherwise opens list view.
        """
        self.ensure_one()
        picking_obj = self.env['stock.picking'].suspend_security().search([
            ('stock_inbound_id', '=', self.id),
        ])
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Pickings',
            'res_model': 'stock.picking',
            'domain': [('stock_inbound_id', '=', self.id)],
            'context': {'default_stock_inbound_id': self.id},
        }
        if len(picking_obj) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = picking_obj.id
        else:
            action['view_mode'] = 'list,form'
        return action

    def check_amount_of_load(self, amount_of_load):
        if amount_of_load <= 0:
            raise Warning('The load quantity cannot be 0 or less, Please fill in the truck load quantity!')            

    def get_number_plate_expedition(self, expedition_number, date=None):
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        query = f"""
            SELECT DISTINCT bfcl.value AS name
                FROM tw_b2b_file bf
                LEFT JOIN tw_b2b_file_content bfc on bf.id = bfc.file_id
                LEFT JOIN tw_b2b_file_content_line bfcl on bfc.id = bfcl.file_content_id
                WHERE bf.ext = 'SL'
                    AND bfcl.name = 'nama_expedisi'
                    AND bfc.id IN (
                        SELECT bfc.id
                        FROM tw_b2b_file_content bfc
                        LEFT JOIN tw_b2b_file_content_line bfcl on bfc.id = bfcl.file_content_id
                        WHERE bfcl.value = '{expedition_number}'
                        AND bfcl.name = 'expedition_number'
                    )
                    AND bf.upload_date = '{date}'
        """
        self.env.cr.execute(query)
        return self.env.cr.dictfetchone()
    
    def get_expedition(self, name):
        expedition_obj = self.env['res.partner'].search([('name','ilike',name)],limit=1)
        if not expedition_obj:
            code = self.env['ir.sequence'].suspend_security().get_per_doc_code(name, 'EX')
            expedition_obj = self.env['res.partner'].create({
                'name': name, 
                'default_code': code,
                'category_id': [self.env.ref('tw_stock_inbound.contact_tags_expedition').id]
            })
        return expedition_obj