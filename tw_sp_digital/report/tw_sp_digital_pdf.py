# 1: imports of python lib
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class EmployeeSpDigitalPdf(models.AbstractModel):
    _name = "report.tw_sp_digital.sp_digital_pdf"
    _description = 'Report SP Digital PDF'

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    
    # 13: action methods
    def get_month_name(self, index):
        if index == '1':
            return 'Januari'
        elif index == '2':
            return 'Februari'
        elif index == '3':
            return 'Maret'
        elif index == '4':
            return 'April'
        elif index == '5':
            return 'Mei'
        elif index == '6':
            return 'Juni'
        elif index == '7':
            return 'Juli'
        elif index == '8':
            return 'Agustus'
        elif index == '9':
            return 'September'
        elif index == '10':
            return 'Oktober'
        elif index == '11':
            return 'November'
        elif index == '12':
            return 'Desember'

    # 14: private methods
    def _get_max_sp_type(self, sp_id):
        query = """
            SELECT type
            FROM tw_sp_digital_line
            WHERE sp_digital_id = %s
            ORDER BY sp_level DESC
            LIMIT 1
        """ % sp_id
        self._cr.execute(query)
        
        return self._cr.fetchone()[0]
    
    @api.model
    def _get_report_values(self, docids, data=None):
        sp_data = data['data']
        sp_digital_pdf_report = self.env['ir.actions.report']._get_report_from_name('tw_sp_digital.sp_digital_pdf')
        sp_digital_obj = self.env['tw.sp.digital'].suspend_security().search([
            ('id','=',data.get('id'))
        ], limit=1)
        sp_level_romawi = ''.join(['I' for x in range(int(sp_data['sp_level']))])
        fomonth = sp_digital_obj.date.replace(day=1).replace(month=int(sp_digital_obj.month)).replace(year=int(sp_digital_obj.year))
        fomonth_text = '1 ' + self.get_month_name(sp_digital_obj.month) + ' ' + sp_digital_obj.year
        six_month_latter = fomonth + relativedelta(months=6) - relativedelta(days=1)
        six_month_latter_text = str(six_month_latter.day) + ' ' + self.get_month_name(str(six_month_latter.month)) + ' ' + str(six_month_latter.year)
        biggest_sp = self.env['tw.sp.digital.line'].sudo().search([
            ('sp_digital_id','=',data.get('id')),
            ('type','in',('indisipliner','performance'))
        ], order='sp_level DESC', limit=1)

        return {
            'doc_ids': self.ids,
            'doc_model': sp_digital_pdf_report.model,
            'docs': data['data'],
            'sp_obj': sp_digital_obj,
            'sp_level_romawi': sp_level_romawi,
            'Date': fields.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'fomonth': fomonth_text,
            'six_month_latter': six_month_latter_text,
            'biggest_sp': biggest_sp
        }