import base64
import re
import xlsxwriter
import statistics
from io import BytesIO
from datetime import datetime, timedelta, date
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning

class WebReport(models.TransientModel):
    _name = "web.report"
    _description = "Report Utils"

    @api.model
    def _get_default_datetime_plus_7(self): 
        return datetime.now() + timedelta(hours=7)

    name = fields.Char(string='Name')
    report_file = fields.Binary('File', readonly=True)

    def _check_date_range_limit(self, start_date, end_date):
        if not self.env.user.has_group('web_report.group_web_report_admin_report') and start_date and end_date:
            limit = int(self.env['ir.config_parameter'].sudo().get_param('web_report.report_date_range_limit',31))
            if end_date - start_date > timedelta(limit):
                raise Warning('Perhatian!\nRange tanggal tidak boleh lebih dari ' + str(limit) + ' hari.\n\nNote: Jika ada kebutuhan khusus untuk menarik data lebih dari limit hari, silahkan hubungi Helpdesk.')

    def _excel_col_to_index(self, col):
        """
        Convert Excel column reference (A, B, ..., Z, AA, AB, etc.) to zero-based index
        
        :param col: str - Excel column reference (case-insensitive)
        :return: int - Zero-based column index
        """
        col = col.upper()
        index = 0
        for i, char in enumerate(reversed(col)):
            index += (ord(char) - ord('A') + 1) * (26 ** i)
        return index - 1  # Convert to zero-based index
    
    def _excel_index_to_column_name(self, column_index):
        """
        Converts a 1-based column index to its Excel column name.
        e.g., 1 -> A, 2 -> B, 27 -> AA
        """
        result = ""
        while column_index > 0:
            remainder = (column_index - 1) % 26
            result = chr(65 + remainder) + result  # 65 is ASCII for 'A'
            column_index = (column_index - 1) // 26
        return result

    def custom_title(self,text):
        return re.sub(r"(?:(?<=\W)|^)\w(?=\w)", lambda x: x.group(0).upper(), text)
    
    def get_cell_format(self, value):
        cell_format = 'content'
        if isinstance(value, float):
            cell_format = 'content_float'
        elif isinstance(value, int):
            cell_format = 'content_int'
        elif isinstance(value, date):
            cell_format = 'content_date'
        elif isinstance(value, datetime):
            cell_format = 'content_datetime'
        return self.wbf[cell_format]

    def _add_dynamic_header_format(self, workbook, bg_color, is_group_header=False):
        """
        Create format with dynamic background color for grouped headers.
        
        :param workbook: xlsxwriter workbook instance
        :param bg_color: Background color hex code (e.g., '#00CED1')
        :param is_group_header: True for group header (row 1), False for sub-header (row 2)
        :return: xlsxwriter format object
        """
        fmt = workbook.add_format({
            'bg_color': bg_color,
            'bold': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_color': '#000000',
            'font_size': 11 if is_group_header else 10,
        })
        fmt.set_border(1)
        return fmt

    def _write_grouped_headers(self, worksheet, workbook, header_groups, start_row, start_col, numbering, default_color='#FFFACD'):
        """
        Write multi-level grouped headers with custom styling.
        
        :param worksheet: xlsxwriter worksheet instance
        :param workbook: xlsxwriter workbook instance
        :param header_groups: List of header group configurations
            Example:
            [
                {
                    'name': 'PUST',          # Group header name (merged cell), optional
                    'bg_color': '#90EE90',   # Background color for group header
                    'columns': [             # Columns under this group
                        {'key': 'PUST_SR', 'label': 'Showroom', 'bg_color': '#90EE90'},
                        {'key': 'PUST_WS', 'label': 'Workshop', 'bg_color': '#FFFF00'},
                    ]
                },
                ...
            ]
        :param start_row: Starting row number
        :param start_col: Starting column number
        :param numbering: Whether numbering is enabled
        :param default_color: Default header color if not specified
        :return: tuple (group_row, sub_header_row, column_order, column_sizes)
        """
        group_row = start_row
        sub_header_row = start_row + 1
        col = start_col
        column_order = []  # List of column keys in order
        column_sizes = []
        
        # Handle numbering column
        if numbering:
            num_fmt = self._add_dynamic_header_format(workbook, default_color, is_group_header=False)
            worksheet.write(group_row, col, '', num_fmt)
            worksheet.write(sub_header_row, col, 'No', num_fmt)
            column_sizes.append(4)
            col += 1
        
        for group in header_groups:
            group_name = group.get('name', '')
            group_color = group.get('bg_color', default_color)
            columns = group.get('columns', [])
            
            if not columns:
                continue
            
            group_start_col = col
            group_end_col = col + len(columns) - 1
            
            # Write group header (merged if more than 1 column and has name)
            if group_name and len(columns) > 1:
                group_fmt = self._add_dynamic_header_format(workbook, group_color, is_group_header=True)
                worksheet.merge_range(group_row, group_start_col, group_row, group_end_col, group_name, group_fmt)
            elif group_name and len(columns) == 1:
                group_fmt = self._add_dynamic_header_format(workbook, group_color, is_group_header=True)
                worksheet.write(group_row, group_start_col, group_name, group_fmt)
            else:
                # No group name - write empty cells for group row
                for idx, column in enumerate(columns):
                    col_color = column.get('bg_color', group_color)
                    empty_fmt = self._add_dynamic_header_format(workbook, col_color, is_group_header=True)
                    worksheet.write(group_row, col + idx, '', empty_fmt)
            
            # Write sub-headers
            for column in columns:
                col_key = column.get('key', '')
                col_label = column.get('label', col_key.replace('_', ' ').title())
                col_color = column.get('bg_color', group_color)
                
                sub_fmt = self._add_dynamic_header_format(workbook, col_color, is_group_header=False)
                worksheet.write(sub_header_row, col, col_label, sub_fmt)
                
                column_order.append(col_key)
                column_sizes.append(len(str(col_label)))
                col += 1
        
        return group_row, sub_header_row, column_order, column_sizes

    wbf = {}

    def generate_report(self
        , report_name 
        , data
        , data_sheet=False
        , data_summary_header=False
        , data_summary_style=False
        , data_summary_header_col_size=True
        , start_date=False
        , end_date=False
        , header_title=True
        , header=True
        , header_color = '#FFFACD'
        , header_groups=None
        , capitalize=True
        , numbering=True
        , auto_filter=True
        , freeze_panes=True
        , freeze_panes_column=0
        , bottom_remark=True
        , show_total_footer=True
        , data_custom_footer={}
        , return_fp=False
        , remove_all_styling=False
        , is_by_pass_generate=False
        ):
        """ Return XLSX Report from the given 'List of Dictionary' data.
            :param report_name: File name of the report before given datetime at the end of it
            :param data: data with 'List of Dictionary' type, the key will be Header and the value will be inserted into each row 
            :param data_sheet: dictionary of sheet name and data, the key will be sheet name and the value will be inserted into each row 
            :param data_summary_header: dictionary of summary header, the key will be cell name and the value will be inserted into the key cell 
            :param data_summary_style: dictionary of summary header style, the key will be cell name and the value will be inserted into the key cell 
            :param data_summary_header_col_size: True or False, if True, summary header size will be calculated based on the content 
            :param start_date: For report title, if this param is filled, title will generated above header
            :param end_date: For report title, start_date must be filled to show end_date. end date will shown after start_date
            :param header: Enable/Disable header (title) option, header text will generated from data key's, underscores '_' will replaced with space and will capitalize unless all words is uppercase 
            :param header_color: Color of the header, the default will be yellow (#FFFF00)
            :param header_groups: List of header group configurations for multi-level headers with custom colors
                Example:
                [
                    {
                        'name': 'Group Name',      # Group header name (merged cell), optional
                        'bg_color': '#90EE90',     # Background color for group header
                        'columns': [               # Columns under this group
                            {'key': 'DATA_KEY', 'label': 'Display Label', 'bg_color': '#90EE90'},
                        ]
                    },
                ]
            :param capitalize: Enable/Disable auto capitalize for header text
            :param numbering: Enable/Disable Numbering. Number will generated at first column. The default will be True
            :param auto_filter: Enable/Disable Auto Filter. 'Auto Filter' will filter first row. The default will be True, however.. this only active when params header is true
            :param freeze_panes: Enable/Disable Freeze Pane. Freeze first column. The default will be True, however.. this only active when params header is true
            :param freeze_panes_column: Freeze column from given integer (starting from 0). The default will be 0, however.. this only active when params header & freeze_panes is true
            :param bottom_remark: Enable/Disable remark Give remark at the bottom of the workbook. The remark contains Downloader name & Download date
            :param show_total_footer: Enable/Disable total footer row. If True, adds a summary row at the bottom with sums of numeric columns. Default is False.
            :param data_custom_footer: Dictionary of custom params formulas for each column. The default is an empty dictionary.
            :param return_fp: Return file pointer instead of download URL if True
            :return: xlsx file of the report generated
        """
        if not data and not is_by_pass_generate:
            raise Warning("There is no data available.")

        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)       
        workbook = self.add_workbook_format(workbook,header_color,remove_all_styling)
        wbf = self.wbf

        if not data_sheet:
            data_sheet = {report_name: data}

        filename = report_name.lower()+"_"+ str(self._get_default_datetime_plus_7())+'.xlsx'
        for sheet_name, sheet_config in data_sheet.items():
            # Support both old format (list) and new format (dict with 'data' and 'header_groups')
            if isinstance(sheet_config, dict):
                data = sheet_config.get('data', [])
                sheet_header_groups = sheet_config.get('header_groups', header_groups)
            else:
                data = sheet_config
                sheet_header_groups = header_groups
            
            # Skip empty sheets
            if not data:
                continue
                
            # Give Report name
            report_name = sheet_name.replace("/","")
            worksheet = workbook.add_worksheet(report_name)

            # Initialize params
            column_size = []
            header_len = len(list(data[0].keys()))
            header_row = 0
            number = 1
            row = 0
            col = 0

            # Setup title
            if header_title:
                header_row = 3
                worksheet.merge_range(row,col,row,header_len, report_name, wbf['title_doc'])
                row += 1
            
                # Handle title
                if start_date:
                    # Change header row
                    header_row = 3

                    # Setup date title
                    time_title = str(start_date)
                    if end_date:
                        time_title += ' - '+str(end_date)

                    worksheet.merge_range(row,col,row, header_len, time_title, wbf['title_doc'])
                else:
                    worksheet.merge_range(row,col,row, header_len, str(self._get_default_datetime_plus_7()), wbf['title_doc'])
                
                # Add 2 rows if header_title or start_date is true untuk memberikan ruang untuk header
                if header_title or start_date:
                    row += 2
            
            # Handle Summary Header
            highest_summary_row = 0
            summary_column_size = {}
            if data_summary_header:
                for cell, value in data_summary_header.items():
                    # Extract row and column from cell 
                    # Cellreference (e.g., 'A1:D1' -> col_start='A', row_start=1, col_end='D', row_end=1)
                    is_merge = False
                    if ':' in cell:
                        split_cell = cell.split(':')
                        if len(split_cell) != 2:
                            raise Warning("Invalid cell format for summary header. Merged cell format must be 'column and row'. Ex: A1:A12")

                        cell_start = split_cell[0]
                        cell_end = split_cell[1]
                        
                        col_str_start = ''.join(filter(str.isalpha, cell_start.upper()))
                        row_str_start = ''.join(filter(str.isdigit, cell_start))

                        col_str_end = ''.join(filter(str.isalpha, cell_end.upper()))
                        row_str_end = ''.join(filter(str.isdigit, cell_end))
                        
                        if not col_str_start or not row_str_start or not col_str_end or not row_str_end:
                            raise Warning("Invalid cell format for summary header. Cell format must be 'column and row'. Ex: A9")

                        is_merge = True
                    else:
                        # Cellreference (e.g., 'A1' -> col='A', row=1)
                        col_str = ''.join(filter(str.isalpha, cell.upper()))
                        row_str = ''.join(filter(str.isdigit, cell))
                    
                        if not col_str or not row_str:
                            raise Warning("Invalid cell format for summary header. Cell format must be 'column and row'. Ex: A9")
                    
                    try:
                        if data_summary_style:
                            cell_format = self.wbf[data_summary_style]
                        else:
                            cell_format = self.get_cell_format(value)

                        if is_merge:
                            summary_row = int(row_str_start) - 1  # Convert to zero-based row
                            summary_col = self._excel_col_to_index(col_str_start)  # Convert to zero-based column
                            summary_row_end = int(row_str_end) - 1  # Convert to zero-based row
                            summary_col_end = self._excel_col_to_index(col_str_end)  # Convert to zero-based column
                            worksheet.merge_range(summary_row, summary_col, summary_row_end, summary_col_end, value, cell_format)
                        else:
                            summary_row = int(row_str) - 1  # Convert to zero-based row
                            summary_col = self._excel_col_to_index(col_str)  # Convert to zero-based column
                            worksheet.write(summary_row, summary_col, value, cell_format)

                            # Change column size if content bigger than previous stored size
                            if data_summary_header_col_size:
                                if summary_column_size.get(summary_col,0) < len(str(value)):
                                    summary_column_size[summary_col] = (len(str(value)))
                    except (ValueError, IndexError) as e:
                        raise Warning(f"Invalid cell reference: {cell}. Error: {str(e)}")
                    
                    
                    # Set highest summary row to determine where the first data will be inserted
                    highest_summary_row = max(highest_summary_row, summary_row)
                
                highest_summary_row += 2
                header_row = highest_summary_row

            row = max(row,highest_summary_row)

            # Handle header_groups if provided (use sheet-specific or global)
            grouped_column_order = None
            if sheet_header_groups and header:
                # Write grouped headers using helper method
                group_row, sub_header_row, grouped_column_order, column_size = self._write_grouped_headers(
                    worksheet, workbook, sheet_header_groups, row, 0, numbering, header_color
                )
                # Grouped headers use 2 rows
                header_row = sub_header_row
                row = sub_header_row + 1

            # Handle data
            for line in data:
                col = 0
                # Handle header (First data) - only if header_groups is not provided
                if header and number == 1 and not sheet_header_groups:
                    
                    # Give column number
                    if numbering:
                        worksheet.write(row, col, "No", wbf['header'])
                        column_size.append(2)
                        col += 1
                    
                    # Loop key for Header/Title
                    for key in line:
                        # Wirte Header Title with key from dictionary
                        formated_header_string = key.replace('_',' ')
                        # IF capitalize params is true and not all word is uppercase, capitalize words
                        if capitalize and not formated_header_string.isupper():
                            formated_header_string = formated_header_string.capitalize()

                        worksheet.write(row, col, formated_header_string, wbf['header'])
                        
                        # Write initial column size
                        column_size.append(len(str(formated_header_string)))
                        col+=1
                    row +=1
                    col = 0

                # Give column number
                if numbering:
                    worksheet.write(row, col, number, wbf['content'])
                    col += 1

                # Write Content
                # Use grouped_column_order if header_groups is provided
                keys_to_iterate = grouped_column_order if grouped_column_order else line.keys()
                for key in keys_to_iterate:
                    # Define Cell format
                    cell_data = line.get(key, '') if grouped_column_order else line[key]
                    cell_format = self.get_cell_format(cell_data)
                    # ? jika menggunakan cell_data if cell_data else '' untuk angka akan menjadi kosong/null, padahal harusnya menjadi 0
                    # worksheet.write(row, col, cell_data if cell_data else '', cell_format)
                    worksheet.write(row, col, cell_data, cell_format)

                    # Change column size if content bigger than previous stored size
                    if grouped_column_order:
                        current_column_index = grouped_column_order.index(key) + int(numbering)
                    else:
                        current_column_index = list(line.keys()).index(key) + int(numbering)
                    if current_column_index < len(column_size) and column_size[current_column_index] < len(str(cell_data)):
                        column_size[current_column_index] = (len(str(cell_data)))

                    col+=1
                
                row +=1
                number +=1
            
            # set column width
            for i in range(0, len(column_size)):
                final_column_size = max(column_size[i], summary_column_size.get(i,0)) + 2
                worksheet.set_column(i, i, final_column_size)

            # set auto_filter (only if worksheet have header)
            if header and auto_filter:
                worksheet.autofilter(header_row, 0, row-1, col-1)

            # freeze panes (only if worksheet have header)
            if header and freeze_panes:
                # Handle freeze_panes_column params, and check format 
                to_freeze_column = 0
                if isinstance(freeze_panes_column,int):
                    to_freeze_column = freeze_panes_column

                worksheet.freeze_panes(header_row+1, to_freeze_column)

            if show_total_footer and data and header:
                # Move to the row after the last data row
                col = 0
                
                # If numbering is enabled, skip the first column
                if numbering:
                    worksheet.write(row, col, "Total", wbf['content_total'])
                    col += 1

                # Get the first data row to determine column types
                first_row = next(iter(data))
                
                # Calculate and write totals for each column
                for i, (key, value) in enumerate(first_row.items()):
                    current_col = col + i
                    # Check if the column contains numeric values
                    if any(isinstance(d[key], (int, float)) for d in data):
                        # Check if there is custom footer calculation send by data_custom_footer params
                        operations = data_custom_footer.get(key.upper(),'SUM')
                        # Get column name from index + Write formula
                        col_name = self._excel_index_to_column_name(current_col+1)
                        formula = f'IFERROR({operations}({col_name}{highest_summary_row+2}:{col_name}{row}),0)'
                        # Write the total with total format
                        worksheet.write_formula(row, current_col, formula, wbf['content_total'])
                    else:
                        # For non-numeric columns, leave empty or put a dash
                        worksheet.write_blank(row, current_col, "", wbf['content_total'])
            
            # Set bottom remark
            if bottom_remark:
                worksheet.merge_range('A%s:D%s'%(row+2,row+2), '%s - %s' % (self.sudo().env.user.name, str(self._get_default_datetime_plus_7())) , wbf['footer']) 
            
        workbook.close()

        # Return file pointer if return_fp is True
        if return_fp:
            return fp

        out=base64.encodebytes(fp.getvalue())
        report = self.sudo().create({
            'report_file' : out,
            'name' : filename,
        })
        
        fp.close()
        return {
            'type': 'ir.actions.act_url',
            "target": "self",
            'url': '/web/content/web.report/%s/report_file/%s?download=true' % (report.id, filename)
        }  
    
    def add_workbook_format(self, workbook, header_color, remove_all_styling):
        if remove_all_styling:
            self.wbf['title_doc'] = workbook.add_format({})
            self.wbf['footer'] = workbook.add_format({})
            self.wbf['header'] = workbook.add_format({})
            self.wbf['content'] = workbook.add_format({})
            self.wbf['content_float'] = workbook.add_format({})
            self.wbf['content_total'] = workbook.add_format({})
            self.wbf['content_int'] = workbook.add_format({})
            self.wbf['content_date'] = workbook.add_format({'num_format': 'yyyy-mm-dd'})
            self.wbf['content_date_time'] = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm:ss'})
            
        else:
            self.wbf['title_doc'] = workbook.add_format({'bold': 1,'align': 'left'})
            self.wbf['title_doc'].set_font_size(12)

            self.wbf['footer'] = workbook.add_format({'align':'left'})

            self.wbf['header'] = workbook.add_format({'bg_color':header_color,'bold': 1,'align': 'center','font_color': '#000000'})
            self.wbf['header'].set_top(2)
            self.wbf['header'].set_bottom()
            self.wbf['header'].set_left()
            self.wbf['header'].set_right()
            self.wbf['header'].set_font_size(11)
            self.wbf['header'].set_align('vcenter')

            self.wbf['content'] = workbook.add_format({'align': 'left','font_color': '#000000'})
            self.wbf['content'].set_left()
            self.wbf['content'].set_right()
            self.wbf['content'].set_top()
            self.wbf['content'].set_bottom()
            self.wbf['content'].set_font_size(10)                

            self.wbf['content_float'] = workbook.add_format({'align': 'right','num_format': '#,##0.00'})
            self.wbf['content_float'].set_right() 
            self.wbf['content_float'].set_left()
            self.wbf['content_float'].set_top()
            self.wbf['content_float'].set_bottom()
            self.wbf['content_float'].set_font_size(10)                
            
            self.wbf['content_total'] = workbook.add_format({'bg_color': header_color, 'bold': 1, 'align': 'right', 'num_format': '#,##0.00'})
            self.wbf['content_total'].set_font_color('#000000')
            self.wbf['content_total'].set_font_size(10)                
            self.wbf['content_total'].set_right() 
            self.wbf['content_total'].set_left()
            self.wbf['content_total'].set_top()
            self.wbf['content_total'].set_bottom()
            
            self.wbf['content_int'] = workbook.add_format({'align': 'right','num_format': '#,##0'})
            self.wbf['content_int'].set_right() 
            self.wbf['content_int'].set_left()
            self.wbf['content_int'].set_top()
            self.wbf['content_int'].set_bottom()
            self.wbf['content_int'].set_font_size(10)
                    
            self.wbf['content_date'] = workbook.add_format({'num_format': 'yyyy-mm-dd'})
            self.wbf['content_date'].set_left()
            self.wbf['content_date'].set_right() 
            self.wbf['content_date'].set_top()
            self.wbf['content_date'].set_bottom()
            self.wbf['content_date'].set_font_size(10)                
                    
            self.wbf['content_date_time'] = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm:ss'})
            self.wbf['content_date_time'].set_left()
            self.wbf['content_date_time'].set_right() 
            self.wbf['content_date_time'].set_top()
            self.wbf['content_date_time'].set_bottom()
            self.wbf['content_date_time'].set_font_size(10)                
        
        return workbook   
    