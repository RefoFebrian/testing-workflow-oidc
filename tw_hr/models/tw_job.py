from odoo import models, fields, api, _
from datetime import datetime


class TwHrJob(models.Model):
    _inherit = "hr.job"
    
    branch_control = fields.Selection(selection=[
        ('salesman','Salesman'),
        ('workshop','Workshop')
    ], string='Branch Control')

    job_category_id = fields.Many2one('tw.selection', string='Category', domain=[('type', '=', 'JobCategory')])
    job_level_id = fields.Many2one('tw.selection', string='Level', domain=[('type', '=', 'JobLevel')])
    sales_force_id = fields.Many2one('tw.selection', string='Sales Force', domain=[('type', '=', 'SalesForce')])
    is_sales_digital = fields.Boolean(string='Sales Digital', default=False,help="Digunakan untuk menandakan bahwa job ini adalah sales digital. Jika checked, maka akan akan mempengaruhi Visibilitas data Sales Digital")
    group_id = fields.Many2one('res.groups', string='Group')

    @api.model_create_multi
    def create(self, vals_list):
        jobs = super(TwHrJob, self).create(vals_list)
        if not self.env.context.get('import_file'):
            # Jika import banyak sekaligus, akan lemot sekali jika langsung sync group.
            # Somehow odoo mengcreate batch, lalu mencobanya 1 per 1 ulang.
            # Fitur auto create Group di handle dari Scheduller
            jobs.action_sync_res_groups()
        return jobs

    def action_sync_res_groups(self):
        """
        Batch synchronize res.groups for hr.job.
        1. Find/Create groups for each job in self.
        2. Assign users to the groups based on their job.
        """
        if not self:
            return

        # 1. Collect job names and check existing groups
        job_names = self.mapped('name')
        existing_groups = self.env['res.groups'].search([('name', 'in', job_names)])
        group_map = {group.name: group for group in existing_groups}

        # 2. Identify missing groups and batch create them
        missing_names = list(set(name for name in job_names if name not in group_map))
        if missing_names:
            category_id = self.env.ref('tw_base.tw_job').id
            vals_list = [{'name': name, 'category_id': category_id} for name in missing_names]
            new_groups = self.env['res.groups'].create(vals_list)
            for group in new_groups:
                group_map[group.name] = group

        # 3. Assign group_id to jobs
        for job in self:
            job.group_id = group_map.get(job.name)

        # 4. Sync employees: find all relevant employees and their users
        employees = self.env['hr.employee'].search([
            ('job_id', 'in', self.ids),
            ('user_id', '!=', False)
        ])
        
        # 5. Group users by the groups they need to be added to
        # This prevents redundant calls to user.write() if a user has multiple jobs (if possible in setup)
        user_to_groups = {}
        for emp in employees:
            user = emp.user_id
            group = emp.job_id.group_id
            if group and group not in user.groups_id:
                if user not in user_to_groups:
                    user_to_groups[user] = set()
                user_to_groups[user].add(group.id)

        # 6. Apply group updates to users
        for user, group_ids in user_to_groups.items():
            user.write({'groups_id': [fields.Command.link(gid) for gid in group_ids]})

    @api.model
    def scheduler_sync_res_groups(self):
        jobs = self.env['hr.job'].search([('active','=',True),('group_id', '=', False)])
        jobs.action_sync_res_groups()