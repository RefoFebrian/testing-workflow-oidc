# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools, Command
from odoo.tools.config import config
from odoo.addons.tw_db_config.models.config import DictCursor
from odoo.exceptions import UserError, ValidationError
from markupsafe import escape
import psycopg2

class DbConfig(models.Model):
    _name = "tw.db.config"
    _description = 'Config Database'

    name = fields.Char(string='Config Code')
    db_name = fields.Char(string='Database Name')
    host = fields.Char(string='Host')
    port = fields.Char(string='Port')
    user = fields.Char(string='User')
    password = fields.Char(string='Password')
            
    def get_db_conn(self):
        # Build the connection string
        conn_string = "host='{db_host}' port='{db_port}' user='{db_user}' password='{db_password}' dbname='{db_name}'".format(
        db_host = self.host, 
        db_port = self.port, 
        db_user = self.user, 
        db_password = self.password, 
        db_name = self.db_name, 
        )

        # Create the database connection
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor(cursor_factory=DictCursor)

        return cursor
        
    def execute(self, query, type='dictfetchall', with_cursor=False):
        
        # Avoid sql injection
        if " delete " in query.lower():
            raise ValidationError(_('Cant delete anything from this method!'))
        
        cr_db = self.get_db_conn()
        cr_db.execute(query)
        
        if type == 'dictfetchall':
            data = cr_db.dictfetchall()
        elif type == 'dictfetchone':
            data = cr_db.dictfetchone()
        elif type == 'fetchall':
            data = cr_db.fetchall()
        elif type == 'fetchone':
            data = cr_db.fetchone()
        else :
            data = cr_db.dictfetchall()
            
        if with_cursor:
            return data, cr_db
        return data

    def test_connection(self):
        try:
            self.execute("SELECT 1")
        except Exception as e:
            raise UserError(_("Koneksi Gagal :"+str(e)))
        
        message = 'Your connection with %s is successfully establish'%self.name
        raise ValidationError(_(message))

    def get_data(self):
        return 1
        
    
