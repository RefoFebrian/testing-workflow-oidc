# -*- coding: utf-8 -*-

# 1: imports of python lib
import ast

# 2: import of known third party lib
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError, UserError as Warning
from odoo.tools import SQL

# 5: local imports
import logging

# 6: Import of unknown third party lib


_logger = logging.getLogger(__name__)

STATES = [
    ('pending', 'Pending'),
    ('earned', 'Earned'),
    ('rejected', 'Rejected'),
    ('cancelled', 'Cancelled'),
    ('expired', 'Expired')
]


class EmployeeIncentive(models.Model):
    _name = "tw.employee.incentive"
    _description = "Employee Incentive"
    _order = "id desc"
    
    # 7: defaults methods
    def _get_default_date(self):
        return date.today()

    # 8: fields
    name = fields.Char(string="Name", help="Unique number of the incentive document.")
    type = fields.Selection(selection=[('sale', 'Sale'), ('other', 'Other'), ('trainee', 'Pembinaan'), ('reward', 'Reward')],
                            string="Type", help="Type of incentive, e.g., Sale, Other, Pembinaan (Trainee), or Reward.")
    state = fields.Selection(selection=STATES, string="State", help="Current state of the incentive (Pending, Earned, Rejected, Cancelled, Expired).")
    date = fields.Date(string="Date", help="Date when the incentive was created.")
    earned_date = fields.Date(string="Earned Date", help="Date when the incentive was earned.")
    model_id = fields.Integer(string="Model", help="ID of the related business model (e.g., sale order).")
    model_name = fields.Char(string="Model name", help="Technical name of the related business model.")
    transaction_ref = fields.Char(string="Transaction", help="Reference to the related transaction (e.g., sale order number).", index="trigram")
    incentive_value = fields.Float(string="Incentive value", compute='_compute_total_incentive', store=True,
                                   help="Total value of the incentive.")
    incentive_available = fields.Float(string="Incentive available", compute='_compute_total_incentive', store=True,
                                   help="Amount of incentive currently available for the employee.")
    incentive_outgoing = fields.Float(string="Incentive outgoing", compute='_compute_total_incentive', store=True,
                                   help="Amount of incentive that has been used or is outgoing.")
    remarks = fields.Char(string="Remarks", help="Additional remarks or notes about the incentive.")
    incentive_sales = fields.Float(help="Amount of incentive earned from total sales.")
    incentive_credit = fields.Float(help="Amount of incentive earned from credit sales.")
    incentive_reward = fields.Float(help="Amount of incentive earned as a reward.")

    # 9: relation fields
    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Branch",
        help="Branch or company associated with this incentive."
    )
    master_margin_id = fields.Many2one(
        comodel_name='tw.master.target.margin',
        string="Master Target Margin",
        help="Reference to the master target margin used for this incentive."
    )
    master_incentive_id = fields.Many2one(
        comodel_name='tw.master.incentive',
        string="Master Incentive",
        help="Reference to the master incentive used for this calculation."
    )
    job_id = fields.Many2one(
        comodel_name='hr.job',
        help="Job assigned to the employee at the time of the incentive transaction."
    )
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string="Salesman",
        index=True,
        help="Employee (salesman) who receives the incentive."
    )
    order_line_id = fields.Many2one(
        comodel_name='tw.dealer.sale.order.line',
        string="Order Line",
        index=True,
        help="Order line that is related to the incentive."
    )
    incentive_detail_ids = fields.One2many(
        comodel_name='tw.employee.incentive.detail',
        inverse_name='employee_incentive_id',
        string="Incentive Detail",
        help="Incentive detail records related to this employee incentive."
    )
    incentive_history_ids = fields.One2many(
        comodel_name='tw.employee.incentive.history',
        inverse_name='employee_incentive_id',
        string="Incentive History",
        help="History records related to this employee incentive."
    )
    recalculate_id = fields.Many2one(
        comodel_name='tw.recalculate.incentive',
        string='Recalculate',
        help="Attached Recalculate Incentive number if this incentive is recalculated"
    )

    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    
    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            branch = self.env['res.company'].browse(vals.get('company_id'))
            ref = self.env['ir.sequence'].get_sequence_code('INS', branch.code)
            vals['name'] = ref
            vals['incentive_available'] = vals.get('incentive_value')
            if vals.get('state') == 'earned':
                vals['earned_date'] = self._get_default_date()
        return super().create(vals_list)
    
    def write(self, vals):
        if vals.get('state') == 'earned':
            vals['earned_date'] = self._get_default_date()
        write = super().write(vals)
        return write
    
    def unlink(self):
        for record in self:
            raise Warning(_("You cannot delete an incentive that is already created!."))
        return super().unlink()
    
    # 13: action methods
    # cek dso > cek margin salesman > cek margin koordinator
    def check_incentive(self, limit=20, additional_search_param=[], raise_warning=False):
        search_param = [('incentive_state', '=', 'draft'), ('state', 'in', ['sale', 'done']), ('sales_id', '!=', False)]
        orders = self.env['tw.dealer.sale.order'].sudo().search(search_param + additional_search_param, order="date_order", limit=limit)
        if orders:
            for order in orders:
                salesman = order.sales_id
                for line in order.order_line.filtered(lambda l: l.incentive_state != 'done' and l.item_type == 'main'):
                    try:
                        is_incentive_calculated = False
                        if salesman.job_id.sales_category:
                            self.calculate_incentive(salesman, line)
                            is_incentive_calculated = True
                        if order.sales_coordinator_id and order.sales_coordinator_id.job_id.sales_category:
                            if (salesman.job_id.sales_category != 'sales_coordinator' and salesman != order.sales_coordinator_id):
                                self.calculate_incentive(order.sales_coordinator_id, line)
                                is_incentive_calculated = True

                        if not is_incentive_calculated:
                            line.incentive_state = 'skip'
                            order.incentive_state = 'skip'
                            order.error_message = _("Skipped. No incentive calculated for this line.")
                    except Warning as e:
                        _logger.warning("Failed to calculate incentive : %s"%str(e))
                        if raise_warning:
                            raise Warning(_(str(e)))
                        else:
                            order.error_message = _(str(e))
                            order.incentive_state = 'error'
                            line.incentive_state = 'error'
                            continue

        else:
            _logger.info(_("Scheduller Check Incentive : Dealer Sales Order with incentive state 'draft' is not found!"))

    # cek master incentive > cari line == qty > hitung incentive credit > cash > reward > create incentive
    def calculate_incentive(self, salesman, order_line):
        order = order_line.order_id
        master_margin = self.check_margin(salesman, order.date_order, order_line)
        
        order.incentive_state = 'done'
        order_line.incentive_state = 'done'
        
        sales_category = self._get_sales_job_categ(salesman, order.date_order)
        master_incentive = self._get_master_incentive(sales_category, order)
            
        if not master_incentive and sales_category != 'sales_team_leader':
            raise Warning(_(f"No master incentive found for Branch '{order.company_id.name}' and '{sales_category}' sales category."))
        
        # Initialize variables for calculation
        incentive_component = salesman.calculate_incentive(sales_category, order.date_order, master_incentive, order_line)
        incentive = incentive_component.pop('incentive', 0)
        incentive_detail_line = self._prepare_incentive_detail(incentive_component)
        
        if incentive:
            self.create_incentive_record(order_line, salesman, master_margin, incentive, master_incentive, incentive_detail_line)

    def create_incentive_record(self, order_line, salesman, master_margin, incentive, master_incentive, incentive_detail_line):
        state = 'pending'
        order = order_line.order_id
        order_date = datetime.combine(order.date_order, datetime.min.time())
        sales_record = self.env['tw.employee.career.record'].get_career_record_by_date(salesman.id, order_date, 'role')
        job_id = self.env['hr.job'].browse(sales_record.curr_id) or salesman.job_id
        
        if order.state == 'done' or job_id.sales_category == 'sales_partner':
            state = 'earned'
        
        vals = {
            'company_id': salesman.company_id.id,
            'type': 'sale',
            'date': order.date_order,
            'state': state,
            'model_id': order.id,
            'model_name': 'tw.dealer.sale.order',
            'transaction_ref': order.name,
            'order_line_id': order_line.id,
            'incentive_value': incentive,
            'employee_id': salesman.id,
            # TODO: in previous version master_margin for sales coordinator is not used,
            # would be better if we have can switch to use master_margin for sales coordinator
            # but for now we just use master_margin for sales counter and sales partner
            'master_margin_id': master_margin.target_margin_id.id if master_margin else False,
            'master_incentive_id': master_incentive.id,
            'job_id': job_id.id,
            'incentive_detail_ids': incentive_detail_line
        }
        
        self.env['tw.employee.incentive'].sudo().create(vals)
 
    # perhitungan sisa margin > cek target margin > komparasi margin > hitung incentive
    def check_margin(self, salesman, date_order, line):
        job_type = self._get_job_type_for_margin(salesman, date_order)
        if not job_type:
            raise Warning(_(f"Cannot determine margin calculation type for salesman '{salesman.name}' (job: '{salesman.job_id.name}'). "
                            "Please ensure the job category is correctly set for margin calculation."))
        
        margin_series, net_margin, target_margin = line.get_margin_values(salesman, job_type)
        if salesman.job_id.sales_category in ('sales_coordinator', 'sales_team_leader'):
            # NOTE: check_margin will be enabled when operation called to activate it based on task TSK/2024/04/03103
            line.achieve_coordinator_target = net_margin > target_margin
            line.target_margin_coordinator_id = margin_series.id
            # TODO: do this validation in pbt module
            # line.achieve_coordinator_target = target_achieved if salesman.job_id.is_pbt else True
        elif salesman.job_id.sales_category in ('sales_counter', 'sales_partner', 'sales_payroll', 'sales_digital'):
            line.achieve_salesman_target = net_margin > target_margin
            line.target_margin_sales_id = margin_series.id
            # TODO: do this validation in pbt module
            # line.achieve_coordinator_target = target_achieved if salesman.job_id.is_pbt else True
        else:
            # For other job categories, we do not set target achievement
            raise Warning(_("Salesman job category '%s' is not supported for margin calculation." % salesman.job_id.sales_category))
            
        return margin_series
    
    def get_previous_incetive_detail(self, employee_id, name, model_name=None):
        domain = [('employee_id', '=', employee_id), ('state', 'in', ['pending', 'earned'])]
        if model_name:
            domain.append(('model_name', '=', model_name))

        incentive = self.search(domain)
        details = incentive.incentive_detail_ids.filtered(lambda l: l.name == name)

        return max([detail.value for detail in details]) if details else 0.0
      
    # 14: private methods
    def _get_sales_job_categ(self, salesman, date):
        order_date = datetime.combine(date, datetime.min.time())
        sales_record = salesman.get_employee_career_record(order_date, 'role')
        job_id = self.env['hr.job'].browse(sales_record.curr_id) or salesman.job_id
        return job_id.sales_category
    
    def _get_master_incentive(self, sales_category, order):
        domain = [
            ('sales_category', '=', sales_category),
            ('state', '=', 'active')
        ]
        if sales_category == 'sales_payroll':
            branch_class = order.company_id.branch_class
            if not branch_class:
                raise Warning(_(f"Branch {order.company_id.name} does not have any class yet."))
            
            domain.append(('branch_class', '=', branch_class))
        margin = self.env['tw.master.incentive'].sudo().search(domain, limit=1)
        return margin

    def _schedulle_redraft_incentive(self):
        """
        Redraft dealer sale orders with incentive state 'error'.
        This method updates the incentive state of these orders to 'draft'.
        """
        try:
            self._cr.execute(SQL("""
                UPDATE tw_dealer_sale_order
                SET incentive_state = 'draft',
                    error_message = NULL,
                    incentive_retry_count = incentive_retry_count + 1
                WHERE incentive_state = 'error' 
                AND incentive_retry_count < 3
            """))
        except Exception as e:
            _logger.error(f"Error redrafting dealer sale orders with incentive state 'error': {str(e)}")
    
    def _schedulle_settlement_incentive(self, limit=30):
        """
        Update the state of employee incentives to 'earned'
        for those that are pending and associated with completed dealer sale orders.
        """
        pending_incentive = self.search([('state', '=', 'pending')], limit=30, order='date ASC')
        if not pending_incentive:
            raise Warning(_("No pending incentive found!"))
        

        q_incentive_pending = SQL("""
            SELECT inc.id
            FROM tw_employee_incentive AS inc
            LEFT JOIN tw_dealer_sale_order AS dso ON inc.transaction_ref = dso.name
            LEFT JOIN stock_picking p ON p.dealer_sale_order_id = dso.id
            LEFT JOIN account_move am ON am.ref = dso.client_order_ref
                AND am.move_type IN ('out_invoice', 'out_refund')
                AND am.journal_id = (SELECT journal_dso_settlement_id FROM tw_account_setting)
            WHERE dso.state IN ('sale', 'done')
            AND inc.state = 'pending'
            AND am.payment_state = 'paid'
            AND p.state = 'done'
            LIMIT %s
        """, limit)
        
        query = SQL("""
            UPDATE tw_employee_incentive
            SET earned_date = NOW() - INTERVAL '7 Hours',
                state = 'earned'
            WHERE id IN (%s)
        """, q_incentive_pending)
        
        try:
            self._cr.execute(query)
        except Exception as e:
            _logger.error(f"Error updating employee incentives to 'earned': {str(e)}")

    def _schedulle_expire_incentive(self):
        """ 
        Update the state of employee incentives to 'expired'
        for those that are pending and have dso in draft state
        for more than 21 days.
        """
        q_incentive_pending = SQL("""
            SELECT inc.id
            FROM tw_dealer_sale_order AS dso
            JOIN tw_employee_incentive AS inc ON inc.transaction_ref = dso.name
            WHERE inc.state = 'pending'
                AND dso.state = 'draft'
                AND NOW()::DATE - (dso.date_order + INTERVAL '7 hours')::DATE > 21
            ORDER BY dso.date_order desc
        """)

        query = SQL("""
            UPDATE tw_employee_incentive
            SET state = 'expired'
            WHERE id IN (%s)
        """, q_incentive_pending)

        try:
            self._cr.execute(query)
        except Exception as e:
            _logger.error(f"Error updating employee incentives to 'expired': {str(e)}")
        
    def _schedulle_send_incentive_result_notification(self, employee_id=None):
        folmonth = (date.today() - relativedelta(months=1) + relativedelta(day=1))
        lomonth = (date.today() + relativedelta(day=1) - relativedelta(days=1))
        fomonth = (date.today() - relativedelta(day=1))

        kwargs = {
            'first_of_last_month': folmonth,
            'last_of_month': lomonth,
            'first_of_month': fomonth
        }

        query = """ 
            SELECT employee.id
                , employee.name AS name
                , branch.id AS company_id
                , COALESCE(SUM(incentive.incentive_value) FILTER(WHERE incentive.state = 'earned'
                    AND incentive.model_name = 'tw.dealer.sale.order'
                    AND incentive.date BETWEEN %(first_of_last_month)s AND %(last_of_month)s
                ),0) AS earned_incentive
                , COALESCE(SUM(incentive.incentive_value) FILTER(WHERE incentive.state = 'pending'
                    AND incentive.model_name = 'tw.dealer.sale.order'
                    AND incentive.date BETWEEN %(first_of_last_month)s AND %(last_of_month)s
                ),0) AS pending_in_incentive
                , COALESCE(SUM(incentive.incentive_value) FILTER(WHERE incentive.state = 'earned' 
                    AND incentive.model_name != 'tw.dealer.sale.order'
                    AND incentive.date BETWEEN %(first_of_month)s AND NOW()
                ),0) AS potongan
            FROM hr_employee employee
            JOIN tw_employee_incentive incentive ON employee.id = incentive.employee_id
            JOIN res_company branch ON branch.id = employee.company_id
        """

        if employee_id:
            query += " WHERE employee.id = %(employee_id)s"
            kwargs['employee_id'] = employee_id

        query += " GROUP BY employee.id, branch.id"
        self._cr.execute(SQL(query, **kwargs))
        ress = self._cr.dictfetchall()

        if ress:
            # Firebase
            to_create_notification_firebase = self._create_notification_firebase_content(ress)
            if to_create_notification_firebase:
                create_message_data= self.env['tw.firebase.notification'].sudo().create(to_create_notification_firebase)
                if create_message_data:
                    for message in create_message_data:
                        message_title = "Notifikasi Detail Insentive kepada " + (message.customer_name or '')
                        message_body  = "Cek Secara Berkala Terkait Insentivemu melalui Aplikasi doodool atau Situs Web Tunas Honda."
                        data = {
                            "priority" : "normal",
                            "notification" : {
                                "id" : message.id,
                                "body" : "%s"%(message_body),
                                "title" : "%s"%(message_title),
                                "icon" : "logo_sahabat_tunas",
                                "model" : "tw.firebase.notification",
                                "click_action": "com.matra.dwipa.tunas.hoking.firebase.page.DetailsNotifications"
                            },
                            "data" : {
                                "text" : "new Symulti update !"
                            }
                        }
                        obj_firebase_user = self.env['tw.firebase.user'].search([('user_id', '=', message.employee_receiver_id.user_id.id),
                                                                                 ('active', '=', True)])
                        if obj_firebase_user :
                            for token in obj_firebase_user:
                                try:
                                    obj_firebase_user.notify_single_device(token.firebase_token, data)
                                    message.write({'send_date':self._get_default_date(), 'state': 'unread'})
                                except Exception as e:
                                    _logger.error(e)

    def _create_notification_firebase_content(self, ress):
        month = datetime.strptime(str(date.today().month), "%m").strftime("%B") + ' ' + str(date.today().year)
        to_create_notification_firebase = []
        model_category = self.env['tw.firebase.notification.category'].suspend_security().search([('name', '=', 'Notification Incentive Bulanan')],limit=1)
        template = model_category.content_template_id
        if template:
            for data in ress:
                total_insentive = data.get('earned_incentive') + data.get('potongan')
                content_msg = template.content
                content_msg = content_msg.replace("%penerima%", str(data.get('name')))
                content_msg = content_msg.replace("%bulan%", str(month))
                content_msg = content_msg.replace("%earned%", f"{data.get('earned_incentive'):,.2f}")
                content_msg = content_msg.replace("%pending%", f"{data.get('pending_in_incentive'):,.2f}")
                content_msg = content_msg.replace("%potongan%", f"{data.get('potongan'):,.2f}")
                content_msg = content_msg.replace("%total%", f"{total_insentive:,.2f}")
                to_create_notification_firebase.append({
                    'name' : template.name + "["+str(data.get('id'))+"-"+str(data.get('company_id'))+"]",
                    'customer_name' : data.get('name'),
                    'message' : content_msg,
                    'company_id' : data.get('company_id'),
                    'employee_receiver_id': data.get('id'),
                    'category_id' : model_category.id,
                })
        return to_create_notification_firebase
    
    def _get_job_type_for_margin(self, salesman, date_order):
        """
        Determine the job type margin code for a given salesman and order date.

        Args:
            salesman: The salesman object for which to determine the job type.
            date_order: The date of the order to check the salesman's job at that time.

        Returns:
            str or None: The margin job type code ('sc', 'sco', or 'sales'), or None if not found.
        """
        # cek job tipe untuk mencari master margin
        job_type_margin = {
            'sales_counter': 'sc',
            'sales_coordinator': 'sco',
            'sales_team_leader': 'sco',
            'sales_partner': 'sales',
            'sales_payroll': 'sales',
            'sales_digital': 'sales'
        }
        job = salesman.get_job_by_order_date(date_order)
        job_type = job_type_margin.get(job.sales_category)
        if not job_type:
            job_type = job_type_margin.get(job.sales_force_id.value)
        return job_type
    
    def _prepare_incentive_detail(self, component):
        incentive_detail_line = []
        for key, value in component.items():
            incentive_detail_line.append(Command.create({'name': key.replace('_', ' ').title(), 'value': value}))

        return incentive_detail_line
        
    

class EmployeeIncentiveDetail(models.Model):
    _name = "tw.employee.incentive.detail"
    _description = "Employee Incentive Detail"
    _order = "id desc"

    # 7: defaults methods
    
    # 8: fields
    name = fields.Char(string='Name', help="Description of the incentive component")
    value = fields.Float(string='Value', help="Value of the incentive component")
    
    # 9: relation fields
    employee_incentive_id = fields.Many2one(
        comodel_name="tw.employee.incentive",
        string="Employee Incentive",
        ondelete='cascade',
        help="Reference to the related employee incentive."
    )

