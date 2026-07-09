# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
import os
import time
import traceback
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import re

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.tools import SQL

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


_logger = logging.getLogger(__name__)

    
class TwB2BFile(models.Model):
    _name = "tw.b2b.file"
    _description = "B2B File"

    _LARGE_FILE_THRESHOLD = 1024 * 1024
    _DEFAULT_BATCH_LIMIT = 200

    # 7: defaults methods
    def get_default_datetime(self):
        return datetime.now()

    # 8: fields
    name = fields.Char(string="File Name", help="B2B File Name")
    ext = fields.Char(string="Extension", help="File Extension of the file", compute='_compute_ext', store=True)
    state = fields.Selection([
        ('batch_loading', 'Batch Loading'),
        ('open', 'Open'),
        ('done', 'Done'),
        ('duplicate', 'Duplicate'),
        ('partially_error', 'Partially Error'),
        ('error', 'Error'),
        ('closed', 'Closed')
    ], default='open', string="Status",
    help=" * Open: The content has been pre-processed for creating a transactions.\n"
         " * Batch Loading: The file is too large and its lines are being generated per batch.\n"
         " * Done: The content has been processed into transactions.\n"
         " * Duplicate: The content is already exists, and unlikely to be processed.\n"
         " * Error: The content has an error when processing.\n"
         " * closed: The content has an error, and we don’t want to process it further.\n")
    upload_date = fields.Date(string="Upload Date", default=date.today(), help="Date the files are uploaded to the system")

    batch_limit = fields.Integer(string="Batch Limit", default=_DEFAULT_BATCH_LIMIT, help="Number of rows generated and processed per batch for large files.")
    batch_offset = fields.Integer(string="Batch Offset", default=0, help="Number of rows already generated from the large file.")
    batch_total_records = fields.Integer(string="Batch Total Records", default=0, help="Total processable rows available in the large file.")
    batch_file_path = fields.Char(string="Batch File Path", help="Temporary file path used for staged processing of large files.")
    batch_file_size = fields.Integer(string="File Size (Bytes)", help="Original imported file size in bytes.")
    content_open_count = fields.Integer(string="Open Contents", compute='_compute_content_state_counts')
    content_error_count = fields.Integer(string="Error Contents", compute='_compute_content_state_counts')
    content_done_count = fields.Integer(string="Done Contents", compute='_compute_content_state_counts')
    
    # 9: relation fields
    config_id = fields.Many2one('tw.b2b.file.config', help="Configurations")
    content_file_ids = fields.One2many('tw.b2b.file.content', 'file_id', string="Content Detail", help="The content detail of the uploaded file")

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('name')
    def _compute_ext(self):
        for record in self:
            record.ext = record.name.split('.')[-1]

    @api.depends('content_file_ids.state')
    def _compute_content_state_counts(self):
        for record in self:
            contents = record.content_file_ids
            record.content_open_count = len(contents.filtered(lambda content: content.state == 'open'))
            record.content_error_count = len(contents.filtered(lambda content: content.state == 'error'))
            record.content_done_count = len(contents.filtered(lambda content: content.state == 'done'))

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                raise Warning(_("File name cannot be empty!"))

            if not vals.get('upload_date'):
                vals['upload_date'] = date.today()
            if not vals.get('batch_limit'):
                vals['batch_limit'] = self._DEFAULT_BATCH_LIMIT
                
        return super().create(vals_list)
    
    # TODO: Delete if the transaction requires delete
    def unlink(self):
        for record in self:
            if not record.env.user.has_group('tw_base.group_system_admin'):
                raise Warning(_("Warning!\nCannot delete records!"))
        
        return super().unlink()

    # 13: action methods
    def action_read_folder_in(self):
        self._read_folder_in()

    def action_batch_process_file(self):
        # iterate file listed in the directory
        active_ids = self.env.context.get('active_ids')
        for file in self.browse(active_ids):
            file._process_draft_file()
            file._update_states()
    
    def action_process(self):
        self._process_draft_file()
        self._update_states()
            
    def action_re_open_state(self):
        self.content_file_ids.filtered(lambda x: x.state in ('error','pending')).write({ 'state': 'open', 'log': False })
        self.state = 'open'
    
    def action_close(self):
        self.state = 'closed'

    def action_open_content_list(self):
        self.ensure_one()
        action = self.env.ref('tw_b2b_file.action_window_tw_b2b_file_content').read()[0]
        action['domain'] = [('file_id', '=', self.id)]
        action['context'] = {
            'default_file_id': self.id,
        }
        return action
            
    # 14: private methods
    def _configuration_file(self, code):
        configuration_file = self.env['tw.config.files'].search([('active', '=', True),
                                                                 ('name', '=', code)])
        if not configuration_file:
            raise Warning(f"Warning!\nConfiguration files with Code {code} does not exists!")
        
        return configuration_file
    
    def _validate_path(self, path):
        if not os.path.exists(path):
            raise Warning(_(f"Warning!\nDirectory {path} is not found {os.linesep}!"))

        if not os.path.isdir(path):
            raise Warning(_(f"Warning!\nDirectory {path} is not a folder {os.linesep}!"))

        if not os.access(path, os.W_OK):
            raise Warning(_(f"Warning!\nDirectory {path} does not have write access {os.linesep}!"))
        
        return True
        
    def _get_path(self, code):
        config = self._configuration_file(code)
        self._validate_path(config.local_path)
        
        return config.local_path
    
    def _move_file(self, source_file, dest_dir, filename):
        """
        Moves a file from the source location to the destination directory.
        If a file with the same name already exists in the destination directory,
        the method appends '_new' to the filename to avoid duplication.
        """
        dest_file = os.path.join(dest_dir, filename)
        if os.path.exists(dest_file):
            dest_file = os.path.join(dest_dir, f"{os.path.splitext(filename)[0]}_new{os.path.splitext(filename)[1]}")
        os.rename(source_file, dest_file)
        return dest_file

    def _move_file_to_error(self, source_file, err_dir):
        if source_file and os.path.exists(source_file):
            self._move_file(source_file, err_dir, os.path.basename(source_file))

    def _is_large_file(self, file_path):
        return os.path.getsize(file_path) > self._LARGE_FILE_THRESHOLD

    def _get_batch_limit_value(self):
        self.ensure_one()
        return self.batch_limit if self.batch_limit and self.batch_limit > 0 else self._DEFAULT_BATCH_LIMIT

    def _get_record_name(self, file, existing_file):
        name = file.split('.')[0]
        ext = file.split('.')[-1]
        return f"{name} - ({len(existing_file)}).{ext}" if existing_file else file

    def _split_record_by_index_mapping(self, record, config):
        row = []
        stripped_record = record.strip()
        for index in config.index_mapping.split(','):
            start, end = index.strip("[]").split(":")
            start_idx = int(start) if start else None
            end_idx = int(end) if end else None
            row.append(stripped_record[start_idx:end_idx])
        return row

    def _prepare_content_file_vals(self, config, record):
        content_line_ids = []
        delimiter = chr(int(config.separator_id.value))
        if config.separator_id.name != 'index':
            row = record.strip().split(delimiter)
            if not any(row):
                return False
        else:
            row = self._split_record_by_index_mapping(record, config)
            if not any(row):
                return False

        for dt in zip(config.headers.split(','), row):
            content_line_ids.append([0, 0, {'name': dt[0], 'value': dt[1]}])

        return {
            'name': record,
            'content_line_ids': content_line_ids,
        }

    def _prepare_content_file_ids(self, config, records):
        content_file_ids = []
        if config.name == 'UPO':
            self._get_upo_content_file_ids(config, records, content_file_ids)
            return content_file_ids

        for record in records:
            content_vals = self._prepare_content_file_vals(config, record)
            if content_vals:
                content_file_ids.append([0, 0, content_vals])
        return content_file_ids

    def _count_batch_records(self, file_path, config):
        count = 0
        if config.name == 'UPO':
            with open(file_path, 'r') as file_obj:
                for record in file_obj:
                    stripped_record = record.strip()
                    if not stripped_record:
                        continue
                    if 'error' in record and re.search(r'ke-(\d+)', record):
                        count += 1
            return count

        with open(file_path, 'r') as file_obj:
            for record in file_obj:
                if self._prepare_content_file_vals(config, record):
                    count += 1
        return count

    def _prepare_upo_batch_content_vals(self, config, offset, limit):
        delimiter = chr(int(config.separator_id.value))
        dict_data = {}
        content_vals_list = []
        current_offset = 0

        with open(self.batch_file_path, 'r') as file_obj:
            for record in file_obj:
                row = record.strip().split(delimiter)
                if row == ['']:
                    continue

                if 'error' not in record:
                    dict_data[len(dict_data) + 1] = row
                    continue

                line_ke = re.search(r'ke-(\d+)', record)
                if not line_ke:
                    continue

                if current_offset >= offset and len(content_vals_list) < limit:
                    line_no = int(line_ke.group(1))
                    data_row = dict_data.get(line_no)
                    if not data_row:
                        raise Warning(_(f"UPO line reference {line_no} is not found in {self.name}!"))

                    content_line_ids = [[0, 0, {
                        'name': 'data',
                        'value': data_row[0],
                    }]]
                    content_vals_list.append({
                        'name': row[0],
                        'content_line_ids': content_line_ids,
                    })

                current_offset += 1
                if len(content_vals_list) >= limit:
                    break

        return content_vals_list

    def _prepare_standard_batch_content_vals(self, config, offset, limit):
        content_vals_list = []
        current_offset = 0

        with open(self.batch_file_path, 'r') as file_obj:
            for record in file_obj:
                content_vals = self._prepare_content_file_vals(config, record)
                if not content_vals:
                    continue

                if current_offset >= offset and len(content_vals_list) < limit:
                    content_vals_list.append(content_vals)

                current_offset += 1
                if len(content_vals_list) >= limit:
                    break

        return content_vals_list

    def _load_next_batch_content(self):
        self.ensure_one()
        if self.state != 'batch_loading':
            return 0

        if not self.batch_file_path:
            raise Warning(_(f"Batch file path for {self.name} is empty!"))

        if not os.path.exists(self.batch_file_path):
            raise Warning(_(f"Batch file {self.batch_file_path} is not found!"))

        if self.batch_offset >= self.batch_total_records:
            return 0

        limit = self._get_batch_limit_value()
        if self.config_id.name == 'UPO':
            content_vals_list = self._prepare_upo_batch_content_vals(self.config_id, self.batch_offset, limit)
        else:
            content_vals_list = self._prepare_standard_batch_content_vals(self.config_id, self.batch_offset, limit)

        if not content_vals_list:
            return 0

        self.env['tw.b2b.file.content'].create([
            {
                'file_id': self.id,
                'name': vals['name'],
                'content_line_ids': vals['content_line_ids'],
            }
            for vals in content_vals_list
        ])
        self.batch_offset += len(content_vals_list)
        return len(content_vals_list)
    
    def _read_folder_in(self):
        """
        Reads files from the 'MFT-IN' directory, processes them according to their configuration,
        stores the content in the model, and moves the files to the 'MFT-PROCESS' directory.
        The method performs the following steps:
        1. Retrieves the source and destination paths.
        2. Iterates over the files in the source directory.
        3. For each file, determines its extension and retrieves the corresponding configuration.
        4. Reads the file content, splits it based on the configured delimiter, and stores the data in the model.
        5. Checks for existing files with the same name and marks new entries as 'duplicate' if found.
        6. Moves the processed files to the destination directory.
        Raises:
            Exception: Logs an error if there is an issue creating the record in the model.
        Logs:
            Warning: If no configuration is found for the file extension.
            Error: If there is an issue creating the record in the model.
        """
        src = self._get_path('MFT-IN')
        pro = self._get_path('MFT-PROCESS')
        arc = self._get_path('MFT-ARCHIN')
        err = self._get_path('MFT-ERROR')

        # iterate file listed in the directory
        for file in os.listdir(src):
            # find ext to obtain file config
            name = file.split('.')[0]
            ext = file.split('.')[-1]
            config = self.env['tw.b2b.file.config'].search([('name', '=', ext)])
            if not config:
                _logger.warning(_(f"B2B File Configuration for extension {ext} is not found!"))
                continue

            existing_file = self.search([('name', '=', file)])
            file_in = os.path.join(src, file)
            is_large_file = self._is_large_file(file_in)

            if is_large_file:
                batch_total_records = self._count_batch_records(file_in, config)
                record = False
                archived_path = False
                try:
                    record = self.create({
                        'name': self._get_record_name(file, existing_file),
                        'config_id': config.id,
                        'batch_limit': self._DEFAULT_BATCH_LIMIT,
                        'batch_offset': 0,
                        'batch_total_records': batch_total_records,
                        'state': 'duplicate' if existing_file else 'batch_loading',
                    })

                    archived_path = self._move_file(file_in, arc, file)
                    record.write({
                        'batch_file_path': archived_path,
                        'batch_file_size': os.path.getsize(archived_path),
                    })
                except Exception as e:
                    _logger.error(e.__str__())
                    if record:
                        record.write({'state': 'error'})
                    self._move_file_to_error(archived_path or file_in, err)
                continue

            # read file content and store to models
            with open(file_in, 'r') as f:
                records = f.readlines()
                content_file_ids = self._prepare_content_file_ids(config, records)

            file_process = self._move_file(file_in, pro, file)
            try:
                self.create({
                    'name': self._get_record_name(file, existing_file),
                    'config_id': config.id,
                    'content_file_ids': content_file_ids,
                    'state': 'duplicate' if existing_file else 'open'
                })

                self._move_file(file_process, arc, os.path.basename(file_process))
            except Exception as e:
                _logger.error(e.__str__())
                self._move_file(file_process, err, os.path.basename(file_process))
                continue

    def _get_upo_content_file_ids(self,config,records,content_file_ids):
        dict_data = {}
        list_data_error = []

        delimiter = chr(int(config.separator_id.value))

        for record in records:
            row = record.strip().split(delimiter)
            # Check blank space
            if row != ['']:
                if 'error' not in record:
                    dict_data.update({
                        len(dict_data) + 1: row  
                    })
                else:
                    line_ke = re.search(r'ke-(\d+)', record)
                    if line_ke:
                        line_no = int(line_ke.group(1))
                        list_data_error.append({
                            'line': line_no,
                            'rows': [row]
                        })

        content_line_ids = []
        for data in list_data_error:
            # Data
            content_line_ids.append([0, 0, {
                'name': 'data',
                'value': dict_data.get(data['line'])[0]
            }])
            content_file_ids.append([0, 0, {
                'name': data['rows'][0][0],
                'content_line_ids': content_line_ids
            }])
            content_line_ids = []

        return content_file_ids

    def _process_draft_file(self):
        self.ensure_one()
        if self.state == 'batch_loading':
            self._load_next_batch_content()
            return []

        content_states = []
        ext = self.config_id.name
        limit = self.config_id.limit
        #? Generate data SL hanya di proses pada saat generate data SIPB
        excluded_ext = ['SL']
        content_files = self.content_file_ids.filtered(lambda x: x.state == 'open')
        if limit > 0:
            content_files = content_files[:limit]
        start = datetime.now()
        if not self.config_id.is_process_by_header:
            if ext in excluded_ext:
                content_files.write({'state': 'pending', 'log': 'Pending. It will be processed in another action'})
            for content in content_files:
                try:
                    for content in content_files:
                        content.with_user(SUPERUSER_ID).process_file(ext)
                        content_states.append(content.state)
                    self.env.cr.commit()  # Commit hanya jika semua berhasil
                except Exception as err:
                    error_traceback = "\n\n" + traceback.format_exc()
                    self.env.cr.rollback()  # Rollback semua perubahan jika ada error
                    _logger.error(error_traceback)
                    content_files = self.content_file_ids.filtered(lambda x: x.state == 'open')
                    content_files.write({'state': 'error', 'log': err.__str__() + error_traceback})
        else:
            state = 'error'
            error = ''
            try:
                self.with_user(SUPERUSER_ID).process_file(ext)
                state = 'done'
            except Exception as err:
                error_traceback = "\n\n" + traceback.format_exc()
                self._cr.rollback()
                _logger.error(error_traceback)
                error = err.__str__() + error_traceback
            finally:
                for content in content_files:
                    content.log = error
                    content.state = state
                    content_states.append(content.state)

        end = datetime.now()
        _logger.info(f"Process {ext} file completed in {end - start}")
        return content_states
    
    def _update_states(self):
        for file in self:
            if file.state == 'batch_loading':
                if file.batch_offset >= file.batch_total_records:
                    file.state = 'open'
                else:
                    file.state = 'batch_loading'
                continue

            error = file.content_file_ids.filtered(lambda x: x.state == 'error')
            done = file.content_file_ids.filtered(lambda x: x.state == 'done')
            pending_or_open = file.content_file_ids.filtered(lambda x: x.state in ('open', 'pending'))

            if not file.content_file_ids and file.batch_total_records == 0:
                file.state = 'done'
            elif len(done) == len(file.content_file_ids):
                file.state = 'done'
            elif len(error) == len(file.content_file_ids):
                file.state = 'error'
            elif error:
                file.state = 'partially_error'
            elif pending_or_open:
                file.state = 'open'
            else:
                file.state = 'open'

    def schedulle_read_folder_in(self):
        self._read_folder_in()

    def schedulle_process_outstanding_file(self, limit=20):
        priority_order = ['SIPB', 'PS']
        processed = 0
        batch_processed_ids = []

        # Stage 1: only load content lines for batch_loading files.
        for priority_ext in priority_order:
            if processed >= limit:
                return

            remaining_limit = limit - processed
            files = self.suspend_security().search([
                ('config_id.name', '=', priority_ext),
                ('state', '=', 'batch_loading')
            ], limit=remaining_limit)

            for file in files:
                file._process_draft_file()
                file._update_states()
                batch_processed_ids.append(file.id)
                processed += 1
                if processed >= limit:
                    return

        excluded_ext = ['SL'] + priority_order
        remaining_limit = limit - processed
        if remaining_limit <= 0:
            return

        files = self.suspend_security().search([
            ('config_id.name', 'not in', excluded_ext),
            ('state', '=', 'batch_loading')
        ], limit=remaining_limit)

        for file in files:
            file._process_draft_file()
            file._update_states()
            batch_processed_ids.append(file.id)
            processed += 1
            if processed >= limit:
                return

        # Stage 2: process normal open files only.
        for priority_ext in priority_order:
            if processed >= limit:
                return

            remaining_limit = limit - processed
            domain = [
                ('config_id.name', '=', priority_ext),
                ('state', '=', 'open'),
            ]
            if batch_processed_ids:
                domain.append(('id', 'not in', batch_processed_ids))

            files = self.suspend_security().search(domain, limit=remaining_limit)

            for file in files:
                file._process_draft_file()
                file._update_states()
                processed += 1
                if processed >= limit:
                    return

        remaining_limit = limit - processed
        if remaining_limit <= 0:
            return

        domain = [
            ('config_id.name', 'not in', excluded_ext),
            ('state', '=', 'open'),
        ]
        if batch_processed_ids:
            domain.append(('id', 'not in', batch_processed_ids))

        files = self.suspend_security().search(domain, limit=remaining_limit)

        for file in files:
            file._process_draft_file()
            file._update_states()
            processed += 1
            if processed >= limit:
                return

    def schedulle_set_error_to_draft(self):
        for file in self.suspend_security().search([('state', 'in', ('error', 'partially_error'))]):
            file.content_file_ids.filtered(lambda x: x.state == 'error').write({'state': 'open','log': False})
            file.state = 'open'
    
    def schedulle_process_utc(self,limit=1, state='open'):
        utc_files = self.search([('config_id.name', '=', 'UTC'), ('state', 'in', ['open', 'partially_error'])],limit=limit)
        for utc in utc_files:
            utc.content_file_ids.filtered(lambda x: x.state == state)._process_utc()
            
            not_done = utc.content_file_ids.filtered(lambda x: x.state != 'done')
            if not not_done:
                utc.state = 'done'
    

    # PROCESS FILE
    def process_file(self, ext):
        if self.state == 'open':
            method_name = f'_process_{ext.lower()}'
            process_method = getattr(self, method_name, None)
            if process_method:
                process_method()
            else:
                raise Warning(_(f"No attribute named _process_{ext.lower()}!"))
    
    def _process_fdo(self):
        """
        Process FDO file content in batch mode.
        Groups content lines by invoice number and processes them together.
        """
        # Initialize services with suspend_security
        product_product = self.env['product.product'].suspend_security()
        stock_picking = self.env['stock.picking'].suspend_security()
        
        # Group content lines by invoice number
        invoice_groups = {}
        for content in self.content_file_ids.filtered(lambda x: x.state == 'open'):
            data = content.convert_to_vals()
            if not data:
                raise Warning(_("Data not found!"))

            invoice_number = data.get('no_invoice')
            if not invoice_number:
                raise Warning(_("Invoice number not found in data"))
                
            if invoice_number not in invoice_groups:
                invoice_groups[invoice_number] = []
            invoice_groups[invoice_number].append((content, data))
        
        # Process each invoice group
        for invoice_number, content_data_pairs in invoice_groups.items():
            # Get first content line for common data
            first_content, first_data = content_data_pairs[0]
            
            # Get branch and journal info
            branch_obj = self.env['res.company'].suspend_security().search(
                [('code', '=', first_content._get_default_main_dealer_code())], 
                limit=1
            )
            if not branch_obj:
                raise Warning(_("Branch not found!"))
            
            journal_id = first_content._get_purchase_journal_id(branch_obj.id, 'Sparepart')
            if not journal_id:
                raise Warning(_("Journal Purchase not found for Sparepart in Branch %s" % branch_obj.name))
            
            # Prepare invoice data
            invoice_vals = None
            invoice_header_obj = None
            invoice_line_vals_list = []
            
            total_discount = 0
            # First pass: collect all data and validate
            for content, data in content_data_pairs:
                # Parse common data
                invoice_date = data.get('tanggal_invoice')
                ps_number = str(data.get('kode_ps')).replace(' ', '')
                product_code = str(data.get('kode_sparepart')).replace(' ', '')
                quantity = float(data.get('qty'))
                price = float(data.get('price'))
                discount1 = float(data.get('discount_satu'))
                discount2 = float(data.get('discount_dua'))
                discount3 = float(data.get('discount_tiga'))
                dpp = float(data.get('dpp'))
                top_date = data.get('top')
                ppn = float(data.get('ppn'))
                top_ppn_date = data.get('top_ppn')
                discount4 = float(data.get('discount_empat'))
                invoice_total = data.get('invoice_jml')
                code_md = data.get('kode_md')

                # Format dates
                top_date_fix = f"{top_date[4:]}-{top_date[2:4]}-{top_date[0:2]}" if top_date and len(top_date) >= 8 else False
                invoice_date_fix = f"{invoice_date[4:]}-{invoice_date[2:4]}-{invoice_date[0:2]}" if invoice_date and len(invoice_date) >= 8 else False
                
                # Find product
                product_obj = product_product.search([('default_code', '=', product_code)], limit=1)
                if not product_obj:
                    raise Warning(_("Product %s not found!" % product_code))
                
                # Get product accounts
                get_account = product_obj.product_tmpl_id._get_product_accounts()
                account_id = get_account.get('stock_input', {}).id
                if not account_id:
                    raise Warning(_("Account configuration for product %s not found!" % product_code))
                
                # Validate quantities
                total_qty_ps = first_content._get_total_qty('PS', 'qty_ps', 'kode_ps', None, ps_number)
                total_qty_fdo = first_content._get_total_qty('FDO', 'qty', 'kode_ps', self.id, ps_number)
                if total_qty_ps != total_qty_fdo:
                    raise Warning(_("Total Qty PS %s is %s not equal to Total Qty FDO %s!" % (ps_number, total_qty_ps, total_qty_fdo)))
                
                # Find picking/PO
                picking_obj = stock_picking.search([
                    ('mft_reference', '=', ps_number),
                    ('purchase_order_id', '!=', False),
                ], limit=1)
                if not picking_obj:
                    raise Warning(_("Picking/PS %s not found!" % ps_number))
                
                # Store invoice header data from first line
                if invoice_vals is None:
                    # Check if invoice exists
                    invoice_header_obj = self.env['account.move'].suspend_security().search([
                        ('ref', '=', invoice_number),
                        ('company_id', '=', branch_obj.id),
                        ('division', '=', 'Sparepart'),
                        ('partner_id', '=', branch_obj.default_supplier_id.id),
                        ('move_type', '=', 'in_invoice'),
                    ], limit=1)
                    
                    if not invoice_header_obj:
                        # Prepare invoice values
                        invoice_vals = {
                            'move_type': 'in_invoice',
                            'ref': invoice_number,
                            'company_id': branch_obj.id,
                            'division': 'Sparepart',
                            'partner_id': branch_obj.default_supplier_id.id,
                            'invoice_date': invoice_date_fix,
                            'invoice_date_due': top_date_fix,
                            'journal_id': journal_id,
                            'is_combined_tax': True,
                            'invoice_line_ids': [],
                        }
                
                # Prepare invoice line
                total_discount_line = discount1 + discount2 + discount3 + discount4
                total_discount += total_discount_line

                untaxed_price = (price * quantity) - total_discount_line
                tax_obj = self.env['account.tax'].suspend_security()._verify_account_tax(untaxed_price, ppn, 'purchase', 'percent')
                price_unit = price * ((tax_obj.amount / 100) + 1)

                # Find purchase order lines via the picking's stock moves
                moves = picking_obj.move_ids_without_package.filtered(
                    lambda m: m.product_id.id == product_obj.id
                )
                if not moves:
                    raise Warning(_("Stock Move for %s product %s not found in Picking %s!" % (picking_obj.name, product_obj.default_code, picking_obj.name)))
                
                remaining_qty = quantity
                for move in moves:
                    po_line = move.purchase_line_id
                    if not po_line:
                        continue
                    
                    # Allocate quantity proportionally based on stock move quantity
                    alloc_qty = min(move.product_uom_qty, remaining_qty)
                    if alloc_qty <= 0:
                        continue

                    # Update purchase order price
                    vals_pol = {'price_unit': price_unit}
                    if not po_line.original_price_unit:
                        vals_pol['original_price_unit'] = po_line.price_unit
                    po_line.write(vals_pol)

                    invoice_line_vals = {
                        'product_id': product_obj.id,
                        'name': product_obj.name,
                        'company_id': branch_obj.id,
                        'quantity': alloc_qty,
                        'price_unit': price_unit,
                        'account_id': account_id,
                        'purchase_line_id': po_line.id,
                    }
                    
                    invoice_line_vals_list.append((content, invoice_line_vals))
                    remaining_qty -= alloc_qty
   
            # Create/update invoice if we have valid lines
            if invoice_line_vals_list:
                if not invoice_vals:
                    raise Warning(_("Invoice %s already exists in the system!") % invoice_number)
                
                # Create invoice with all lines at once
                invoice_vals['invoice_line_ids'] = [(0, 0, vals) for _, vals in invoice_line_vals_list]
                account_discounts = self.env['tw.account.discount'].with_company(branch_obj)._get_discount_account(branch_obj, 'in_invoice')
                if total_discount > 0:
                    account_discount = account_discounts.filtered(lambda x: x.name == 'Discount Other')
                    invoice_vals['discount_line_ids'] = [(0, 0, account_discount._prepare_discount_invoice_line(total_discount, branch_obj.id))]

                invoice_header_obj = self.env['account.move'].sudo().create(invoice_vals)
                
                # Post the invoice
                invoice_header_obj.with_company(invoice_header_obj.company_id).action_open()
                invoice_header_obj.with_company(invoice_header_obj.company_id).action_post()
                    
    
    def _process_inv(self):
        def get_lot(data,product_id):
            lot_obj = self.env['stock.lot'].suspend_security().search([
                ('sipb_number', '=', data.get('sipb_number')),
                ('ship_list_number', '=', data.get('ship_list_number')),
                ('product_id', '=', product_id),
                ('purchase_order_id', '!=', False),
                ('supplier_invoice_id', '=', False)
            ],limit=1)
            if not lot_obj:
                raise Warning(_("Lot with SIPB %s and SL %s without invoice not found!\nContent line generation has been skipped." % (data.get('sipb_number'), data.get('ship_list_number'))))
            return lot_obj

        def get_purchase_order(lot_obj):
            purchase_order_obj = lot_obj.purchase_order_id
            if not purchase_order_obj:
                raise Warning(_("Purchase Order for %s not found!" % lot_obj.name))
            return purchase_order_obj
        
        def get_purchase_order_line(purchase_order_id, product_id):
            purchase_order_line_obj = self.env['purchase.order.line'].suspend_security()._get_purchase_line_id(purchase_order_id.id, product_id.id)
            if not purchase_order_line_obj:
                raise Warning(_("Purchase Order Line for %s product %s not found!" % (purchase_order_id.name, product_id.default_code)))
            return purchase_order_line_obj
        
        def get_header_data(data, po):
            invoice_data = po._prepare_invoice()
            branch_config_obj = self.env['tw.account.setting'].suspend_security()._get_purchase_journal_id(po.company_id.id, 'Unit')
            if not branch_config_obj:
                raise Warning(_(
                        f"No journal found for the Unit division in Branch {branch_obj.display_name}.\n"
                        "Please configure the journal in the branch settings.\n"
                        "Content line generation has been skipped."
                    ))
            if not branch_config_obj:
                raise Warning(_(
                        f"No journal found for the Unit division in Branch {branch_obj.display_name}.\n"
                        "Please configure the journal in the branch settings.\n"
                        "Content line generation has been skipped."
                    ))

            top = str(data.get('top'))
            factur_date = str(data.get('factur_date'))
            invoice_data['invoice_date'] = top[4:]+"-"+top[2:4]+"-"+top[0:2]
            invoice_data['invoice_date_due'] = factur_date[4:]+"-"+factur_date[2:4]+"-"+factur_date[0:2]
            invoice_data['ref'] = data.get('factur_number')
            invoice_data['division'] = 'Unit'
            invoice_data['journal_id'] = branch_config_obj
            invoice_data['is_combined_tax'] = True
            return invoice_data
        
        def get_line_data(data,po_line_id):
            line_vals = po_line_id.suspend_security()._prepare_account_move_line()
            amount = int(data.get('amount')) if data.get('amount') else 0
            qty = int(data.get('qty')) if data.get('qty') else 0
            ppn = int(data.get('ppn')) if data.get('ppn') else 0
            price_unit = (amount + ppn) / qty
            line_vals['price_unit'] = price_unit
            line_vals['quantity'] = qty
            
            tax_ids = []
            tax_obj = self.env['account.tax'].suspend_security()._verify_account_tax(amount, ppn, 'purchase', 'percent')
            branch_obj = po_line_id.order_id.company_id
            if tax_obj:
                tax_ids.append(tax_obj.id)
            pph_id = branch_obj.additional_purchase_tax_id.id if branch_obj.additional_purchase_tax_id.id else None
            if pph_id:
                tax_ids.append(pph_id)
            line_vals['tax_ids'] = [(6, 0, tax_ids)]

            # Update purchase order price
            vals_pol = {'price_unit': price_unit}
            if not po_line_id.original_price_unit:
                vals_pol['original_price_unit'] = po_line_id.price_unit
            po_line_id.write(vals_pol)

            return line_vals
        
        def get_account_discount(name,account_discounts):
            account_discount = account_discounts.filtered(lambda x: x.name == name)
            if not account_discount:
                raise ValidationError(_("Account Discount untuk %s belum disetting, silahkan konfigurasi terlebih dahulu." % name))
            return account_discount

        content_to_process = self.content_file_ids.filtered(lambda x: x.state == 'open')
        if not content_to_process:
            return
        
        sequence = 10
        purchase_order_id = False
        invoice_vals = {}
        discount_type_cash = 0
        discount_other = 0
        discount_quotation = 0
        lot_objs = []
        for content in content_to_process:
            data = content.convert_to_vals()
            # Verifikasi
            if not data:
                raise Warning(_("Data not found!\n Content line generation has been skipped."))

            product_id = content._get_unit_product_id(data.get('type_code'),data.get('color_code'))
            if not product_id:
                raise Warning(_(f"Product {data.get('type_code')} with color {data.get('color_code')} not found!\n Content line generation has been skipped."))

            content_sl_ids = content._get_content('SL','type_code','color_code',data.get('type_code'),data.get('color_code'),data.get('ship_list_number'))
            content_obj = content.suspend_security().browse(content_sl_ids)
            if not content_obj:
                raise Warning(_(f"Shipping List {data.get('ship_list_number')} for product {data.get('type_code')} with color {data.get('color_code')} not found!\n Content line generation has been skipped."))

            total_qty_inv = content._get_total_qty('INV',data.get('type_code'),data.get('color_code'),content.file_id.id,data.get('ship_list_number'))
            if len(content_sl_ids) != total_qty_inv:
                raise Warning(_(
                        f"Total quantity for Ship List {data.get('ship_list_number')} is {len(content_sl_ids)}, "
                        f"which does not match the total quantity for Invoice/INV {total_qty_inv}.\n"
                        "Content line generation has been skipped."
                    ))

            # Pemrosesan
            lot_obj = get_lot(data, product_id)
            lot_objs.append(lot_obj)

            purchase_order_id = get_purchase_order(lot_obj)
            if not invoice_vals:
                invoice_vals = get_header_data(data,purchase_order_id)
            
            purchase_order_line_id = get_purchase_order_line(purchase_order_id,lot_obj.product_id)
            line_vals = get_line_data(data,purchase_order_line_id)
            line_vals.update({'sequence': sequence})
            invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
            sequence += 1

            discount_type_cash += int(data.get('discount_type_cash')) if data.get('discount_type_cash') else 0
            discount_other += int(data.get('discount_other')) if data.get('discount_other') else 0
            discount_quotation += int(data.get('discount_quotation')) if data.get('discount_quotation') else 0
        
        # Handle Discount
        move_type = 'in_invoice'
        invoice_vals['discount_line_ids'] = []
        account_discounts = self.env['tw.account.discount']._get_discount_account(purchase_order_id.company_id, move_type)
        if not account_discounts:
            raise ValidationError(_("Account Discount untuk %s belum disetting, silahkan konfigurasi terlebih dahulu." % move_type))
            
        account_discount = get_account_discount('Discount Cash', account_discounts)
        invoice_vals['discount_line_ids'].append((0, 0, account_discount._prepare_discount_invoice_line(discount_type_cash or 0, purchase_order_id.company_id.id)))
        
        account_discount = get_account_discount('Discount Other', account_discounts)
        invoice_vals['discount_line_ids'].append((0, 0, account_discount._prepare_discount_invoice_line(discount_other or 0, purchase_order_id.company_id.id)))
        
        account_discount = get_account_discount('Discount Program', account_discounts)
        invoice_vals['discount_line_ids'].append((0, 0, account_discount._prepare_discount_invoice_line(discount_quotation or 0, purchase_order_id.company_id.id)))


        create_invoice = self.env['account.move'].with_context(default_move_type='in_invoice').with_company(purchase_order_id.company_id.id).create(invoice_vals)
        create_invoice.action_open()
        create_invoice.sudo().action_post()

        for lot_obj in lot_objs:
            lot_obj.write({ 
                'supplier_invoice_id': create_invoice.id,
                'supplier_invoice_number': invoice_vals.get('ref') if invoice_vals.get('ref') else ''
            })
        
        return create_invoice

    def _process_ps(self):
        """
        Optimized PS file processing with header-level batch operations.
        Reduces database queries from ~3000 to ~50-100 for 200 lines.
        """
        content_files = self.content_file_ids.filtered(lambda x: x.state == 'open')
        if not content_files:
            return
        
        # Initialize models with sudo
        StockPicking = self.env['stock.picking'].sudo()
        StockPickingType = self.env['stock.picking.type'].sudo()
        StockMove = self.env['stock.move'].sudo()
        StockMoveLine = self.env['stock.move.line'].sudo()
        StockQuantPackage = self.env['stock.quant.package'].sudo()
        ProductProduct = self.env['product.product'].sudo()
        PurchaseOrder = self.env['purchase.order'].sudo()
        PurchaseOrderLine = self.env['purchase.order.line'].sudo()
        ResCompany = self.env['res.company'].sudo()
        
        # Step 1: Extract all data from content files and collect unique values
        content_data_list = []
        unique_product_codes = set()
        unique_po_codes = set()
        unique_ps_numbers = set()
        
        for content in content_files:
            data = {}
            for line in content.content_line_ids:
                data[line.name] = line.value
            
            ps_number = str(data.get('kode_ps', '')).replace(' ', '')
            po_md_code = str(data.get('kode_po_md', '')).replace(' ', '')
            product_code = str(data.get('kode_sparepart', '')).replace(' ', '')
            
            unique_product_codes.add(product_code)
            unique_po_codes.add(po_md_code)
            unique_ps_numbers.add(ps_number)
            
            content_data_list.append({
                'content': content,
                'data': data,
                'ps_number': ps_number,
                'po_md_code': po_md_code,
                'product_code': product_code,
                'ps_quantity': float(data.get('qty_ps', 0)),
                'box_number': str(data.get('kode_dus', '')).replace(' ', ''),
            })
        
        # Step 2: Batch fetch all required records (single query each)
        # Cache branch (same for all lines)
        default_md_code = self.env['res.company'].get_default_main_dealer_code()
        branch_obj = ResCompany.search([('code', '=', default_md_code)], limit=1)
        if not branch_obj:
            raise Warning(_(f'Branch {default_md_code} not found!'))
        
        # Cache picking type (same for all sparepart lines)
        picking_type_obj = StockPickingType.get_picking_type('incoming', branch_obj.id, 'Sparepart')
        
        # Batch fetch products
        products = ProductProduct.search([('default_code', 'in', list(unique_product_codes))])
        product_map = {p.default_code: p for p in products}
        
        # Batch fetch purchase orders (by origin first, then by partner_ref)
        po_by_origin = PurchaseOrder.search([('origin', 'in', list(unique_po_codes))])
        po_origin_map = {po.origin: po for po in po_by_origin}
        
        # Find missing POs by partner_ref
        missing_po_codes = unique_po_codes - set(po_origin_map.keys())
        if missing_po_codes:
            po_by_ref = PurchaseOrder.search([('partner_ref', 'in', list(missing_po_codes))])
            po_ref_map = {po.partner_ref: po for po in po_by_ref}
        else:
            po_ref_map = {}
        
        # Combine PO maps
        po_map = {**po_origin_map, **{k: v for k, v in po_ref_map.items() if k not in po_origin_map}}
        
        # Batch fetch existing pickings for these PS numbers
        existing_pickings = StockPicking.search([
            ('mft_reference', 'in', list(unique_ps_numbers)),
            ('state', '=', 'assigned')
        ])
        picking_by_mft_reference = {p.mft_reference: p for p in existing_pickings}
        
        # Step 3: Validate all data and prepare creation values
        # move_vals_by_picking: keyed by (ps_number, product_id) to prevent duplicate moves
        move_vals_by_picking = {}  # (ps_number, product_id, po_id) -> {move_vals, box_numbers, ...}
        pickings_to_create_by_ps = {}
        po_ids_by_ps = {}  # ps_number -> set of purchase_order_obj ids
        po_names_by_ps = {}  # ps_number -> set of purchase_order_obj names
        po_line_cache = {}  # (po_id, product_id) -> po_line
        
        for item in content_data_list:
            content = item['content']
            data = item['data']
            ps_number = item['ps_number']
            product_code = item['product_code']
            po_md_code = item['po_md_code']
            ps_quantity = item['ps_quantity']
            box_number = item['box_number']
            
            # Validate product
            product_obj = product_map.get(product_code)
            if not product_obj:
                raise Warning(_(f"Product {product_code} not found!\n Content line generation has been skipped."))
            
            # Validate PO
            purchase_order_obj = po_map.get(po_md_code)
            if not purchase_order_obj:
                if po_md_code.startswith('H2ZKPB') or po_md_code.startswith('G5ZKPB'):
                    purchase_order_type_obj = self.env['tw.purchase.order.type'].sudo().search([
                        ('name', '=', 'Additional'),
                        ('company_id', 'child_of', branch_obj.parent_id.id),
                        ('division', '=', 'Sparepart')
                    ], limit=1)
                    if not purchase_order_type_obj:
                        raise Warning(_(f"For PO {po_md_code}, Purchase Order Type 'Additional' not found for branch {branch_obj.name}!\n Content line generation has been skipped."))

                    purchase_order_obj = PurchaseOrder.search([('origin', '=', po_md_code)], limit=1)
                    if not purchase_order_obj:
                        purchase_order_obj = PurchaseOrder.with_company(branch_obj.id).create({
                            'company_id': branch_obj.id,
                            'origin': po_md_code,
                            'partner_ref': po_md_code,
                            'partner_id': branch_obj.default_supplier_id.id,
                            'date_order': datetime.now(),
                            'purchase_order_type_id': purchase_order_type_obj.id,
                            'picking_type_id': picking_type_obj.id,
                            'user_id': self._uid,
                            'start_date': datetime.now(),
                            'end_date': datetime.now() + relativedelta(months=1),
                            'division': 'Sparepart',
                            'state': 'draft',
                            'is_blank_po': True,
                        })
                else:
                    raise Warning(_(f"Purchase Order of Source Document/Vendor Reference '{po_md_code}' not found!\n Content line generation has been skipped."))

            is_blank_po = purchase_order_obj.is_blank_po

            # Get or cache PO line (only create/update if is_blank_po)
            po_line_key = (purchase_order_obj.id, product_obj.id)
            if po_line_key not in po_line_cache:
                po_line = PurchaseOrderLine.search([
                    ('order_id', '=', purchase_order_obj.id),
                    ('product_id', '=', product_obj.id)
                ], limit=1)
                if po_line:
                    # Update existing PO line quantity only for blank PO
                    if is_blank_po:
                        po_line.write({'product_qty': po_line.product_qty + ps_quantity})
                    po_line_cache[po_line_key] = po_line
                elif is_blank_po:
                    # Create PO line only for blank PO
                    po_line = PurchaseOrderLine.create({
                        'name': product_obj.name,
                        'product_id': product_obj.id,
                        'product_qty': ps_quantity,
                        'product_uom': product_obj.product_tmpl_id.uom_id.id,
                        'order_id': purchase_order_obj.id
                    })
                    po_line_cache[po_line_key] = po_line
                else:
                    raise Warning(_(f"Product {product_code} not registered in Purchase Order {purchase_order_obj.name}!\n Content line generation has been skipped."))
            else:
                # Update existing cached PO line quantity only for blank PO
                if is_blank_po:
                    po_line = po_line_cache[po_line_key]
                    po_line.write({'product_qty': po_line.product_qty + ps_quantity})
            
            purchase_line_obj = po_line_cache[po_line_key]
            
            # Store validated data for later batch creation
            item['product_obj'] = product_obj
            item['purchase_order_obj'] = purchase_order_obj
            item['purchase_line_obj'] = purchase_line_obj
            
            # Track all PO IDs per PS for later state confirmation
            po_ids_by_ps.setdefault(ps_number, set()).add(purchase_order_obj.id)
            po_names_by_ps.setdefault(ps_number, set()).add(purchase_order_obj.name)
            
            # Prepare picking vals if not exists
            if ps_number not in picking_by_mft_reference and ps_number not in pickings_to_create_by_ps:
                pickings_to_create_by_ps[ps_number] = {
                    'origin': purchase_order_obj.name,
                    'mft_reference': ps_number,
                    'picking_type_id': picking_type_obj.id,
                    'company_id': branch_obj.id,
                    'division': 'Sparepart',
                    'partner_id': branch_obj.default_supplier_id.id,
                    'date': datetime.now(),
                    'min_date': datetime.now(),
                    'location_id': picking_type_obj.default_location_src_id.id,
                    'location_dest_id': picking_type_obj.default_location_dest_id.id,
                    'purchase_order_id': purchase_order_obj.id,
                    'start_date': purchase_order_obj.start_date,
                    'end_date': purchase_order_obj.end_date,
                }
            
            # Group move vals by (ps_number, product_id, po_id) — one move per product per PO per picking
            move_key = (ps_number, product_obj.id, purchase_order_obj.id)
            if move_key not in move_vals_by_picking:
                move_vals_by_picking[move_key] = {
                    'content': content,
                    'ps_number': ps_number,
                    'move_vals': {
                        'picking_type_id': picking_type_obj.id,
                        'origin': ps_number,
                        'company_id': branch_obj.id,
                        'name': product_obj.default_code or '',
                        'product_uom': product_obj.product_tmpl_id.uom_id.id,
                        'product_id': product_obj.id,
                        'product_uom_qty': ps_quantity,
                        'date': datetime.now(),
                        'location_id': picking_type_obj.default_location_src_id.id,
                        'location_dest_id': picking_type_obj.default_location_dest_id.id,
                        'is_create_serial_number': False,
                        'purchase_line_id': purchase_line_obj.id,
                    },
                    # Track every box so Steps 6 & 7 can create one package/move_line per box
                    'boxes': [{'box_number': box_number, 'qty': ps_quantity, 'content': content}],
                    'product_obj': product_obj,
                    'purchase_line_obj': purchase_line_obj,
                }
            else:
                # Accumulate qty — multiple boxes of the same product → one move
                move_vals_by_picking[move_key]['move_vals']['product_uom_qty'] += ps_quantity
                move_vals_by_picking[move_key]['boxes'].append(
                    {'box_number': box_number, 'qty': ps_quantity, 'content': content}
                )
        
        # Step 4: Batch create pickings
        if pickings_to_create_by_ps:
            new_pickings = StockPicking.create(list(pickings_to_create_by_ps.values()))
            # Update ALL related PO states (not just the one on picking header)
            all_related_po_ids = set()
            for ps_number in pickings_to_create_by_ps:
                all_related_po_ids.update(po_ids_by_ps.get(ps_number, set()))
            if all_related_po_ids:
                PurchaseOrder.browse(list(all_related_po_ids)).write({'state': 'purchase'})
            # Add to picking map and update origin with all PO names
            for picking in new_pickings:
                picking_by_mft_reference[picking.mft_reference] = picking
                ps_po_names = po_names_by_ps.get(picking.mft_reference, set())
                if len(ps_po_names) > 1:
                    picking.write({'origin': ','.join(sorted(ps_po_names))})
        
        # Step 5: Batch create moves with picking_id — one move per (picking, product)
        all_move_vals = []
        move_metadata = []  # To track content, box_number, product for each move
        
        for (ps_number, _product_id, _po_id), item in move_vals_by_picking.items():
            picking = picking_by_mft_reference.get(ps_number)
            if not picking:
                continue
            
            move_vals = item['move_vals'].copy()
            move_vals['picking_id'] = picking.id
            all_move_vals.append(move_vals)
            move_metadata.append({
                'content': item['content'],
                'boxes': item['boxes'],     # all boxes: [{box_number, qty, content}, ...]
                'product_obj': item['product_obj'],
                'picking': picking,
                'purchase_line_obj': item['purchase_line_obj'],
            })
        
        created_moves = StockMove.create(all_move_vals)
        
        # Step 6: Batch create packages — one package per unique (box, picking, product)
        package_keys_to_create = {}  # (box_number, picking_id, product_id) -> vals
        
        for idx, move in enumerate(created_moves):
            meta = move_metadata[idx]
            picking = meta['picking']
            product_obj = meta['product_obj']
            
            for box in meta['boxes']:
                box_number = box['box_number']
                box_qty = box['qty']
                package_key = (box_number, picking.id, product_obj.id)
                if package_key not in package_keys_to_create:
                    package_keys_to_create[package_key] = {
                        'name': box_number,
                        'picking_id': picking.id,
                        'company_id': branch_obj.id,
                        'product_id': product_obj.id,
                        'quantity': box_qty,
                        'current_quantity': box_qty,
                    }
                else:
                    package_keys_to_create[package_key]['quantity'] += box_qty
                    package_keys_to_create[package_key]['current_quantity'] += box_qty
        
        # Check for existing packages
        existing_packages = StockQuantPackage.search([
            ('name', 'in', [k[0] for k in package_keys_to_create.keys()]),
            ('picking_id', 'in', [k[1] for k in package_keys_to_create.keys()]),
        ])
        existing_package_map = {(p.name, p.picking_id.id, p.product_id.id): p for p in existing_packages}
        
        # Filter out existing packages and create new ones
        packages_to_create = [
            vals for key, vals in package_keys_to_create.items()
            if key not in existing_package_map
        ]
        
        if packages_to_create:
            new_packages = StockQuantPackage.create(packages_to_create)
            for pkg in new_packages:
                existing_package_map[(pkg.name, pkg.picking_id.id, pkg.product_id.id)] = pkg
        
        # Step 7: Batch create move lines — one per box (package) per move
        move_line_vals = []
        for idx, move in enumerate(created_moves):
            meta = move_metadata[idx]
            picking = meta['picking']
            product_obj = meta['product_obj']
            
            for box in meta['boxes']:
                box_number = box['box_number']
                package_key = (box_number, picking.id, product_obj.id)
                package_obj = existing_package_map.get(package_key)
                
                move_line_vals.append({
                    'picking_id': picking.id,
                    'move_id': move.id,
                    'product_id': product_obj.id,
                    'company_id': branch_obj.id,
                    'location_id': picking_type_obj.default_location_src_id.id,
                    'location_dest_id': picking_type_obj.default_location_dest_id.id,
                    'result_package_id': package_obj.id if package_obj else False,
                    'quantity': box['qty'],
                    'quantity_product_uom': box['qty'],
                    'state': 'assigned',
                })
        
        StockMoveLine.create(move_line_vals)
        
        # Step 8: Batch update content states
        content_files.suspend_security().write({'state': 'done'})
        
        # Step 9: Confirm and assign pickings
        # Use direct state write instead of action_confirm() to avoid PO procurement
        # triggering duplicate moves via purchase.order.line._create_stock_moves()
        all_pickings = StockPicking.browse([p.id for p in picking_by_mft_reference.values()])
        if all_pickings:
            all_pickings.move_ids.write({'state': 'confirmed'})
            all_pickings.action_assign()
            all_pickings.mapped('move_ids_without_package').mapped('move_line_ids').sudo().write({'is_removeable': False})

    def _process_pmp(self):
        content_files = self.content_file_ids.filtered(lambda x: x.state == 'open')
        
        limit = self.config_id.limit
        if limit > 0:
            content_files = content_files[:limit]

        if not content_files:
            return
        
        product_to_create = []       # list of vals of product template to be created
        for content_file in content_files:
            vals_create = content_file._process_pmp(return_vals=True)
            if vals_create:
                product_to_create.append(vals_create)
        
        self.env['product.template'].create(product_to_create)
        
            
            