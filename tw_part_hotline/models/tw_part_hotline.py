# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning, ValidationError

# 4: imports from odoo modules

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib
class PartHotline(models.Model):
    _name = "tw.part.hotline"
    _description = "TW Part Hotline"

    # 7: defaults methods
    def _get_default_branch(self):
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1:
            return company_ids[0].id
        return False

    @api.model
    def _get_default_date(self):
        return fields.Date.context_today(self)

    @api.model
    def _get_default_datetime(self):
        return fields.Datetime.now()

    # 8: fields
    name = fields.Char('Name')
    date = fields.Date('Date', default=_get_default_date, readonly=True)
    chassis_number = fields.Char('No Chassis', compute='_compute_lot_data', readonly=True, store=True)
    plate_number = fields.Char('No Polisi', compute='_compute_lot_data', readonly=True, store=True)
    customer_name = fields.Char('Pembawa')
    mobile = fields.Char('No Telp')
    po_order_date = fields.Date('Tanggal Order ke MD')
    picking_count = fields.Integer('Picking Count', compute='_compute_picking_count')
    # is_check_available = fields.Boolean('Check Available')
    amount_untaxed = fields.Float('Untaxed Amount', compute='_compute_amount_total', store=True)
    amount_tax = fields.Float('Taxes', compute='_compute_amount_total', store=True)
    amount_total = fields.Float('Total', compute='_compute_amount_total', store=True)
    amount_dp = fields.Float('Amount DP', compute='_compute_dp')
    minimal_dp = fields.Float('Minimal DP',compute='_compute_minimal_dp')

    is_exception = fields.Boolean('Exceptions ?', help="Exceptions:\n a. Hotline untuk part claim C1 dan C2 tanpa DP \n b. Stok tersedia (Available))")
    is_used = fields.Boolean('Used?', default=False, compute='_compute_is_used', help="[√] Hotline sudah digunakan\n[x] Hotline belum digunakan", store=True)
    division = fields.Selection([('Sparepart', 'Sparepart')], string='Division', default='Sparepart')
    status_po = fields.Selection([
        ('draft','Draft'),
        ('done','Done')
    ],default='draft',string="Status PO")
    po_claim_type = fields.Selection([
        ('Claim C1', 'Claim C1'),
        ('Claim C2', 'Claim C2'),
        ('No Claim', 'No Claim')
    ], string='Jenis PO')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], default='draft')

    # Audit Trail
    cancel_uid = fields.Many2one('res.users','Cancel by')
    cancel_date = fields.Datetime('Cancel on')

    # 9: relation fields
    company_id = fields.Many2one('res.company', 'Branch', default=_get_default_branch,domain=[('parent_id','!=',False)])
    lot_id = fields.Many2one('stock.lot', 'No Engine')
    work_order_id = fields.Many2one('tw.work.order', 'No WO', compute='_compute_linked_wo_ps', search='_search_work_order_id', store=False)
    part_sales_id = fields.Many2one('tw.part.sales', 'No PS', compute='_compute_linked_wo_ps', search='_search_part_sales_id', store=False)
    purchase_order_id = fields.Many2one('purchase.order', 'No PO')
    purchase_order_ids = fields.One2many('purchase.order', 'part_hotline_id', string='Purchase Orders')
    is_fully_po = fields.Boolean('Fully PO', compute='_compute_is_fully_po', help="Flag untuk pengecekkan apabila semua product pada hotline sudah dilakukan PO", store=True)
    customer_id = fields.Many2one('res.partner', 'Customer', compute='_compute_lot_data', store=True)
    alocation_dp_ids = fields.One2many('tw.part.hotline.alocation.dp', 'hotline_id')
    part_detail_ids = fields.One2many('tw.part.hotline.detail', 'hotline_id')
    part_hotline_available_ids = fields.One2many('tw.part.hotline.available', 'hotline_id')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    def _compute_picking_count(self):
        for rec in self:
            rec.picking_count = self.env['stock.picking'].search_count([('part_hotline_id', '=', rec.id)])

    @api.depends('lot_id')
    def _compute_lot_data(self):
        for record in self:
            record.chassis_number = record.lot_id.chassis_number
            record.plate_number = record.lot_id.plate_number
            record.customer_id = record.lot_id.partner_id.id if record.lot_id.partner_id else False

    @api.depends('part_detail_ids.subtotal', 'part_detail_ids.price_tax')
    def _compute_amount_total(self):
        for record in self:
            record.amount_untaxed = sum(line.subtotal for line in record.part_detail_ids)
            record.amount_tax = sum(line.price_tax for line in record.part_detail_ids)
            record.amount_total = record.amount_untaxed + record.amount_tax

    @api.depends('alocation_dp_ids.amount_hl_allocation')
    def _compute_dp(self):
        for record in self:
            total = sum([x.amount_hl_allocation for x in record.alocation_dp_ids])
            record.amount_dp = total

    @api.depends('amount_total')
    def _compute_minimal_dp(self):
        for record in self:
            minimal_dp = 0
            record.minimal_dp = 0
            if int(record.amount_total) >= 0:
                minimal_dp = record.amount_total * (record.company_id.branch_setting_id.minimal_dp_part_hotline / 100)
            record.minimal_dp = minimal_dp

    @api.depends('part_detail_ids')
    def _compute_is_used(self):
        for record in self:
            record.is_used = all(line.qty_reserved > 0 and line.qty_available == 0 for line in record.part_detail_ids)

    @api.depends('part_detail_ids.qty', 'part_detail_ids.qty_available', 'purchase_order_ids.order_line.product_qty', 'purchase_order_ids.state')
    def _compute_is_fully_po(self):
        for rec in self:
            is_fully_po = False
            if rec.part_detail_ids:
                all_ordered = True
                # Get valid PO lines
                po_lines = rec.purchase_order_ids.filtered(lambda po: po.state != 'cancel').mapped('order_line')

                for detail in rec.part_detail_ids:
                    ordered_qty = sum(po_lines.filtered(lambda line: line.product_id.id == detail.product_id.id).mapped('product_qty'))
                    total_fulfilled = max(detail.qty_available, ordered_qty)
                    unfulfilled = detail.qty - total_fulfilled
                    if unfulfilled > 0:
                        all_ordered = False
                        break
                is_fully_po = all_ordered
            else:
                is_fully_po = False
            rec.is_fully_po = is_fully_po

    @api.onchange('customer_id')
    def onchange_customer_name(self):
        self.customer_name = False
        self.mobile = False
        if self.customer_id:
            self.customer_name = self.customer_id.name
            self.mobile = self.customer_id.mobile

    def _compute_linked_wo_ps(self):
        for rec in self:
            wo_line = self.env['tw.work.order.line'].sudo().search([
                ('part_hotline_id', '=', rec.id)
            ], limit=1)
            rec.work_order_id = wo_line.order_id.id if wo_line else False

            ps_line = self.env['tw.part.sales.line'].sudo().search([
                ('part_hotline_id', '=', rec.id)
            ], limit=1)
            rec.part_sales_id = ps_line.order_id.id if ps_line else False

    def _search_work_order_id(self, operator, value):
        wo_lines = self.env['tw.work.order.line'].sudo().search([
            ('order_id', operator, value)
        ])
        return [('id', 'in', wo_lines.mapped('part_hotline_id').ids)]

    def _search_part_sales_id(self, operator, value):
        ps_lines = self.env['tw.part.sales.line'].sudo().search([
            ('order_id', operator, value)
        ])
        return [('id', 'in', ps_lines.mapped('part_hotline_id').ids)]

    # 12: override methods
    @api.model
    def _needaction_domain_get(self):
        return [('state', '=', 'waiting_for_approval')]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('part_detail_ids'):
                raise ValidationError('Part detail tidak boleh kosong !')
            branch_src = self.env['res.company'].suspend_security().search([('id','=',vals['company_id'])],limit=1)
            seq_name = self.env['ir.sequence'].with_company(branch_src).get_sequence_code('HOTLINE', branch_src.code)
            vals['name'] = seq_name
        return super(PartHotline, self).create(vals_list)

    def write(self, vals):
        wo_obj = self.env['tw.work.order'].search([('order_line.part_hotline_id', '=', self.id)], limit=1)
        ps_obj = self.env['tw.part.sales'].search([('order_line.part_hotline_id', '=', self.id)], limit=1)
        if self.status_po == 'done':
            if wo_obj:
                if wo_obj.state == 'done':
                    super(PartHotline, self).write({'state': 'done'})
            elif ps_obj:
                if ps_obj.state == 'done':
                    super(PartHotline, self).write({'state': 'done'})
        return super(PartHotline, self).write(vals)

    def unlink(self):
        for x in self:
            if x.state != 'draft':
                raise UserError('Transaksi yang berstatus selain Draft tidak bisa dihapus.')
        return super(PartHotline, self).unlink()

    def action_change_product(self):
        self.ensure_one()
        form_id = self.env.ref('tw_part_hotline.tw_part_hotline_change_product_view_form').id
        return {
            'name': ('Change Product'),
            'res_model': 'tw.part.hotline',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'views': [(form_id, 'form')],
            'view_mode': 'form',
            'target': 'new',
            'view_type': 'form',
            'res_id': self.id,
        }

    def action_change_product_form(self):
        return True

    def action_view_picking(self):
        self.ensure_one()
        pickings = self.env['stock.picking'].search([('part_hotline_id', '=', self.id)])
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif len(pickings) == 1:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def _check_available_part(self):
        if not self.part_detail_ids:
            raise Warning('Part detail tidak boleh kosong !')
        
        prod_ids = {}            
        for x in self.part_detail_ids:
            if x.state == 'draft':
                x.state = 'open'
            prod_ids[x.product_id.id] = x.id

        cek_stock = """
            SELECT l.company_id
                , l.complete_name as location
                , q.product_id
                , COALESCE(MAX(date_part('days', now() - q.in_date)), 0) as aging
                , (
                    sum(
                    CASE WHEN q.consolidated_date IS NOT NULL 
                    THEN q.quantity ELSE 0 END
                    ) + 
                    sum(
                    CASE WHEN q.consolidated_date IS NULL 
                    THEN q.quantity ELSE 0 END)
                    ) - 
                    CASE WHEN l.usage='internal' 
                    THEN COALESCE(
                        (
                            SELECT sum(product_uom_qty) 
                            FROM stock_move sm 
                            LEFT JOIN stock_picking sp ON sm.picking_id = sp.id 
                            LEFT JOIN stock_picking_type spt ON sp.picking_type_id = spt.id
                            LEFT JOIN stock_location stl ON sm.location_dest_id = stl.id 
                            WHERE spt.code in ('outgoing','interbranch_out') 
                            AND sp.company_id=l.company_id 
                            AND sp.state not in ('draft','cancel','done') 
                            AND sp.division = 'Sparepart' 
                            AND sm.product_id = q.product_id
                        ),0) ELSE 0 END as stock 
            FROM stock_quant q
            INNER JOIN stock_location l ON q.location_id = l.id AND l.usage = 'internal'
            LEFT JOIN product_product p ON q.product_id = p.id
            LEFT JOIN product_template t ON p.product_tmpl_id = t.id
            LEFT JOIN product_category c ON t.categ_id = c.id 
            LEFT JOIN product_category c2 ON c.parent_id = c2.id 
            WHERE (c.name = 'Sparepart' or c2.name = 'Sparepart')  and q.product_id in %s
            GROUP BY l.id,q.product_id,l.usage,q.id
        """ %(str(tuple(prod_ids.keys())).replace(',)', ')'))
        self.env.cr.execute(cek_stock)
        ress = self.env.cr.dictfetchall()

        part_hotline_available_ids = []
        if ress:
            for res in ress:
                company_id = res.get('company_id')
                product_id = res.get('product_id')
                part_detail_obj = self.env['tw.part.hotline.detail'].search([
                    ('hotline_id','=',self.id),
                    ('product_id','=',product_id)],limit=1)
                qty_stock = res.get('stock') or 0
                location = res.get('location') 
                aging = res.get('aging') or 0
                
                if qty_stock > 0:
                    if prod_ids.get(product_id):
                        if part_detail_obj:
                            part_detail_obj.write({'is_available':True})

                    part_hotline_available_ids.append([0,False,{
                        'company_id':company_id,
                        'product_id':product_id,
                        'qty':qty_stock,
                        'name':location,
                        'aging':int(aging),
                    }])
                else:
                    if part_detail_obj:
                        part_detail_obj.write({'is_available':False})
        _logger.warning('Part Hotline Available IDS: %s' % part_hotline_available_ids)
        self.part_hotline_available_ids = False
        if len(part_hotline_available_ids) > 0:
            self.part_hotline_available_ids = part_hotline_available_ids
        # Commit agar data part_hotline_available_ids tidak ikut rollback
        # ketika action_rfa raise Warning setelah method ini
        self.env.cr.commit()

    def action_view_purchase_order(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'target': 'current',
            'res_id': self.purchase_order_id.id,
        }

    def action_view_work_order(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tw.work.order',
            'view_mode': 'form',
            'target': 'current',
            'res_id': self.work_order_id.id,
        }

    def action_view_part_sales(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tw.part.sales',
            'view_mode': 'form',
            'target': 'current',
            'res_id': self.part_sales_id.id,
        }   

    def action_print_form(self):
        return self.env.ref('tw_part_hotline.action_tw_part_hotline_print_pdf').report_action(self)
            
    def cek_sparepart_hotline(self,company_id,product_id):
        obj_hotline_detail = []
        obj_hotline = self.search([('state','=','approved'),('status_po','=','draft'),('company_id','=',company_id)])
        if obj_hotline:
            hotline_ids = [htl.id for htl in obj_hotline]
            obj_hotline_detail = self.env["tw.part.hotline.detail"].search([('hotline_id','in',hotline_ids),('product_id','=',product_id)],order="create_date desc")
        
        return obj_hotline_detail

    def _check_po_done(self):
        # Jika Hotline Detail sudah tidak ada maka status po done
        for record in self.part_detail_ids:
            status_po = self.env['tw.part.hotline.detail'].sudo().search([
                ('hotline_id','=',record.hotline_id.id),
                ('qty_available','<',record.qty)])
            # Jika satu terpenuhi maka hotline bisa digunakan di PS/WO
            if not status_po:
                self.status_po = 'done'

    def _check_line_qty_available(self):
        for record in self.part_detail_ids:
            if record.qty_available < record.qty:
                raise UserError('Qty Available tidak mencukupi')