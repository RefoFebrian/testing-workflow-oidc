# -*- coding: utf-8 -*-

# 1: imports of python lib
import random

# 2: import of known third party lib
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError, UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


STATES = [
    ('draft', 'Draft'),
    ('active', 'Active'),
    ('expired', 'Expired')
]


class MasterIncentive(models.Model):
    _name = "tw.master.incentive"
    _description = "Master Incentive"
    _order = "id desc"
    
    # 7: defaults methods
    def _get_default_date(self):
        return fields.Datetime.now()

    def _get_default_branch(self):
        if self.env.company.parent_id:
            return self.env.company.parent_id.id
        else:
            return self.env.company.id
        
    # 8: fields
    name = fields.Char()
    date = fields.Datetime('Datetime', default=_get_default_date)
    sales_category = fields.Selection(selection=lambda self: self.env['tw.selection'].get_option_list('IncentiveCategory'))
    branch_class = fields.Selection(selection=lambda self: self.env['tw.selection'].get_option_list('BranchClass'), default='-')
    state = fields.Selection(selection=STATES, default='draft', help="Whether the master incentive can be used or not")
    is_payroll = fields.Boolean()

    # 9: relation fields
    company_id = fields.Many2one(comodel_name='res.company', string="Branch", help="", default=_get_default_branch)
    incentive_line_ids = fields.One2many(comodel_name='tw.master.incentive.line', inverse_name="incentive_id", help="")

    # 10: constraints & sql constraints
    @api.constrains('incentive_line_ids')
    def _check_lines(self):
        if not self.incentive_line_ids:
            raise ValidationError(_("Master detail must not be empty!"))
        
    @api.constrains('sales_category', 'branch_class')
    def _check_sales_payroll_branch_class(self):
        if self.sales_category == 'sales_payroll' and self.branch_class == '-':
            raise ValidationError(_("Please assign a branch category when the sales category is set to 'Sales Payroll'."))
	
    # 11: compute/depends & on change methods
    @api.onchange('sales_category')
    def _onchange_job_id(self):
        if self.sales_category == 'sales_payroll':
            self.is_payroll = True
        else:
            self.is_payroll = False
            self.branch_class = '-'
            
    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            date = self._get_default_date()
            vals['name'] = "{}-{}".format(vals.get('sales_category'), date.strftime("%Y-%m-%d"))
            
        return super().create(vals_list)
    
    def unlink(self):
        for record in self:
            if record.state in ['active', 'expired']:
                raise Warning(_("You cannot delete master incentive that active or expired!."))
        return super().unlink()
    
    # 13: action methods
    def action_active(self):
        self.ensure_one()
        self.state = 'active'
        self._expire_old_master_incentive(self.sales_category, self.branch_class)
    
    def action_expire(self):
        self.state = 'expired'

    def get_incentive_line(self, quantity):
        """
        Get the incentive line based on the quantity.
        :param quantity: The quantity to check against the incentive lines.
        :return: The incentive line that matches the quantity, or None if no match is found.
        """
        return self.incentive_line_ids.filtered(lambda l: l.quantity == quantity)

    # 14: private methods
    def _expire_old_master_incentive(self, sales_category, branch_class):
        date = self._get_default_date()
        domain = [
            ('sales_category', '=', sales_category),
            ('date', '<', date),
            ('state', '=', 'active'),
            ('id', '!=', self.id)  # Ensure we don't expire the current record
        ]
        if sales_category == 'sales_payroll':
            domain.append(('branch_class', '=', branch_class))
                
        masters = self.search(domain)
        if masters:
            masters.action_expire()

    # TODO: remove this method if incentive testing is done
    def random_name(self):
        first_names = ["Luke","Leia","Han","Chewbacca","Obi-Wan","Anakin","Padmé","Darth","Palpatine","Yoda","Mace","Qui-Gon","Count","Maul","Ahsoka","Ezra","Sabine","Hera","Kanan","Jyn","Cassian","Galen","Saw","Lando","Boba","Jango","Rey","Finn","Poe","Kylo"]
        mid_names = ["Luffy","Zoro","Nami","Usopp","Sanji","Chopper","Robin","Franky","Brook","Jinbe","Shanks","Buggy","Mihawk","Crocodile","Doflamingo","Kaido","Big Mom","Whitebeard","Blackbeard","Ace","Sabo","Dragon","Garp","Smoker","Tashigi","Hancock","Fujitora","Kizaru","Akainu","Aokiji"]
        last_names = ["Hendrix","Clapton","Page","Van Halen","Vaughan","King","Santana","Berry","Beck","Atkins","Montgomery","Reinhardt","Gilmour","Allman","Townshend","Young","Vai","Malmsteen","Knopfler","May","Slash","Harrison","Iommi","Blackmore","Guy","Morello","Darrell","Cobain","Hetfield","Green"]

        random_first = random.choice(first_names)
        random_mid = random.choice(mid_names)
        random_last = random.choice(last_names)

        return f"{random_first} {random_mid} {random_last}"
    
    def get_available_unit(self, company_id, location_id=False, is_include_sublocations=True, usage='internal', lot_state='stock', include_reserved=False, location_dest_id=False, idx=0):
        domain = [('company_id', '=', company_id), ('quantity', '=', 1), ('reserved_quantity', '=', 0)]
        if location_id:
            if is_include_sublocations:
                stock_location = self.env['stock.location'].search([('location_id', 'child_of', location_id)])
            else:
                stock_location = self.env['stock.location'].search([('id', '=', location_id)])
        else:
            stock_location = self.env['stock.location'].search([
                ('usage', '=', usage),
                '|', ('company_id', '=', company_id), ('company_id', '=', False)
            ])

        if location_dest_id:
            domain.append(('location_id', '!=', location_dest_id))

        domain.append(('location_id', 'in', stock_location.ids))

        if not include_reserved:
            domain.append(('reservation_ids', '=', False))
            domain.append(('reserved_quantity', '=', 0))

        lot_ids = self.env['stock.lot']
        quants = self.env['stock.quant'].search(domain)
        if quants:
            avb_quant = quants.filtered(lambda q: q.lot_id.state == lot_state or not q.lot_id)
            lot_ids += avb_quant.lot_id
        
        product_ids = list(set({lot.product_id for lot in lot_ids}))
        return product_ids[idx % len(product_ids)]
    
    def create_mock_leads(self, branch_code, lead, count=10):
        branch = self.env['res.company'].search([('code', '=', branch_code)])
        salesmen = self.env['hr.employee'].search([
            ('company_id', '=', branch.id),
            ('job_id.sales_force_id.value', 'in', ('salesman', 'sales_counter', 'sales_partner', 'sales_coordinator', 'sales_operation_head'))
        ])
        
        for sales in salesmen:
            for i in range(count):
                product_id = self.get_available_unit(branch.id, idx=i)
                default = {
                    'name': self.env['ir.sequence'].get_sequence_code('LEADS', branch.code),
                    'identification_number': str(random.randint(1000000000000000, 9999999999999999)),
                    'mobile': f"+62 {str(random.randint(100, 999))} {str(random.randint(1000, 9999))} {str(random.randint(1000, 9999))}",
                    'customer_name': self.random_name(),
                    'company_id': branch.id,
                    'sales_id': sales.id,
                    'state': 'approved',
                    'product_id': product_id.id,
                    'date': datetime.today().replace(day=1) + relativedelta(days=i) if lead.date else False,
                    'down_payment_date': datetime.today() + relativedelta(days=i) if lead.down_payment_date else False,
                    'due_date': datetime.today() + relativedelta(days=i) if lead.due_date else False,
                    'last_state_date': datetime.today() + relativedelta(days=i) if lead.last_state_date else False,
                }
                lead.copy(default)

    def create_mock_spk(self, branch_code, limit=50):
        leads = self.env['tw.lead'].search([('state', '=', 'approved'), ('company_id.code', '=', branch_code)], limit=limit)
        if not leads:
            raise Warning(_("No leads found to create SPK."))

        for lead in leads:
            lead.action_create_spk()

    def create_mock_dso(self, branch_code, limit=10):
        spks = self.env['tw.dealer.spk'].search([('state', '=', 'progress'), ('company_id.code', '=', branch_code)], limit=limit)
        for spk in spks:
            try:
                spk.action_create_so()
            except Exception as e:
                print(f"Failed to create DSO for SPK {spk.name}: {e}")

    def create_mock_leads_to_dso(self, branch_code, count=30):
        eg_lead = self.env['tw.lead'].browse(1)
        self.create_mock_leads(branch_code, eg_lead, count)
        self.create_mock_spk(branch_code)
        spks = self.env['tw.dealer.spk'].search([('state', '=', 'draft'), ('company_id.code', '=', branch_code)])
        for spk in spks:
            spk.write({'state': 'sale'})
        self.create_mock_dso(branch_code)
        dsos = self.env['tw.dealer.sale.order'].search([('state', '=', 'draft'), ('company_id.code', '=', branch_code)])
        for dso in dsos:
            dso.write({'state': 'sale'})
        
    def create_mock_stock(self, lot_id, product_product, copy_count=10):
        lot = self.env['stock.lot'].browse(lot_id)
        
        for count in range(copy_count):
            quants = []
            
            product_tmpl_id = product_product.product_tmpl_id.id
            product_id = product_product.id
            for q in lot.quant_ids:
                q_record = q.read()[0]
                q_record.update({
                    'product_id': product_id,
                    'product_tmpl_id': product_tmpl_id,
                    'product_uom_id': q_record['product_uom_id'][0] if q_record.get('product_uom_id') else False,
                    'company_id': q_record['company_id'][0] if q_record.get('company_id') else False,
                    'location_id': q_record['location_id'][0] if q_record.get('location_id') else False,
                    'warehouse_id': q_record['warehouse_id'][0] if q_record.get('warehouse_id') else False,
                    'storage_category_id': q_record['storage_category_id'][0] if q_record.get('storage_category_id') else False,
                    'lot_id': q_record['lot_id'][0] if q_record.get('lot_id') else False,
                    'package_id': q_record['package_id'][0] if q_record.get('package_id') else False,
                    'owner_id': q_record['owner_id'][0] if q_record.get('owner_id') else False,
                    'product_categ_id': q_record['product_categ_id'][0] if q_record.get('product_categ_id') else False,
                    'user_id': q_record['user_id'][0] if q_record.get('user_id') else False,
                    'currency_id': q_record['currency_id'][0] if q_record.get('currency_id') else False,
                })
                quants.append([0, 0, q_record])
            lot.copy({
                'name': self.random_serial(),
                'state': 'stock',
                'product_id': product_id,
                'quant_ids': quants
            })

    def random_serial(self):
        import random
        import string

        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

