# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date , timedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError, UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwLossDemaandReport(models.TransientModel):
    _name = "tw.loss.demand.report"
    _description = "Loss Demand Report"

    # 7: defaults methods
    def get_default_datetime(self):
        return datetime.now()
    
    def _get_default_branch(self):
        if self.env.company.parent_id:
            return self.env.company.id
        else:
            company_ids = self.env.companies.filtered(lambda x: x.parent_id)
            if company_ids:
                return company_ids[0].id
            
        raise Warning(_('Please choose another branch / company other than %s on the top right of the screen.'%self.env.company.name))
    
    # 8: fields
    name = fields.Char('Filename')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options(), default=lambda self: self.env.context.get('default_division'))
    start_date = fields.Date('Start Date', default=date.today())
    end_date = fields.Date('End Date', default=date.today())

    # 9: relation fields
    company_ids = fields.Many2many('res.company',"Branch", copy=False)

    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods

    # 12: override methods
    
    # 13: action methods
    def action_generate_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        start = datetime.combine(self.start_date, datetime.min.time()).strftime('%Y-%m-%d %H:%M:%S')
        end = datetime.combine(self.end_date, datetime.max.time()).strftime('%Y-%m-%d %H:%M:%S')
        query_where = f" WHERE a.create_date BETWEEN '{start}'::timestamp AND '{end}'::timestamp AND d.division = '{self.division}'"
        
        if self.company_ids:
            query_where += f" AND a.company_id IN ({', '.join(str(b.id) for b in self.company_ids)})"
        else:
            companies = self.env.user._get_company_ids()
            query_where += f" AND a.company_id IN {str(tuple(companies)).replace(',)', ')')}"

        query = f"""
            select
            b.code as "Branch Code"
            , b.name as "Branch Name"
            , d.name->>'en_US' as "Product Name"
            , c.default_code as "Product Code"
            , e.name as "Category"
            , f.name as "Customers"
            , f.mobile as "Mobile No."
            , a.qty as "Qty"
            from tw_loss_demand a
            left join res_company b on a.company_id = b.id
            left join product_product c on a.product_id = c.id
            left join product_template d on c.product_tmpl_id = d.id
            left join product_category e on d.categ_id = e.id
            left join res_partner f on a.partner_id = f.id
            {query_where}
            ORDER BY a.id, b.name
        """

        self._cr.execute(query)
        ress =  self._cr.dictfetchall()
        return self.env['web.report'].sudo().generate_report('Report Purchase Order',ress)

    # 14: private methods
    
    