from logging import warning
from odoo import models, fields, api, Command
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError as Warning
import base64
import xlrd
import xlsxwriter
from io import BytesIO


class ResGroupWizard(models.TransientModel):
    _name = "tw.res.groups.wizard"
    _description = "Res Groups Wizard"

    group_id = fields.Many2one('res.groups','Groups')
    file = fields.Binary('Upload Access')

    name = fields.Char(string='Name')
    report_file = fields.Binary('File', readonly=True)


    wbf = {}

    def action_upload(self):
        data = base64.decodebytes(self.file)
        excel = xlrd.open_workbook(file_contents = data)  
        sh = excel.sheet_by_index(0)  
        ids = []
        warning = ""

        for rx in range(1,sh.nrows):  
            group_name = [sh.cell(rx, ry).value for ry in range(sh.ncols)] [0]
            group_obj = self.group_id.sudo().search([
                ('name','=',str(group_name.strip()))
            ])
            
            if not group_obj:
                warning += "Untuk Access %s Pada Baris %s Tidak Ada.\n"%(group_name, rx)
            else:
                ids.append(group_obj.id)
        
        if warning:
            raise Warning(warning)

        write = self.group_id.sudo().write({
            'implied_ids': [Command.link(g_id) for g_id in ids],
        })

    
    def _add_workbook_format(self,workbook):      
        self.wbf['header'] = workbook.add_format({'bold': 1,'align': 'center','bg_color': '#FFFFDB','font_color': '#000000'})
        self.wbf['header'].set_border()

        self.wbf['footer'] = workbook.add_format({'align':'left'})

        self.wbf['title_doc'] = workbook.add_format({'bold': 1})
        self.wbf['title_doc'].set_font_size(12)

        self.wbf['hidden_content'] = workbook.add_format({'font_color': '#FFFFFF'})

        self.wbf['content'] = workbook.add_format()
        self.wbf['content'].set_left()
        self.wbf['content'].set_right()
        self.wbf['content'].set_border()

        self.wbf['content_center'] = workbook.add_format({'align': 'center'})
        self.wbf['content_center'].set_left()
        self.wbf['content_center'].set_right()

        return workbook
    
    def print_template_access(self):
        query="""
            SELECT name->>'en_US' as name
            FROM res_groups
            ORDER BY name
        """

        self._cr.execute(query)
        ress =self._cr.dictfetchall()

        if not ress:
            raise Warning("Data Tidak Ada !")

        title = 'Template Upload Res Groups'
        filename = title + '.xlsx'

        fp = BytesIO()
        wbf = self.wbf
        workbook = xlsxwriter.Workbook(fp)
        workbook = self._add_workbook_format(workbook)

        # Create Sheet
        worksheet_template = workbook.add_worksheet('Template Upload')
        worksheet_groups = workbook.add_worksheet('Daftar Res Groups')

        # Sheet Template Upload
        worksheet_template.set_column('A1:A1', 45)
        worksheet_template.write('A1', 'Groups Access' , wbf['header'])

        # Sheet Daftar Res Groups
        worksheet_groups.set_column('B1:B1', 45)
        row=0
        worksheet_groups.merge_range('A%s:A%s' % (row+1,row+2), 'No' , wbf['header'])
        worksheet_groups.merge_range('B%s:B%s' % (row+1,row+2), 'Access Name' , wbf['header'])

        no = 1      
        row += 2

        for res in ress:
            name = res.get('name')
            worksheet_groups.write('A%s' % row, no , wbf['content']) 
            worksheet_groups.write('B%s' % row, name , wbf['content']) 
            no+=1
            row += 1
        

        workbook.close()
        out=base64.encodebytes(fp.getvalue())
        fp.close()
        create = self.sudo().create ({
            'name': filename,
            'report_file': out
        })

        return {
            'type': 'ir.actions.act_url',
            "target": "new",
            'url': '/web/content/tw.res.groups.wizard/%s/report_file/%s?download=true' % (create.id, filename)
        }  
