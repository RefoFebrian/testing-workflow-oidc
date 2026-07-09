# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
import os
import pytz
import base64
import csv
import xlsxwriter
import calendar
from io import StringIO,BytesIO
from datetime import date, datetime, time

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib
class TwAuthOauthReport(models.TransientModel):
    _name = "tw.auth.oauth.report"
    _description = "Report Journal"

    def _get_default_date(self): 
        return datetime.now()
    
    name = fields.Char('File Name')    
    option = fields.Selection([
        ('user_active', 'User Active'),
        ('assign_local_passord', 'Assigned and Local Password'),
        ('only_assign', 'Only Assigned')
    ], string='Option')

    # 9: relation fields

    def action_download(self):
        return self._get_report()
    
    def _get_where_clause(self):
        query_where = "WHERE 1=1"
        
        # ? Option user_active get all active users
        query_where += " AND users.active = True"
        
        if self.option == 'assign_local_passord':
            query_where += " AND users.oauth_uid IS NOT NULL AND users.password IS NOT NULL"
        elif self.option == 'only_assign':
            query_where += " AND users.oauth_uid IS NOT NULL AND users.password IS NULL"
            
        return query_where

    def _get_report(self):
        query_where = self._get_where_clause()
 
        query = f"""
           SELECT
                rp.name,
                users.login,
                users.oauth_uid,
                (users.password IS NOT NULL) AS has_local_password,
                last_logins.last_login_date + interval '7 hours' AS last_login,
                last_logins.last_sso_date + interval '7 hours' AS last_login_sso
            FROM
                res_users users
            LEFT JOIN
                res_partner rp ON rp.id = users.partner_id
            LEFT JOIN
                (
                    SELECT
                        create_uid,
                        MAX(CASE WHEN type = 'normal' THEN create_date END) AS last_login_date,
                        MAX(CASE WHEN type = 'oauth'  THEN create_date END) AS last_sso_date
                    FROM
                        res_users_log
                    GROUP BY
                        create_uid
                ) AS last_logins ON last_logins.create_uid = users.id
            {query_where}
        """
        # ? Get Title 
        title = self._get_title()
        
        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        
        # ? Get Header
        summary_header = self._get_summary_header_data(title,ress)
        
        return self.env['web.report'].sudo().generate_report('Laporan User SSO Tunas',ress, data_summary_header=summary_header)
    
    def _get_summary_header_data(self,title,result):
        user_active = self.env['res.users'].suspend_security().search([('active','=',True)])
        
        if user_active:
            user_assigned_local_password = self._cr.execute(""" 
            SELECT COUNT(*) FROM res_users WHERE active = True AND oauth_uid IS NOT NULL AND password IS NOT NULL
            """)
            user_assigned_local_password = self._cr.dictfetchone()
            user_assigned_local_password = user_assigned_local_password.get('count',0)
            user_only_assigned = user_active.filtered(lambda x: x.oauth_uid and not x.password)
            user_active = len(user_active.ids)
            user_only_assigned = len(user_only_assigned.ids)
            user_not_assigned = user_active - user_assigned_local_password - user_only_assigned
    
        result = len(result)
        return {
            'B3': 'Summary',
            'C3': '',
            'B4':'User Active',
            'C4':user_active,
            'B5':'Data Assigned User SSO Tunas and Has Local Password',
            'C5':user_assigned_local_password,
            'B6':'Data Only Assigned User SSO Tunas',
            'C6':user_only_assigned,
            'B7':'Data User not Assigned',
            'C7': user_not_assigned
        }
        
    def _get_title(self):
        if self.option == 'user_active':
            return "Data User Active SSO Tunas"
        elif self.option == 'assign_local_passord':
            return "Data Assigned User SSO Tunas and Has Local Password Teds 2.0"
        elif self.option == 'only_assign':
            return "Data Only Assigned User SSO Tunas"