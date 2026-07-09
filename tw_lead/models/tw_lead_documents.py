# -*- coding: utf-8 -*-

# 1: imports of python lib
import base64

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class LeadDocuments(models.Model):
    _name = "tw.lead.documents"
    _description = "Lead Documents"

    # 7: defaults methods
    
    # 8: fields
    name = fields.Char('Document Number', compute='_compute_name', store=True)
    lead_id = fields.Many2one('tw.lead')
    document_filename = fields.Char()
    document_file = fields.Binary(
        string='Document File',
        compute='_compute_document_file',
        inverse='_inverse_document_file',
    )
    document_file_temp = fields.Binary(
        help="Temporary field to hold uploaded binary before processing",
        attachment=False,
    )
    document_show = fields.Binary(string='Document', compute='_compute_document')
    upload_date = fields.Datetime('Upload Date', default=fields.Datetime.now)
    
    # 9: relation fields
    document_type_id = fields.Many2one(comodel_name='tw.selection', string="Document Type", domain="[('type', '=', 'DocumentType')]")
    
    # 10: constraints & sql constraints
    ALLOWED_EXTENSIONS = ('pdf', 'jpeg', 'jpg', 'png')
    MAX_FILE_SIZE_KB = 500

    # 11: compute/depends & on change methods
    def _compute_document_file(self):
        """Compute document_file by fetching the file from external storage."""
        for doc in self:
            if doc.document_filename:
                doc.document_file = doc.env['tw.config.files'].suspend_security().get_file(doc.document_filename)
            else:
                doc.document_file = False

    def _inverse_document_file(self):
        """Inverse method: store the uploaded binary into the temp field for processing."""
        for doc in self:
            if doc.document_file:
                doc.document_file_temp = doc.document_file

    def _compute_document(self):
        """ Display the documents using stored path"""
        for doc in self:
            if doc.document_filename:
                doc.document_show = doc.env['tw.config.files'].suspend_security().get_file(doc.document_filename)
            else:
                doc.document_show = False

    @api.depends('lead_id.company_id')
    def _compute_name(self):
        for doc in self:
            if doc.id:
                code = doc.lead_id.company_id.code
                prefix = 'LEADS-DOC'
                doc.name = doc.env['ir.sequence'].get_sequence_code(code, prefix)
            else:
                doc.name = False

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._process_document_file(vals)
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('document_file'):
            # When writing via One2many Command.update, document_file comes
            # through the inverse, but when vals are passed directly we need
            # to process them here.
            for rec in self:
                rec_vals = dict(vals)
                # Populate lead_id and document_type_id from the record when
                # they are not explicitly provided in the vals dict.
                if 'lead_id' not in rec_vals:
                    rec_vals['lead_id'] = rec.lead_id.id
                if 'document_type_id' not in rec_vals:
                    rec_vals['document_type_id'] = rec.document_type_id.id
                self._process_document_file(rec_vals)
                super(LeadDocuments, rec).write(rec_vals)
            return True
        return super().write(vals)

    # 13: action methods

    # 14: private methods
    def _process_document_file(self, vals):
        """Process document file: validate extension/size and upload to
        external storage.  Modifies *vals* in place – pops the binary data
        and sets the canonical ``document_filename``.
        """
        file_bin = vals.get('document_file')
        if not file_bin:
            return

        filename = vals.get('document_filename', '')
        self._check_file_validity(file_bin, filename)

        ext = filename.split('.')[-1] if filename else 'bin'

        # Pop the binary so it is NOT persisted in the DB column
        vals.pop('document_file', None)

        selection = self.env['tw.selection']
        config = self.env['tw.config.files']

        document_type_id = vals.get('document_type_id')
        document_type = selection.browse(document_type_id)
        lead_id = vals.get('lead_id')

        canonical_filename = f"tw_lead-{document_type.value}-{lead_id}.{ext}"
        config.suspend_security().upload_file(canonical_filename, file_bin)
        vals['document_filename'] = canonical_filename
        vals['upload_date'] = fields.Datetime.now()

    @staticmethod
    def _check_file_validity(file_bin, filename):
        """Validate document file extension and size.
        
        Allowed extensions: PDF, JPEG, JPG, PNG
        Maximum file size: 500Kb
        """
        if not filename:
            return
        
        # Check extension
        ext = filename.split('.')[-1].lower()
        if ext not in LeadDocuments.ALLOWED_EXTENSIONS:
            raise Warning(
                "Extension file '%s' tidak diperbolehkan.\n"
                "Hanya file PDF dan gambar (JPEG, JPG, PNG) yang diizinkan." % ext
            )
        
        # Check file size (base64 decoded)
        if file_bin:
            try:
                if isinstance(file_bin, str):
                    file_data = base64.b64decode(file_bin)
                elif isinstance(file_bin, bytes):
                    try:
                        file_data = base64.b64decode(file_bin, validate=True)
                    except Exception:
                        file_data = file_bin
                else:
                    file_data = file_bin
                file_size_kb = len(file_data) / 1024
                if file_size_kb > LeadDocuments.MAX_FILE_SIZE_KB:
                    raise Warning(
                        "Ukuran file '%.1f Kb' melebihi batas maksimal %d Kb. "
                        "Silakan kompres atau gunakan file yang lebih kecil."
                        % (file_size_kb, LeadDocuments.MAX_FILE_SIZE_KB)
                    )
            except Warning:
                raise
            except Exception:
                pass
