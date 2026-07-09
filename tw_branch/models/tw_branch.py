# -*- coding: utf-8 -*-

from odoo import models, fields, api, Command, _
from odoo.exceptions import AccessError
from odoo.exceptions import AccessError, UserError as Warning
from datetime import datetime, timedelta, date


class ResBranch(models.Model):
    _inherit = "res.company"
    _rec_names_search = ['name', 'code']

    def _get_default_parent_company(self):
        company_id = self.env.user.company_id
        if company_id.parent_id:
            return company_id.parent_id.id
        return company_id

    code = fields.Char(string='Code')
    atpm_code = fields.Char(string='ATPM Code')
    rt = fields.Char(string='RT',size=3)
    rw = fields.Char(string='RW',size=3)
    npwp = fields.Char(string='No NPWP')
    profit_centre = fields.Char(string='Profit Centre')
    establishment_date = fields.Date(string='Tanggal Kukuh')
    is_supplier_is_internal = fields.Boolean(default=False,help="Digunakan untuk membedakan bahwa Branch ini adalah Branch Internal (Internal Companies Group / Retail)")
    branch_class = fields.Selection(selection=lambda self: self.env['tw.selection'].get_option_list('BranchClass'), default='-')
    finance_email = fields.Char(string="Finance Email", help="Use to send payment notification email to the company")

    branch_category_id = fields.Many2one(comodel_name='tw.selection', string="Branch Category", domain=[('type', '=', 'BranchCategory')])
    branch_type_id = fields.Many2one(comodel_name='tw.selection', string="Branch Type", domain=[('type','=','BranchType')])
    parent_id = fields.Many2one('res.company', string='Parent Company',default=_get_default_parent_company, help="Parent company, for example [DDS] Saharjo will have [H2Z] Tunas Dwipa Matra as parent")
    dealer_class_id = fields.Many2one(comodel_name='tw.selection', string="Dealer Class", domain=[('type', '=', 'DealerClass')])
    default_supplier_id = fields.Many2one(comodel_name='res.partner',string='Principle',domain=[('category_id.name','=','Principle')], help="Default supplier for the branch. Can refer to the Main Dealer, for example [DDS] Saharjo will have [WMS] Wahana Makmur Sentosa as default supplier")
    city_id = fields.Many2one(comodel_name='res.city',  string="Kabupaten",  help="")
    district_id = fields.Many2one(comodel_name='res.district',  string="Kecamatan",  help="")
    sub_district_id = fields.Many2one(comodel_name='res.sub.district',  string="Kelurahan",  help="")


    @api.onchange('city_id')
    def _onchange_city_id(self):
        self.city = False
        if self.city_id:
            self.city = self.city_id.name

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            args = ['|',('name', operator, name),('code', operator, name)] + args
        records = self.search_fetch(args, ['display_name'], limit=limit)
        return [(record.id, record.display_name) for record in records.sudo()]
    
    @api.depends('name','code')
    def _compute_display_name(self):
        res = super()._compute_display_name()
        for co in self:
            co.display_name = f'[{co.code}] {co.name}'

        return res
        
    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            create_partner = self.create_partner(vals)
            vals['partner_id'] = create_partner.id
        return super(ResBranch, self).create(vals_list)
    
    def action_sync_partner_data(self):
        """Manual sync data from company to partner"""
        for record in self:
            if record.partner_id:
                # Update partner yang sudah ada
                sync_vals = {
                    'name': record.name,
                    'code': record.code,
                    'street': record.street,
                    'street2': record.street2,
                    'state_id': record.state_id.id if record.state_id else False,
                    'city_id': record.city_id.id if record.city_id else False,
                    'district_id': record.district_id.id if record.district_id else False,
                    'sub_district_id': record.sub_district_id.id if record.sub_district_id else False,
                    'phone': record.phone,
                    'mobile': record.mobile,
                    'email': record.email,
                    'zip': record.zip,
                    'rt': record.rt,
                    'rw': record.rw,
                    'category_id': [(6, 0, self.env.ref('tw_partner.contact_tags_branch').ids)],
                }
                record.partner_id.suspend_security().write(sync_vals)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Partner data has been synchronized successfully.'),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def get_formview_action(self, access_uid=None):
        """ Override this method in order to redirect many2one towards the right model depending on access_uid """
        user = self.env.user
        if access_uid:
            user = self.env['res.users'].browse(access_uid).sudo()
        if not user.has_group('tw_branch.group_tw_company_form_read'):
            raise AccessError(_("You do not have access to this document."))
            
        res = super().get_formview_action(access_uid=access_uid)
        return res
        
    
    def create_partner(self,vals):
        partner_vals = self.prepare_partner_vals(vals)
        
        return self.env['res.partner'].suspend_security().create(partner_vals)
    
    def prepare_partner_vals(self,vals):
        partner_vals = {
            'name': vals.get('name'),
            'code': vals.get('code'),
            'street': vals.get('street'),  
            'street2': vals.get('street2'),
            'state_id': vals.get('state_id'),
            'city_id': vals.get('city_id'),  
            'district_id': vals.get('district_id'),
            'sub_district_id': vals.get('sub_district_id'),
            'phone': vals.get('phone'),
            'mobile': vals.get('mobile'),
            'email': vals.get('email'),     
            'company_id': vals.get('parent_id') if vals.get('parent_id') else False,
            'category_id': [(6, 0, self.env.ref('tw_partner.contact_tags_branch').ids)]         
            }
        
        return partner_vals

    def get_default_date(self):
        admin_user = self.env.ref('base.user_admin', raise_if_not_found=False) or self.env.user
        tz = admin_user.tz or self.env.user.tz or self.env.context.get('tz')
        default_date = fields.Date.context_today(self.with_context(tz=tz))
        return fields.Date.to_string(default_date)
    
    def get_default_main_dealer(self):
        branch_type_md = self.env['tw.selection'].get_selection('BranchType', 'MD')
        if not branch_type_md:
            raise Warning("No branch type 'Main Dealer' found in your master")
        active_branch = self.env.company
        parent_branch = active_branch.parent_id
        if parent_branch:
            md_branch = self.env['res.company'].suspend_security().search([('branch_type_id', '=', branch_type_md.id),('parent_id', '=', parent_branch.id)], order='id', limit=1)
        else:
            md_branch = self.env['res.company'].suspend_security().search([('branch_type_id', '=', branch_type_md.id)], order='id', limit=1)
        if not md_branch:
            raise Warning("No branch with 'Main Dealer' type found in your branch data")
        return md_branch

    def get_default_ho_branch(self):
        branch_type_md = self.env['tw.selection'].get_selection('BranchType', 'HO')
        if not branch_type_md:
            raise Warning("No branch type 'Head Office' found in your master")
        ho_branch = self.env['res.company'].suspend_security().search([('branch_type_id', '=', branch_type_md.id)], order='id', limit=1)
        if not ho_branch:
            raise Warning("No branch with 'Head Office' type found in your branch data")
        return ho_branch
    
    def get_default_main_dealer_code(self):
        return self.get_default_main_dealer().code

    def get_default_main_dealer_atpm_code(self):
        return self.get_default_main_dealer().atpm_code
    
    def _accessible_branches(self):
        if self:
            return super()._accessible_branches()
        return self.env.companies
