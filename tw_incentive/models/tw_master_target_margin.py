# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError, AccessError

# 5: local imports

# 6: Import of unknown third party lib


class MasterTargetMargin(models.Model):
    _name = "tw.master.target.margin"
    _description = "Master Target Margin"
    _order = "id desc"

    # 7: defaults methods
    def _get_default_datetime(self):
        return fields.Datetime.now()
    
    # 8: fields
    name = fields.Char()
    job = fields.Selection(selection=[
        ('sales', 'Salesman (Partner, Sales Payroll)'),
        ('sc', 'Sales Counter'),
        ('sco', 'SCO')], string="Job",  help="")
    state = fields.Selection(selection=[
        ('draft','Draft'),
        ('active','Active'),
        ('expired','Expired'),
        ('rejected','Rejected')],  string="state",  default='draft', help="")
    date = fields.Datetime('Active Date')
    
    # 9: relation fields
    company_id = fields.Many2one(comodel_name='res.company', string="Branch", help="")
    target_margin_line_ids = fields.One2many(
        comodel_name='tw.master.target.margin.line',
        inverse_name="target_margin_id",
        string="Target margin lines",
        help=""
    )
    
    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    
    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            vals['name'] = self._get_default_datetime()
            vals['date'] = vals.get('date', self._get_default_datetime())
            # vals['state'] = vals.get('state', 'active')

            existing_master = self.suspend_security().search([
                ('company_id', '=', vals['company_id']),
                ('job', '=', vals['job']),
                ('state', '=', 'active')])
            if existing_master :
                existing_master.write({'state': 'expired'})

        create = super(MasterTargetMargin,self).create(vals_list)
        create.check_all_series()
        return create

    def write(self, vals):
        res = super(MasterTargetMargin, self).write(vals)
        self.check_all_series()
        return res
    
    def unlink(self):
        for record in self:
            if record.state in ['active', 'expired', 'rejected']:
                raise ValidationError(_("You cannot delete a Master Target Margin record that is in 'Active', 'Expired', or 'Rejected' state."))
        return super().unlink()


    def get_formview_action(self, access_uid=None):
        """ Override this method to add access control for user form view """
        user = self.env.user
        if access_uid:
            user = self.env['res.users'].browse(access_uid).sudo()
        if not user.has_group('tw_incentive.group_tw_master_target_margin_read'):
            raise AccessError(_("You do not have access to this document."))
            
        res = super().get_formview_action(access_uid=access_uid)
        return res
        
    # 13: action methods
    def action_confirm(self):
        is_need_approval = False
        #cari master yg aktif
        master = self.suspend_security().search([
            ('company_id', '=', self.company_id.id),
            ('job', '=', self.job),
            ('state', '=', 'active')], limit=1)
        if master:
            # Cari line yg masih aktif, jika ada sisa margin yg lebih kecil, maka tidak auto approve
            for new_line in self.target_margin_line_ids:
                master_line = self.env['tw.master.target.margin.line'].sudo().search([
                    ('target_margin_id', '=', master.id),
                    ('series_id', '=', new_line.series_id.id),
                    ('year', '=', new_line.year)], limit=1)

                # jika ada target margin yang berkurang dari sebelumnya maka incentive tidak langsung aktif (perlu approval)
                if (master_line.cash > new_line.cash or master_line.credit > new_line.credit):
                    is_need_approval = True
                    continue
        
        if not is_need_approval:
            self.action_activate()
        else:
            self.action_rfa()

    def action_activate(self):
        self.deactivate_other_master()
        self.write({
            'state': 'active'
        })
    
    def deactivate_other_master(self):
        # deactivate old master
        master = self.sudo().search([('company_id', '=', self.company_id.id),
            ('job', '=', self.job),
            ('state', 'in', ['active', 'draft'])], limit=1)
        master.state = 'expired'

    def schedule_expired_margin(self):
        target_margin = self.sudo().search([('state', '=', 'active'), ('date', '!=', False)])
        for margin in target_margin:
            if date.today() > (margin.date + relativedelta(months=5)).date():
                margin.state = 'expired'

    def check_all_series(self):
        for master in self:
            if master.state != 'expired':
                #check create master margin tidak di semua series aktif
                create_series_ids = []
                for line in master.target_margin_line_ids:
                    create_series_ids.append(line.series_id.id)
                
                active_series = self.env['product.series'].sudo().search([('active', '=', True)])
                active_series_ids = active_series.ids
                missing_series_ids = set(create_series_ids).difference(set(active_series_ids))
                if missing_series_ids:
                    missing_series = active_series.filtered(lambda s: s.id in missing_series_ids)
                    missing_names = ", ".join(missing_series.mapped("name"))
                    raise ValidationError(_(
                        "Pembuatan Master Target Margin tidak lengkap.\n\n"
                        "Series aktif berikut belum dibuatkan target margin:\n"
                        "- %s\n\n"
                        "Harap buat semua series aktif."
                    ) % missing_names)

    # 14: private methods
