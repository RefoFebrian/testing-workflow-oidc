# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwBranchSetting(models.Model):
    _name = "tw.branch.setting"
    _description = 'Branch Setting'

    # 7: defaults methods
    def get_default_datetime(self):
        return datetime.now()

    # 8: fields
    name = fields.Char(string="Name")
    taxpayer_identification = fields.Char(string="NPWP")
    taxable_person = fields.Char(string="PKP")
    professional_allowance = fields.Float(string="Tunjangan Profesi (%)")
    regional_minimum_wages = fields.Float(string="UMR")
    provincial_minimum_wages = fields.Float(string="UMP")
    
    # 9: relation fields
    company_id = fields.Many2one('res.company', string='Branch', domain="[('parent_id', '!=', False)]")
    branch_head_id = fields.Many2one(comodel_name='hr.employee',string='Branch Head')
    area_manager_id = fields.Many2one('hr.employee', string='Area Manager')
    general_manager_id = fields.Many2one('hr.employee', string='General Manager')
    admin_head_id = fields.Many2one('hr.employee', string='Admin Head')
    admin_pos_id = fields.Many2one('hr.employee',string='Admin POS')
    cashier_id = fields.Many2one('hr.employee', string='Cashier')
    branch_category_id = fields.Many2one(comodel_name='tw.selection', string='Branch Category ID', compute='_compute_branch_category')
    branch_category = fields.Char(string='Branch Category', compute='_compute_branch_category')
    default_area_id = fields.Many2one('res.area', string='Default Area', help="Area untuk default area saat pembuatan karyawan")
    region_id = fields.Many2one('res.area', string='Area 1', help="Area yang muncul di laporan penjualan yang menunjukan wilayah. EX : Jawa Bali, Babel, Kalimantan")
    region_categ_id = fields.Many2one('res.area', string='Area 2', help="Kategori Area : Independent Retail, Babel, Lampung")

    # 10: constraints & sql constraints
    _sql_constraints = [('company_id_uniq', 'unique(company_id)', 'Duplicate Branch Settings. \nBranch settings for branches already exist.')]

    # 11: compute/depends & on change methods
    @api.depends('company_id', 'company_id.branch_category_id')
    def _compute_branch_category(self):
        for record in self:
            if record.company_id.branch_category_id:
                record.branch_category_id = record.company_id.branch_category_id.id
                record.branch_category = record.branch_category_id.value if record.branch_category_id else False
            else:
                record.branch_category_id = False
                record.branch_category = False

    # 12: override methods
    @api.model
    def name_get(self, context=None):
        if context is None:
            context = {}
        res = []
        for record in self:
            rec = "[%s] %s" % (record.company_id.code, record.company_id.name)
            res.append((record.id, rec))
        return res
        
    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if vals.get('company_id'):
                branch_obj = self.env['res.company'].search([('id','=',vals.get('company_id'))])
                vals['name'] = branch_obj.name

        create = super(TwBranchSetting, self).create(vals_list)
        return create 

    def write(self,vals):
        return super(TwBranchSetting, self).write(vals)
    
    
    
    # def unlink(self):
    #     raise Warning("Cannot delete records!")


    # 13: action methods
    def get_branch_setting(self, branch_obj):
        branch_setting = self.env['tw.branch.setting'].search([('company_id', '=', branch_obj.id)], limit=1)
        if not branch_setting:
            raise Warning(f"Branch setting not found for branch {branch_obj.name}")
        return branch_setting
    
    # * Example Action Methods 
    # def action_name (name: confirm, approve, reject, etc...)
    def action_name(self):

        return True

    # 14: private methods


