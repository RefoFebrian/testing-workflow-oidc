# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
import os
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
import odoo.addons.base.models.decimal_precision as dp

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TWNrfsLine(models.Model):
    _name = "tw.nrfs.line"
    _description = "NRFS - Detail Masalah"

    def _get_default_main_dealer_code(self):
        return self.env['res.company'].get_default_main_dealer_code()

    distribution_number = fields.Char(string='No Distribusi')
    description = fields.Char(related='product_sparepart_id.product_tmpl_id.default_code', string='Deskripsi Part')
    qty = fields.Float(string='Qty', default=1, digits='Product Unit of Measure')
    total_stock = fields.Float(string='Qty Avb Vendor', digits='Product Unit of Measure')
    total_stock_md = fields.Float(string='Qty Avb MD', digits='Product Unit of Measure')
    total_stock_all = fields.Float(string='Qty Avb All', digits='Product Unit of Measure')
    is_order_sparepart = fields.Boolean(string='Sparepart dipesan?', default=False)
    is_confirmed_by_md = fields.Boolean(string='Sudah konfirmasi MD?', compute='_compute_md_state')
    is_stock_ok = fields.Boolean(string='Stock Sparepart OK?', compute='_compute_stock')
    
    nrfs_id = fields.Many2one('tw.nrfs', string='NRFS ID')
    rel_partner_id = fields.Many2one(related='nrfs_id.branch_partner_id', string='Vendor')
    handling_id = fields.Many2one('tw.selection', string='Penanganan', domain="[('type','in',['PenangananUnitMd','PenangananUnitVendor'])]")
    vendor_handling_id = fields.Many2one('tw.selection', string='Vendor Penanganan', domain="[('type','=','PenangananUnitVendor')]")
    product_unit_id = fields.Many2one('product.product', string='Unit')
    product_sparepart_id = fields.Many2one('product.product', string='Parts Bermasalah')
    available_sparepart_ids = fields.Many2many('product.product', string='Available Sparepart', compute='_compute_available_sparepart_ids')
    service_ids = fields.Many2many('product.product', 'tw_nrfs_line_jasa_rel', 'line_id', 'service_id', string='Jasa')
    stock_ids = fields.One2many('tw.nrfs.line.stock', 'line_id', string='Info Stok')
    reason_ids = fields.Many2many('tw.selection', 'tw_nrfs_penyebab_selection_rel', 'nrfs_line_id', 'penyebab_id', string='Penyebab', domain=[('type','=','PenyebabNrfs')])
    indication_ids = fields.Many2many('tw.selection', 'tw_nrfs_gejala_selection_rel', 'nrfs_line_id', 'gejala_id', string='Gejala', domain=[('type','=','GejalaNrfs')])

    _sql_constraints = [
        ('unique_product_sparepart_id', 'unique(nrfs_id, product_sparepart_id)', 'Ditemukan part duplicate, silahkan cek kembali!'),
    ]

    @api.depends('nrfs_id.is_p2p_md')
    def _compute_md_state(self):
        for record in self:
            record.is_confirmed_by_md = record.nrfs_id.is_p2p_md

    @api.depends('qty','total_stock')
    def _compute_stock(self):
        for record in self:
            if record.total_stock < record.qty:
                record.is_stock_ok = False
            else:
                record.is_stock_ok = True

    @api.depends('product_sparepart_id', 'nrfs_id.product_id.product_tmpl_id.part_unit_id')
    def _compute_available_sparepart_ids(self):
        ProductProduct = self.env['product.product']
        for record in self:
            if record.nrfs_id.product_id.product_tmpl_id.part_unit_id:
                # part_code_id adalah product.template, perlu cari product.product-nya
                template_ids = record.nrfs_id.product_id.product_tmpl_id.part_unit_id.line_ids.mapped('part_code_id').ids
                record.available_sparepart_ids = ProductProduct.search([('product_tmpl_id', 'in', template_ids)])
            else:
                products = ProductProduct.suspend_security()._get_product_ids_by_division('Sparepart')
                if products:
                    record.available_sparepart_ids = ProductProduct.browse([rec[0] for rec in products])
                else:
                    record.available_sparepart_ids = ProductProduct
        
    @api.onchange('product_sparepart_id')
    def _onchange_product_sparepart_id(self):
        self.qty = 1
        self.reason_ids = False
        self.indication_ids = False

    @api.onchange('product_sparepart_id','qty')
    def _onchange_stock(self):
        self._show_part_stock_all()

    @api.onchange('vendor_handling_id')
    def _onchange_is_order_sparepart_and_handling_id(self):
        self.is_order_sparepart = False
        self.handling_id = False
        if self.vendor_handling_id:
            self.handling_id = self.vendor_handling_id.id
            if self.vendor_handling_id.id == self.env.ref('tw_nrfs.nrfs_penanganan_unit_part_pesan_biasa').id:
                self.is_order_sparepart = True
            
    def _check_part_stock(self, product_id, where_partner):
        _get_stock_query = """
            SELECT 
                dealer.id AS company_id,
                COALESCE(st.qty_stock,0) - (COALESCE(intransit_out.qty_intransit_out,0) + COALESCE(so_md.qty_rfa,0) + COALESCE(mo_md.qty_rfa,0)) AS qty_stock,
                COALESCE(intransit_in.qty_intransit_in,0) AS qty_intransit_in
            FROM res_company dealer
            JOIN res_partner dealer_p ON dealer.partner_id = dealer_p.id
            LEFT JOIN (
                SELECT 
                    b.id AS company_id,
                    SUM(COALESCE(sq.quantity,0)) AS qty_stock
                FROM stock_quant sq
                JOIN stock_location l ON sq.location_id = l.id
                JOIN res_company b ON l.company_id = b.id
                JOIN res_partner p ON b.partner_id = p.id
                WHERE l.usage = 'internal'
                AND sq.product_id = %d
                GROUP BY b.id, sq.product_id
            ) st ON dealer.id = st.company_id
            LEFT JOIN (
                SELECT 
                    b.id AS company_id,
                    SUM(COALESCE(sm.product_uom_qty,0)) AS qty_intransit_out
                from stock_picking sp
                JOIN stock_picking_type spt ON sp.picking_type_id = spt.id
                JOIN stock_move sm ON sp.id = sm.picking_id
                JOIN res_company b ON sp.company_id = b.id
                JOIN res_partner p ON b.partner_id = p.id
                WHERE spt.code IN ('outgoing','interbranch_out')
                AND sp.state NOT IN ('draft','cancel','done')
                AND sm.product_id = %d
                GROUP BY b.id, sm.product_id
            ) intransit_out ON dealer.id = intransit_out.company_id
            LEFT JOIN (
                SELECT 
                    b.id as company_id,
                    SUM(COALESCE(sm.product_uom_qty,0)) AS qty_intransit_in
                FROM stock_picking sp
                JOIN stock_picking_type spt ON sp.picking_type_id = spt.id
                JOIN stock_move sm ON sp.id = sm.picking_id
                JOIN res_company b ON sp.company_id = b.id
                JOIN res_partner p ON b.partner_id = p.id
                WHERE spt.code IN ('incoming','interbranch_in')
                AND sp.state NOT IN ('draft','cancel','done')
                AND sm.product_id = %d
                GROUP BY b.id, sm.product_id
            ) intransit_in ON dealer.id = intransit_in.company_id
            LEFT JOIN (
                SELECT
                    b.id as company_id,
                    COALESCE(SUM(sol.product_uom_qty),0) AS qty_rfa
                FROM tw_sale_order_line sol
                JOIN tw_sale_order so ON sol.order_id = so.id
                JOIN res_company b ON so.company_id = b.id
                JOIN res_partner p ON b.partner_id = p.id
                WHERE so.division = 'Sparepart'
                AND so.state IN ('waiting_for_approval','approved')
                AND sol.product_id = %d
                GROUP BY b.id, sol.product_id
            ) so_md ON dealer.id = so_md.company_id
            LEFT JOIN (
                SELECT
                    b.id as company_id,
                    COALESCE(SUM(mol.qty),0) AS qty_rfa
                FROM tw_mutation_order_line mol
                JOIN tw_mutation_order mo ON mol.mutation_order_id = mo.id
                JOIN res_company b ON mo.company_id = b.id
                JOIN res_partner p ON b.partner_id = p.id
                WHERE mo.division = 'Sparepart'
                AND mo.state IN ('waiting_for_approval','approved')
                AND mol.product_id = %d
                GROUP BY b.id, mol.product_id
            ) mo_md ON dealer.id = mo_md.company_id
            %s
            AND COALESCE(st.qty_stock,0) - (COALESCE(intransit_out.qty_intransit_out,0) + COALESCE(so_md.qty_rfa,0) + COALESCE(mo_md.qty_rfa,0)) + COALESCE(intransit_in.qty_intransit_in,0) > 0 
        """ % (product_id, product_id, product_id, product_id, product_id, where_partner)
        self._cr.execute(_get_stock_query)
        stock_ress = self._cr.dictfetchall()
        return stock_ress

    def _show_part_stock_all(self):
        self.total_stock = 0
        self.total_stock_all = 0
        self.stock_ids = False
        
        if self.rel_partner_id and self.product_sparepart_id and self.qty:
            total_stock = 0
            total_stock_md = 0
            total_stock_all = 0
            stock_vals = []
            md_obj = self.env['res.company'].suspend_security().search([('code','=',self._get_default_main_dealer_code())],limit=1)

            where_partner = " WHERE dealer_p.id IN %s " % (str(tuple([self.rel_partner_id.id])).replace(",)",")"))
            stock = self._check_part_stock(self.product_sparepart_id.id, where_partner)
            for record in stock:
                total_stock += record['qty_stock'] + record['qty_intransit_in']

            where_partner_md = " WHERE dealer_p.id IN %s " % (str(tuple([md_obj.partner_id.id])).replace(",)",")"))
            stock = self._check_part_stock(self.product_sparepart_id.id, where_partner_md)
            for record in stock:
                total_stock_md += record['qty_stock'] + record['qty_intransit_in']

            where_partner_all = " WHERE (dealer.default_supplier_id = %d OR dealer_p.id = %d) " % (md_obj.partner_id.id, md_obj.partner_id.id)
            stock = self._check_part_stock(self.product_sparepart_id.id, where_partner_all)
            for record in stock:
                stock_vals.append([0,0,record])
                total_stock_all += record['qty_stock'] + record['qty_intransit_in']

            self.total_stock = total_stock
            self.total_stock_md = total_stock_md
            self.total_stock_all = total_stock_all
            self.stock_ids = stock_vals

