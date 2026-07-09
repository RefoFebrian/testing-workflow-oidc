# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TWBoomTaskInherit(models.Model):
    _inherit = "tw.boom.task"

    is_last_reminder_escalation = fields.Boolean(string="Last Reminder Escalation?", default=False, help="This field is used as identity for this task if this TRUE that means this task had been given last reminder escalation after the maximum level of reminder escalation")



    def action_process_escalation(self):
        """
        Main entry point for BOOM escalation processing.
        This method scans for 'open' tasks and processes them based on master escalation settings.
        Supported Units:
        - Day (H): Adds days to due date.
        - Week (W): Adds weeks to due date.
        - Month (M): Adds months to due date.
        """
        today = date.today()
        tasks = self.search([
            ('state', '=', 'open'),
        ])
        
        # Group tasks by PIC to batch WA messages
        pic_level_map = {} # {PIC_Employee_ID: (escalation_name, config_record)}

        # Pre-fetch all escalation configs to minimize queries inside the loop
        all_configs = self.env['tw.boom.master.escalation'].sudo().search([])
        configs_by_category = {}
        
        for conf in all_configs:
            configs_by_category.setdefault(conf.category_id.id, []).append(conf)

        for task in tasks:
            if not task.category_id or not task.transaction_date:
                continue

            # Calculate Due Date: transaction_date + due_date_day
            due_date = task.transaction_date.date() + relativedelta(days=task.category_id.due_date_day)
            
            # Check applicable configs
            task_configs = configs_by_category.get(task.category_id.id, [])
            
            # Find the max overdue days defined for this category to determine if we are in "Catch-Up" mode
            max_config_days = 0
            for conf in task_configs:
                days = 0
                if conf.unit == 'day': days = conf.interval
                elif conf.unit == 'week': days = conf.interval * 7
                elif conf.unit == 'month': days = conf.interval * 30 # Approx
                
                if days > max_config_days:
                    max_config_days = days

            # Determine actual days overdue for comparison
            days_overdue = (today - due_date).days
            
            # CATCH-UP LOGIC:
            # Trigger ONLY if task is overdue beyond max config AND hasn't been flagged as 'Last Reminder' yet.
            is_catch_up_mode = days_overdue > max_config_days and not task.is_last_reminder_escalation

            for config in task_configs:
                # Calculate Target Date for this specific escalation rule
                target_date = False
                config_days = 0
                if config.unit == 'day':
                    target_date = due_date + relativedelta(days=config.interval)
                    config_days = config.interval
                elif config.unit == 'week':
                    target_date = due_date + relativedelta(weeks=config.interval)
                    config_days = config.interval * 7
                elif config.unit == 'month':
                    target_date = due_date + relativedelta(months=config.interval)
                    config_days = config.interval * 30 # Approx calculation just for logic check
                
                # Logic:
                # 1. Normal Mode: target_date == today
                # 2. Catch-Up Mode: is_catch_up_mode is True.
                
                should_trigger = False
                if target_date == today:
                    should_trigger = True
                elif is_catch_up_mode:
                    # In catch-up mode, we trigger everything. 
                    should_trigger = True
                
                if not should_trigger:
                    continue
                
                # Check if this task already has an escalation record for THIS level (by name) today
                # This prevents double sending even in catch-up mode (if run multiple times a day)
                existing_escalation = self.env['tw.boom.task.escalation'].sudo().search([
                    ('task_id', '=', task.id),
                    ('unit', '=', config.unit),
                    ('interval', '=', config.interval),
                    ('create_date', '>=', fields.Datetime.to_string(datetime.combine(today, datetime.min.time()))),
                    ('create_date', '<=', fields.Datetime.to_string(datetime.combine(today, datetime.max.time())))
                ], limit=1)

                if existing_escalation:
                    continue

                # Determine PIC
                pic_employee = self.env['hr.employee'].sudo().search([
                    ('job_id', '=', config.job_id.id),
                    ('company_id', '=', task.company_id.id),
                    ('working_end_date', '=', False),
                    ('active', '=', True)
                ], limit=1)

                if not pic_employee:
                    continue

                # Add to batch
                batch_key = (pic_employee.id, config.id)
                pic_level_map.setdefault(batch_key, []).append(task)
            
            # Mark as Last Reminder Escalation DONE if we were in catch-up mode
            if is_catch_up_mode:
                task.sudo().write({'is_last_reminder_escalation': True})

        # Process batches
        for (pic_id, config_id), tasks_to_notify in pic_level_map.items():
            config = self.env['tw.boom.master.escalation'].sudo().browse(config_id)
                
            self._notify_batch_escalation(pic_id, tasks_to_notify, config)

    def _notify_batch_escalation(self, pic_id, tasks, config):
        """
        Create escalation records and send a batched WA message.
        """
        pic = self.env['hr.employee'].sudo().browse(pic_id)
        pic_name = pic.name
        job_name = pic.job_id.name or config.job_id.name or ''
        
        # Build WA message
        template = self.env['tw.whatsapp.content.template'].sudo().search([
            ('name', '=', 'Escalation Boom') # Using the new template
        ], limit=1)
        
        if not template:
            # _logger.warning("WhatsApp Template 'Template BOOM Baru' not found!") # Assuming _logger is defined elsewhere
            # We still create the escalation records even if WA fails
            content = "Notification for overdue BOOM tasks."
        else:
            content = template.content

        # Build detail section
        detail_text = ""
        category_tasks = {}
        for t in tasks:
            main_cat = t.category_id.main_category_id.name or 'Other'
            category_tasks.setdefault(main_cat, []).append(t)

        for main_cat, cat_tasks in category_tasks.items():
            detail_text += f"\n*{main_cat}*\n"
            
            # Sub-group by sub-category for aggregation
            sub_cat_groups = {}
            for t in cat_tasks:
                sub_cat_groups.setdefault(t.category_id, []).append(t)
            
            for cat, tasks_in_sub in sub_cat_groups.items():
                if main_cat.lower() in ['ar', 'cash']:
                    # For AR/Cash, SUM the transaction values by Category
                    total_value = sum(t.transaction_value for t in tasks_in_sub)
                    detail_text += f"- {cat.name} Total: {self._format_rupiah(total_value)}\n"
                else:
                    # For others, show count
                    count = len(tasks_in_sub)
                    detail_text += f"- {cat.name} Total: {count}\n"

        # Replace placeholders
        greeting = self._get_greeting()
        msg = content.replace('[sapaan]', greeting)
        msg = msg.replace('[name]', pic_name)
        msg = msg.replace('[job_name]', f"({job_name})")
        msg = msg.replace('[dealer_name]', tasks[0].company_id.name or '')
        msg = msg.replace('[detail_transaksi]', detail_text)
        msg = msg.replace('[tgl_transaksi]', f"({date.today().strftime('%d/%m/%Y')})\n")
        msg = msg.replace('[footer]', "Mohon segera diselesaikan outstanding task-nya.")
        msg = msg.replace('[url]', '')

        # Create WHATSAPP record
        wa_vals = {
            'name': pic_name,
            'phone_number': pic.mobile_phone or pic.work_phone or '',
            'message': msg,
            'message_type': 'outbox',
            'origin': 'BOOM Escalation',
            'company_id': tasks[0].company_id.id,
            'template_id': template.id if template else False,
            'date': date.today(),
        }
        
        # Set scheduled time if defined in config AND enabled
        if config and config.is_send_message_scheduled and config.escalation_hour and config.escalation_minute:
            scheduled_dt = datetime.combine(date.today(), datetime.min.time()) + \
                           relativedelta(hours=int(config.escalation_hour), minutes=int(config.escalation_minute))
            
            scheduled_dt_utc = scheduled_dt - relativedelta(hours=7)
            wa_vals['scheduled_date'] = scheduled_dt_utc 

        # Create WHATSAPP record
        wa_id = False
        note_wa_error = ''
        if wa_vals.get('phone_number'):
            try:
                whatsapp_model = self.env['tw.whatsapp.message'].sudo()
                message_data = whatsapp_model._prepare_create_whatsapp_message([wa_vals])
                wa_msg = whatsapp_model.create(message_data)
                wa_id = wa_msg.id
            except Exception as e:
                # _logger.error(f"Failed to create start WA message: {str(e)}")
                note_wa_error = str(e)
        else:
            note_wa_error = 'PIC phone number not found'

        # Create Task Escalation Records
        ext_state = 'open' # Default state for escalation record
        for t in tasks:
            self.env['tw.boom.task.escalation'].sudo().create({
                'task_id': t.id,
                'interval': config.interval,
                'unit': config.unit,
                'pic_id': pic.id,
                'job_id': pic.job_id.id or config.job_id.id,
                'state': ext_state,
                'wa_id': wa_id,
                'note': note_wa_error,
            })
            # Update current_escalation in task
            t_level = ''
            if config.unit == 'day':
                t_level = f"H+{config.interval}"
            elif config.unit == 'week':
                t_level = f"W+{config.interval}"
            elif config.unit == 'month':
                t_level = f"M+{config.interval}"

            current_level = t.current_escalation.split('+')[1] if t.current_escalation and '+' in t.current_escalation else False
            if config.interval > int(current_level):
                t.sudo().write({'current_escalation': t_level})

    def _get_greeting(self):
        hour = datetime.now().hour + 7 # Simple UTC+7 adjustment for greeting
        if 5 <= hour < 11:
            return "Selamat Pagi"
        elif 11 <= hour < 15:
            return "Selamat Siang"
        elif 15 <= hour < 18:
            return "Selamat Sore"
        else:
            return "Selamat Malam"

    def _format_rupiah(self, value):
        try:
            val = int(value)
            return "Rp{:,.0f}".format(val).replace(',', '.')
        except:
            return str(value)