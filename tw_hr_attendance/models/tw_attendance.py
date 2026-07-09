# 1: imports of python lib
from datetime import timedelta, datetime, date
from dateutil.relativedelta import relativedelta
from math import radians, sin, cos, acos
import calendar
import requests
import json
import logging
_logger = logging.getLogger(__name__)
# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class Attendance(models.Model):
    _name = "tw.attendance"
    _description = "Absensi"
    _rec_name = "employee_id"

    # 7: defaults methods
    def _get_max_distance(self):
        return 500

    def _get_default_employee(self):
        self.env.user.employee_id.id

    def _get_default_datetime(self):
        return datetime.now()
    
    def _get_default_date(self):
        return self.env['res.company'].get_default_date()

    # 8: fields
    date = fields.Date('date',default=_get_default_date)
    check_in = fields.Datetime('Check In Time')
    check_out = fields.Datetime('Check Out Time')
    radius_in = fields.Float('Radius In')
    radius_out = fields.Float('Radius Out')
    lat_in = fields.Char('Latitude In')
    long_in = fields.Char('Longitude In')
    lat_out = fields.Char('Latitude Out')
    long_out = fields.Char('Longitude Out')
    work_hours = fields.Char('Work Hours')
    work_mins = fields.Char('Work Minutes')
    work_secs = fields.Char('Work Seconds')

    # 9: relation fields
    employee_id = fields.Many2one('hr.employee', 'Name', default=_get_default_employee)
    workplace_in_id = fields.Many2one('res.company', string="Workplace In")
    workplace_out_id = fields.Many2one('res.company', string="Workplace Out")
 
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_attendance_tree(self):
        domain = []
        name = "Absensi"
        path = 'attendance'
        list_view_id = self.env.ref('tw_hr_attendance.tw_attendance_list_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'path': path,
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.attendance',
            'domain': domain,
            'views': [(list_view_id, 'list'), (False, 'form')],
        }

    def get_work_hours(self, leave_time):
        start_hour = self.check_in.strftime('%H:%M:%S')
        start_mins = int(start_hour[3:5])
        start_secs = int(start_hour[6:8])
        start_hour = int(start_hour[0:2])
        total_work_hour = leave_time - timedelta(hours=start_hour,minutes=start_mins,seconds=start_secs)
        work_mins = total_work_hour.strftime('%H:%M:%S')[3:5]
        work_secs = total_work_hour.strftime('%H:%M:%S')[6:8]
        work_hours = total_work_hour.strftime('%H:%M:%S')[0:2]
        return {
            'work_hours': work_hours,
            'work_mins': work_mins,
            'work_secs': work_secs
        }
    
    def work_place(self, employee_id, lat, long):
        """
        Calculate if user is within workplace radius
        Returns workplace dict {'id': id, 'radius': radius} or False
        """
        max_distance = self._get_max_distance()
        
        # Get employee's company/workplace
        employee = self.env['hr.employee'].sudo().browse(employee_id)
        if not employee:
            return False
        
        # Get all possible workplaces for the employee
        branch_obj = self.env['res.company'].sudo().search([('id','=',employee.company_id.id)])
        
        for branch in branch_obj:
            # Check if workplace has lat/long coordinates
            if not branch.lat or not branch.long:
                continue
            
            wp_lat = branch.lat
            wp_long = branch.long
            
            # Calculate distance using haversine formula
            distance = self._calculate_distance(lat, long, wp_lat, wp_long)
            
            # Check if within radius (use max_distance as default radius)
            radius = max_distance
            if distance <= radius:
                return {
                    'id': branch.id,
                    'radius': radius
                }
        
        return False
    
    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate distance between two points using haversine formula
        Returns distance in meters
        """
        # Convert to radians
        lat1_rad = radians(float(lat1))
        lat2_rad = radians(float(lat2))
        lon1_rad = radians(float(lon1))
        lon2_rad = radians(float(lon2))
        
        # Earth radius in meters
        earth_radius = 6371000
        
        # Haversine formula
        distance = earth_radius * acos(
            sin(lat1_rad) * sin(lat2_rad) + 
            cos(lat1_rad) * cos(lat2_rad) * cos(lon2_rad - lon1_rad)
        )
        
        return distance

