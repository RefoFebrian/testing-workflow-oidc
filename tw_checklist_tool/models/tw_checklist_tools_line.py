# 1: imports of python lib
import calendar
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, _, api
from odoo.exceptions import UserError


# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwChecklistToolsLine(models.Model):
    _name = "tw.checklist.tools.line"
    _description = "Checklist Tools Line"

    # 7: defaults methods
    def get_month_selection(self):
        return [(str(i), _(calendar.month_name[i])) for i in range(1, 13)]

    def get_4week_boundaries(self, year, month):
        """
        Returns a list of four (start_day, end_day) tuples for the
        given year/month. The fourth tuple always ends on the month's last day.
        """
        cal = calendar.Calendar(firstweekday=calendar.MONDAY)
        weeks = cal.monthdayscalendar(year, month)
        # Weeks 1–3: take first three calendar rows (dropping zeros)
        boundaries = []
        for wk in weeks[:3]:
            days = [d for d in wk if d != 0]
            boundaries.append((min(days), max(days)))
        # Week 4: everything else
        rem = []
        for wk in weeks[3:]:
            rem += [d for d in wk if d != 0]
        boundaries.append((min(rem), max(rem)))
        return boundaries

    # 8: fields
    date = fields.Date('Date')
    week = fields.Char('Week')
    periode_bulan = fields.Selection(selection=get_month_selection, string='Month')
    tahun = fields.Char('Tahun')

    # 9: relation fields
    checklist_detail_ids = fields.One2many('tw.checklist.tools.detail', 'line_checklist_id', string='Detail Activity Checklist')
    checklist_id = fields.Many2one('tw.checklist.tools', string='Checklist Id', ondelete='cascade')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_submit(self):
        self.ensure_one()
        date_now = (datetime.now() + relativedelta(hours=7)).strftime("%Y-%m-%d")
        conv_date = datetime.strptime(date_now, '%Y-%m-%d').date()
        if self.date:
            if self.date != conv_date:
                raise UserError(
                    "Tidak Dapat Checklist Tool Di Tanggal Yang berbeda Dari Tanggal Sekarang (%s)" % (date_now))

        if self.week:
            current_month = conv_date.month
            if self.periode_bulan != str(current_month):
                raise UserError(
                    "Tidak Dapat Checklist Tool. Harus berada di periode bulan saat ini (%s)." % current_month)

            year = int(self.tahun)
            month = int(self.periode_bulan)
            week_bound = self.get_4week_boundaries(year, month)
            week_num = int(self.week)
            start_day, end_day = week_bound[week_num - 1]

            if not (start_day <= conv_date.day <= end_day):
                raise UserError(
                    "Checklist untuk minggu %s harus di antara hari %s dan %s pada bulan ini."
                    % (week_num, start_day, end_day)
                )

        form_id = self.env.ref('tw_checklist_tool.view_tw_checklist_tools_line_detail_form').id

        record = self.env['tw.checklist.tools.line'].browse(self.id)
        if not record.exists():
            return

        return {
            'type': 'ir.actions.act_window',
            'name': 'Detail Checklist Tools',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tw.checklist.tools.line',
            'view_id': form_id,
            'res_id': self.id,
            'target': 'new',
            'context': {'readonly_by_pass': 1, 'from_submit': True},
        }

    def action_save(self):
        self.ensure_one()
        detail = self.checklist_detail_ids
        for data in detail:
            if not data.tools_state:
                raise UserError("Perhatian!\nTerdapat detail kondisi tool yang belum diisi")
        return True

    # 14: private methods