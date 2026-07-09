# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TWStockOpnameAsset(models.Model):
    _name = "tw.stock.opname.asset"
    _inherit = ["tw.attachment.mixin"]
    _description = "TW Stock Opname Asset"
    _order = "id desc"

    def _get_default_date(self):
        return datetime.now()

    def _get_category_asset(self):
        ids = [('All','All')]
        query = """
            SELECT asset_code
            FROM account_asset_category
            group by asset_code
        """
        self.env.cr.execute(query)  
        ress = self.env.cr.dictfetchall()
        for res in ress:
            ids.append((res.get('asset_code'),(res.get('asset_code'))))
        return ids

    # 8: fields
    name = fields.Char(string="Name", readonly=True, default='New', copy=False, index=True, compute='_compute_name', store=True)
    date = fields.Date('Tanggal SO',default=_get_default_date)
    category = fields.Selection(_get_category_asset,string="Kategory")

    state_asset = fields.Selection([('all','All'), ('active','Active'), ('disposed','Disposed'), ('draft','Draft')],default="active")
    generate_date = fields.Datetime('Generate on', default=fields.Datetime.now())
    
    state = fields.Selection([
        ('draft','Draft'),
        ('posted','Posted')],default="draft")
    
    note_bakso = fields.Text('Note')
    is_pilot = fields.Boolean(string='Is Pilot?',default=False)
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options('Umum'))

    saldo_sistem = fields.Integer(
        string="Total Sistem", 
        compute='_compute_saldo_bakso'
    )
    saldo_cabang = fields.Integer(
        string="Fisik (Di Cabang)", 
        compute='_compute_saldo_bakso'
    )
    saldo_pic = fields.Integer(
        string="Fisik (Dipinjam PIC)", 
        compute='_compute_saldo_bakso'
    )
    saldo_hilang = fields.Integer(
        string="Fisik (Tidak Diketahui)", 
        compute='_compute_saldo_bakso'
    )
    saldo_tidak_ada = fields.Integer(
        string="Fisik (Tidak Ada)", 
        compute='_compute_saldo_bakso'
    )
    other_asset_count = fields.Integer(
        string="Total Fisik Tidak Tercatat", 
        compute='_compute_saldo_bakso'
    )
    total_stock = fields.Integer(
        string="Total Fisik Aset", 
        compute='_compute_saldo_bakso'
    )
    total_fisik_tercatat = fields.Integer(
        string="Total Fisik Tercatat Sistem",
        compute='_compute_saldo_bakso'
    )
    
    
    # 9: Relation fields
    company_id = fields.Many2one('res.company','Branch',index=True)
    asset_id = fields.Many2one('account.asset.asset', string="Asset", readonly=True)
    detail_ids = fields.One2many('tw.stock.opname.asset.line','opname_id')
    other_asset_ids = fields.One2many('tw.stock.opname.asset.other','opname_id')
    pdi_id = fields.Many2one('hr.employee','PDI / Kamek / SA',domain="[('company_id', '=', company_id)]")
    adh_id = fields.Many2one('hr.employee','ADH',domain="[('company_id', '=', company_id)]")
    soh_id = fields.Many2one('hr.employee','SOH',domain="[('company_id', '=', company_id)]")


    # Audit Trail 
    post_date = fields.Datetime('Posted on')
    post_uid = fields.Many2one('res.users','Posted by')

    @api.model_create_multi
    def create(self,vals_list):
        return super(TWStockOpnameAsset,self).create(vals_list)
    
    def write(self,vals):
        return super(TWStockOpnameAsset,self).write(vals)
    
    def read(self, fields=None, load='_classic_read'):
        # * Override method read to check is pilot
        res = super(TWStockOpnameAsset, self).read(fields=fields, load=load)
        # TODO: Need to be confirmed, cause its slow down the loading
        field_checker = self._fields or fields
        if 'is_pilot' in field_checker:
            for record in self:
                branch_id = record.company_id.id
                if 'company_id' in record:
                    branch_id = record['company_id']
                record['is_pilot'] = record._set_is_pilot(company_id=branch_id.id)

        return res

    def unlink(self):
        for data in self:
            if data.state != "draft":
                raise Warning("Tidak bisa menghapus data yang berstatus selain draft!")
        return super(TWStockOpnameAsset, self).unlink()

    # Computed and Onchange method
    @api.depends('company_id')
    def _compute_name(self):
        for rec in self:
            if not rec.name or rec.name == 'New':
                if rec.company_id:
                    rec.name = self.env['ir.sequence'].get_sequence_code('SOAST', rec.company_id.code)

    @api.onchange('company_id')
    def onchange_is_pilot(self):
        self.is_pilot = False
        if self.company_id:
            self.is_pilot = self._set_is_pilot(company_id=self.company_id.id)

    @api.depends('detail_ids', 'other_asset_ids')
    def _compute_saldo_bakso(self):
        """
        Menghitung semua nilai yang dibutuhkan untuk laporan Berita Acara (BASO).
        """
        for record in self:
            record.saldo_sistem = len(record.detail_ids)
            record.other_asset_count = len(record.other_asset_ids)
            
            record.saldo_cabang = len(record.detail_ids.filtered(lambda l: l.asset_status == 'di_cabang'))
            record.saldo_pic = len(record.detail_ids.filtered(lambda l: l.asset_status == 'dipinjam_pic'))
            record.saldo_hilang = len(record.detail_ids.filtered(lambda l: l.asset_status == 'tidak_diketahui'))
            record.saldo_tidak_ada = len(record.detail_ids.filtered(lambda l: l.physical_validation == 'fisik_tidak_ada'))
            
            record.total_fisik_tercatat = record.saldo_cabang + record.saldo_pic
            record.total_stock = record.saldo_cabang + record.saldo_pic + record.other_asset_count


    # Action method
    def action_generate_stock(self):
        if self.generate_date:
            raise Warning('Data Stock Asset telah terbentuk. Silahkan refresh halaman ini !')
        
        query_where = "WHERE 1=1"
        if self.company_id:
            query_where += " AND asset.company_id = %d" %self.company_id
        
        if self.state_asset == 'draft' :
            query_where += " AND asset.state = 'draft'"
        elif self.state_asset == 'active' :
            query_where += " AND asset.state in ('open','CIP','close') "
        elif self.status == 'disposed' :
            query_where += " AND asset.state = 'disposed'"
        
        if self.category:
            if self.category != 'All':
                query_where += " AND category.asset_code = '%s'" %self.category

        query = """
            SELECT asset.code as asset_code
            , asset.name as register_no
            , pp.default_code as asset_name
            , category.name as category_name
            , category.asset_code as category_code
            FROM account_asset_asset asset
            INNER JOIN account_asset_category category ON category.id = asset.category_id
            LEFT JOIN product_product pp ON pp.id = asset.product_id
            %s
            ORDER BY asset_name,code ASC
        """ %(query_where)
        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()
        lines = []
        for res in ress:
            lines.append([0,False,{
                'code':res.get('asset_code'),
                'register_no':res.get('register_no'),
                'name':res.get('asset_name'),
                'category':res.get('category_code'),
                'description':res.get('category_name'),
            }])
        self.write({
            'generate_date':self.date,
            'detail_ids':lines
        })
        
    def action_post(self):
        self._check_line()
        line = self.env['tw.stock.opname.asset.line'].search([
            ('opname_id','=',self.id),
            ('physical_validation','=',False),
            ('asset_status','=',False)],limit=1)
        if line:
            raise Warning('Perhatian ! Ceklis Validasi Lokasi masih ada yang belum diisi !')
        self.write({
            'post_uid':self._uid,
            'post_date':self.date,
            'state':'posted'
        })

    def action_print_validasi(self):
        """
        Mencetak laporan validasi SO Asset (gaya Odoo 18).
        Kita tidak perlu mengirim 'datas' dictionary manual.
        Template QWeb akan membaca langsung dari 'self' (yang akan menjadi 'docs' di template).
        """
        # Cukup panggil report action, QWeb akan menangani sisanya
        return self.env.ref('tw_stock_opname_asset.action_stock_opname_asset_print_validasi').report_action(self)  

    # Di dalam class TWStockOpnameAsset

    def action_bakso(self):
        """
        Method ini sekarang hanya membuka wizard untuk mengisi 'note_bakso'.
        """
        form_id = self.env.ref('tw_stock_opname_asset.view_tw_stock_opname_asset_baso_wizard').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Berita Acara SO',
            'res_model': 'tw.stock.opname.asset.baso.wizard',
            'view_mode': 'form',
            'view_id': form_id,
            'target': 'new',
            'context': {
                'default_opname_id': self.id,
                'default_note_bakso': self.note_bakso,
            },
        }


    def action_download_excel(self):
        """
        Method ini sekarang akan langsung memanggil logika ekspor
        tanpa membuat wizard perantara yang tidak perlu.
        """
        self.ensure_one()
        
        exporter = self.env['tw.stock.opname.asset.excel'].create({
            'stock_opname_asset_id': self.id
        })
        
        return exporter.action_import_excel()

   
    # Private Method
    def _set_is_pilot(self,company_id=None):
        is_pilot = False
        if company_id:
            pilot_branches = self.env['tw.pilot.project'].sudo().search([
                    ('name','=','ATTACHMENT STOCK OPNAME'),
                    ('company_ids','in',[company_id])
                ])
            if pilot_branches:
                is_pilot = True
        
        return is_pilot

    def _check_line(self):
        if not self.detail_ids:
            raise Warning('Tidak ada data Asset untuk di-post !')