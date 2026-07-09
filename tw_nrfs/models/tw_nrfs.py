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

class TWNrfs(models.Model):
    _name = "tw.nrfs"
    _description = "Not Ready For Sale"
    _order = "id desc"

    def _get_default_date(self):
        return self.env['res.company'].get_default_date()

    name = fields.Char(string='No NRFS',compute='_compute_name',store=True)
    origin = fields.Char(string='Source Document')
    nrfs_date = fields.Date(string='Date', default=_get_default_date)
    est_completion_date = fields.Date(string='Estimasi Selesai')
    act_completion_date = fields.Date(string='Aktual Selesai')
    nrfs_type = fields.Selection([
        ('LKUAT','LKUAT'),
        ('LKUAS','LKUAS')
    ], string='Tipe NRFS')
    state = fields.Selection([
        ('cancel', 'Cancelled'),
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'), # NOTE: in this state, all stock part OK
        ('in_progress', 'In Progress'),
        ('done', 'Done')
    ], string='Status', default='draft')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
    
    is_p2p_md = fields.Boolean(string='Dipenuhi dengan P2P?')
    is_order_sparepart = fields.Boolean(string='Sparepart dipesan?')
    is_fulfilled_sparepart = fields.Boolean(string='Seluruh sparepart dipenuhi?', default=False)
    is_send_to_ahm = fields.Boolean(string='Kirim ke AHM?', default=False)
    mft_nrfs = fields.Boolean(string='Sudah kirim MFT NRFS?', default=False)
    expedition_ship = fields.Char(string='Nama Kapal', size=100)
    
    # Audit Trail 
    cancel_uid = fields.Many2one('res.users', string='Cancelled by')
    cancel_date = fields.Datetime(string='Cancelled on')
    confirm_uid = fields.Many2one('res.users', string='Confirmed by')
    confirm_date = fields.Datetime(string='Confirmed on')
    
    # Relation Field (Many2one)
    product_id = fields.Many2one('product.product', string='Tipe Unit')
    backorder_id = fields.Many2one('tw.nrfs', string='Related NRFS', domain="[('nrfs_date','<',nrfs_date),('state','in',['confirmed','in_progress','done'])]")
    branch_partner_id = fields.Many2one('res.partner', string='AHASS Vendor', check_company=False, domain=[('category_id.name', '=', 'AHASS')])
    driver_id = fields.Many2one('res.partner', string='Driver Expedisi', check_company=False, domain=[('category_id.name', '=', 'Driver')])
    vehicle_id = fields.Many2one('tw.vehicle', string='Nopol Expedisi')
    company_id = fields.Many2one('res.company', string="Branch")
    examiner_id = fields.Many2one('hr.employee', string='Nama Pemeriksa')
    
    # Relational Field (One2many)
    line_ids = fields.One2many('tw.nrfs.line', 'nrfs_id', string='Detail NRFS')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('branch_partner_id')
    def _change_stock(self):
        self.action_check_availability()
        
    @api.depends('company_id')
    def _compute_name(self):
        for record in self:
            nrfs_type = record.nrfs_type if record.nrfs_type else 'NRFS'
            seq_name = self.env['ir.sequence'].with_company(record.company_id).get_sequence_code(nrfs_type, record.company_id.code)
            record.name = seq_name

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        return super(TWNrfs, self).create(vals_list)

    def write(self, vals):
        if vals.get('est_completion_date'):
            est_completion_date = datetime.strptime(vals.get('est_completion_date'), '%Y-%m-%d').date()
            if est_completion_date < date.today():
                raise Warning('Tanggal estimasi selesai tidak boleh kurang dari tanggal Hari ini!')

        if self.state in ['approved','confirmed'] and self.division == 'Unit':
            is_order_sparepart = {}
            is_fulfilled_sparepart = {}
            for x in self.line_ids:
                if not is_order_sparepart.get(x.id,False):
                    is_order_sparepart.update({x.id: False})
                is_order_sparepart[x.id] = x.is_order_sparepart
                if x.is_order_sparepart:
                    if not is_fulfilled_sparepart.get(x.id,False):
                        is_fulfilled_sparepart.update({x.id: False})
                    is_fulfilled_sparepart[x.id] = x.distribution_number
            if vals.get('line_ids',False):
                penanganan_by_md = [
                    self.env.ref('tw_nrfs.nrfs_penanganan_unit_part_pesan_biasa').id,
                    self.env.ref('tw_nrfs.nrfs_penanganan_unit_part_pesan_urgent').id
                ]
                for x in vals['line_ids']:
                    if x[0] == 1: # Update data
                        if x[2].get('handling_id', False):
                            if self.state == 'confirmed' and x[2]['handling_id'] not in penanganan_by_md:
                                raise Warning("Penanganan yang bisa dipilih hanya:\n1. Diperbaiki dengan sparepart pesan (Jalur Biasa)\n2. Diperbaiki dengan sparepart pesan (PO Urgent)")
                        if 'is_order_sparepart' in x[2].keys():
                            is_order_sparepart[x[1]] = x[2]['is_order_sparepart']
                        if 'distribution_number' in x[2].keys():
                            is_fulfilled_sparepart[x[1]] = x[2]['distribution_number']
            vals['is_order_sparepart'] = any([val for _, val in is_order_sparepart.items()])
            vals['is_fulfilled_sparepart'] = all([val for _, val in is_fulfilled_sparepart.items()])
        return super(TWNrfs, self).write(vals)

    def unlink(self):
        raise Warning('Data NRFS tidak bisa dihapus!')

    def copy(self):
        raise Warning('Data NRFS tidak bisa diduplikasi!')

    # 13: action methods
    def action_check_availability(self):
        for line in self.line_ids:
            line._show_part_stock_all()
            
    def action_cancel(self):
        self.write({
            'state': 'cancel',
            'cancel_uid': self._uid,
            'cancel_date': self._get_default_date()
        })

    def action_confirm(self):
        if self.division == 'Unit':
            self._check_line_ids()
            # check penanganan dan jasa
            msg = ""
            for line in self.line_ids:
                if len(line.service_ids) <= 0:
                    msg += "Jasa perbaikan untuk sparepart bermasalah %s harus diisi!\n" % (line.product_sparepart_id.product_tmpl_id.name)
                if not line.vendor_handling_id:
                    msg += "Penanganan untuk sparepart bermasalah %s harus diisi!\n" % (line.product_sparepart_id.product_tmpl_id.name)
            if msg:
                raise Warning(msg)
            # cek stok
            self.action_check_availability()

        self.write({
            'state': 'confirmed',
            'confirm_uid': self._uid,
            'confirm_date': datetime.now()
        })

    # 14: private methods
    def _check_line_ids(self):
        if len(self.line_ids) <= 0:
            raise Warning('Detail masalah harus diisi!')
        msg = ""
        for line in self.line_ids:
            if len(line.indication_ids) <= 0:
                msg += "Gejala untuk sparepart bermasalah %s harus diisi!\n" % (line.product_sparepart_id.product_tmpl_id.name)
            if len(line.reason_ids) <= 0:
                for reason in line.reason_ids:
                    msg += "Penyebab untuk sparepart bermasalah %s harus diisi!\n" % (reason.penyebab_id.name)
            if line.qty <= 0:
                msg += "Qty sparepart bermasalah %s harus lebih dari 0!\n" % (line.product_sparepart_id.product_tmpl_id.name)
        if msg:
            raise Warning(msg)
        
        