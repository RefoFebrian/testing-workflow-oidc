from odoo import api, fields, models, _
from odoo.exceptions import UserError
import base64
import logging

_logger = logging.getLogger(__name__)

try:
    from google.api_core.client_options import ClientOptions
    from google.oauth2 import service_account
    from google.cloud import documentai
except ImportError:
    _logger.warning("google-cloud-documentai is not installed")


class TwPaymentOcrWizard(models.TransientModel):
    _name = "tw.payment.ocr.wizard"
    _description = "Wizard to upload and Process Customer Payment via OCR"

    file_data = fields.Binary(string='Upload Payment Document', required=True)
    file_name = fields.Char(string='Filename')

    def action_process_ocr(self):
        """
        Process the uploaded file using Google Cloud Document AI
        """
        self.ensure_one()
        if not self.file_data:
            raise UserError(_("Please upload a document to process."))

        # This should ideally come from configuration parameters
        # ir.config_parameter.sudo().get_param('tw_payment_ocr.project_id')
        project_id = self.env['ir.config_parameter'].sudo().get_param('tw_payment_ocr.project_id')
        location = self.env['ir.config_parameter'].sudo().get_param('tw_payment_ocr.location', 'us')
        processor_id = self.env['ir.config_parameter'].sudo().get_param('tw_payment_ocr.processor_id')
        credentials_path = self.env['ir.config_parameter'].sudo().get_param('tw_payment_ocr.credentials_path')

        if not project_id or not processor_id:
            # We will raise an error if not configured, but for safety in dev we can try/except or mock
            raise UserError(_("Google Cloud Document AI is not configured. Please set the Project ID and Processor ID in the system parameters."))

        try:
            # Parse the document using Document AI
            document = self._process_document(
                project_id=project_id,
                location=location,
                processor_id=processor_id,
                credentials_path=credentials_path,
                file_content=base64.b64decode(self.file_data),
                mime_type=self._get_mime_type(self.file_name)
            )

            # Extract entities (e.g., amount, partner_name, date)
            extracted_data = self._extract_entities(document)

            # Create a draft Customer Payment based on the extracted data
            payment = self._create_customer_payment(extracted_data)

            # Return action to open the newly created payment
            form_id = self.env.ref('tw_payment.tw_account_payment_form_view').id
            return {
                'type': 'ir.actions.act_window',
                'name': ('Supplier Payment'),
                'target': 'current',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'tw.account.payment',
                'res_id': payment.id,
                'views': [(form_id, 'form')]
            }

        except Exception as e:
            _logger.exception("Error processing OCR document: %s", str(e))
            raise UserError(_("Failed to process document through OCR: %s") % str(e))

    def _get_mime_type(self, filename):
        if not filename:
            return 'application/pdf'
        filename = filename.lower()
        if filename.endswith('.pdf'):
            return 'application/pdf'
        elif filename.endswith(('.png', '.jpg', '.jpeg')):
            # Note: Document AI supports images as well, but typical use case is PDF
            if filename.endswith('.png'):
                return 'image/png'
            return 'image/jpeg'
        return 'application/pdf'

    def _process_document(self, project_id, location, processor_id, credentials_path, file_content, mime_type):
        """
        Calls Google Cloud Document AI API to process the document
        """
        opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
        
        credentials = None
        if credentials_path:
            try:
                credentials = service_account.Credentials.from_service_account_file(credentials_path)
            except Exception as e:
                _logger.error("Failed to load credentials from %s: %s", credentials_path, str(e))
                raise UserError(_("Failed to load Google Cloud credentials: /n%s") % str(e))
                
        client = documentai.DocumentProcessorServiceClient(client_options=opts, credentials=credentials)
        
        name = client.processor_path(project_id, location, processor_id)
        
        raw_document = documentai.RawDocument(content=file_content, mime_type=mime_type)
        request = documentai.ProcessRequest(name=name, raw_document=raw_document)
        
        result = client.process_document(request=request)
        return result.document

    def _extract_entities(self, document):
        """
        Extract entities from the Document AI result structure.
        This depends on the specific processor type (Invoice Parser, Receipt Parser, Custom etc.).
        We will extract basic fields assuming Invoice/Receipt parser for now.
        """
        data = {
            'amount': 0.0,
            'partner_name': '',
            'date': False,
            'invoice_id': '',
        }
        
        for entity in document.entities:
            # Typical keys in Document AI pre-trained parsers
            if entity.type_ in ('total_amount', 'net_amount'):
                val = 0.0
                if hasattr(entity, 'normalized_value') and hasattr(entity.normalized_value, 'float_value') and entity.normalized_value.float_value:
                    val = entity.normalized_value.float_value
                else:
                    try:
                        # Clean up currency symbols and whitespace
                        val_str = entity.mention_text.replace('Rp', '').replace('IDR', '').strip()
                        # Handle Indonesian thousand separators (e.g. 287.646 -> 287646)
                        if '.' in val_str and ',' not in val_str:
                            parts = val_str.split('.')
                            if len(parts[-1]) == 3:
                                val_str = val_str.replace('.', '')
                        elif ',' in val_str and '.' in val_str:
                            val_str = val_str.replace('.', '').replace(',', '.')
                        else:
                            val_str = val_str.replace(',', '')
                        val = float(val_str)
                    except ValueError:
                        pass
                
                if val:
                    if entity.type_ == 'total_amount':
                        data['amount'] = val
                    elif not data['amount']:
                        data['amount'] = val
            elif entity.type_ == 'supplier_name' or entity.type_ == 'receiver_name' or 'name' in entity.type_:
                if not data['partner_name']:
                    data['partner_name'] = entity.mention_text
            elif entity.type_ == 'invoice_date' or entity.type_ == 'receipt_date' or 'date' in entity.type_:
                data['date'] = entity.mention_text
            elif entity.type_ == 'invoice_id':
                data['invoice_id'] = entity.mention_text

        return data

    def _create_customer_payment(self, extracted_data):
        """
        Creates a draft tw.account.payment (Customer Payment type) using the OCR data
        """
        # Attempt to find partner
        partner_id = False
        if extracted_data.get('partner_name'):
            # clean up newlines from partner_name (e.g. "intel\nCORE" -> "intel CORE")
            clean_partner_name = extracted_data['partner_name'].replace('\n', ' ').strip()
            partner = self.env['res.partner'].search([
                ('name', 'ilike', clean_partner_name),
                ('is_company', '=', True)
            ], limit=1)
            if not partner:
                partner = self.env['res.partner'].search([
                    ('name', 'ilike', clean_partner_name)
                ], limit=1)
            partner_id = partner.id if partner else False

        # Determine default Journal (Bank/Cash)
        journal = self.env['account.journal'].search([('type', 'in', ['bank', 'cash']), ('company_id', '=', self.env.company.id)], limit=1)
        
        # Determine default Payment Method
        payment_method = self.env['account.payment.method'].search([('payment_type', '=', 'inbound')], limit=1)

        # Get default Payment Method Line
        payment_method_line = False
        if journal and payment_method:
            payment_method_line = self.env['account.payment.method.line'].search([
                ('journal_id', '=', journal.id),
                ('payment_method_id', '=', payment_method.id)
            ], limit=1)

        # Search for outstanding invoice based on invoice_id
        move_line_id = False
        account_id = False
        amount_unreconciled = 0.0

        if extracted_data.get('invoice_id'):
            # Looking for an unreconciled receivable line
            base_domain = [
                ('account_id.account_type', '=', 'asset_receivable'),
                ('full_reconcile_id', '=', False),
                ('parent_state', '=', 'posted'),
                ('company_id', '=', self.env.company.id)
            ]
            
            # 1. Exact match
            aml = self.env['account.move.line'].search(base_domain + [('move_id.name', '=', extracted_data['invoice_id'])], limit=1)
            
            # 2. Fuzzy match
            if not aml:
                fuzzy_name = extracted_data['invoice_id'].replace(' ', '%')
                aml = self.env['account.move.line'].search(base_domain + [('move_id.name', 'ilike', fuzzy_name)], limit=1)
            
            if aml:
                move_line_id = aml.id
                account_id = aml.account_id.id
                amount_unreconciled = abs(aml.amount_residual)
                if not partner_id:
                    partner_id = aml.partner_id.id
                if not extracted_data.get('amount') or extracted_data.get('amount') == 0.0:
                    extracted_data['amount'] = float(amount_unreconciled)

        payment_vals = {
            'type': 'customer_payment',
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': partner_id,
            'amount': extracted_data.get('amount', 0.0),
            'memo': f"OCR Import from {self.file_name}",
            'state': 'draft',
            'company_id': self.env.company.id,
        }
        
        # Get division from context if available
        division = self.env.context.get('default_division') or self.env.context.get('division')
        if division:
            payment_vals['division'] = division

        if journal:
            payment_vals['journal_id'] = journal.id
        if payment_method_line:
            payment_vals['payment_method_line_id'] = payment_method_line.id
            
        if move_line_id and account_id:
            allocate_amount = min(extracted_data.get('amount', amount_unreconciled), amount_unreconciled)
            payment_vals['line_cr_ids'] = [(0, 0, {
                'type': 'cr',
                'move_line_id': move_line_id,
                'account_id': account_id,
                'amount_unreconciled': amount_unreconciled,
                'amount': allocate_amount,
                'is_reconciled': allocate_amount == amount_unreconciled,
            })]
        elif extracted_data.get('invoice_id'):
            # Fallback: if we didn't find the exact invoice in Odoo, still create a credit line 
            # with the document name (invoice_id) so the user doesn't have an empty list.
            
            # Find a default receivable account to use
            if partner_id:
                partner = self.env['res.partner'].browse(partner_id)
                fallback_account_id = partner.property_account_receivable_id.id
            else:
                fallback_account = self.env['account.account'].search([
                    ('account_type', '=', 'asset_receivable'), 
                    ('company_id', '=', self.env.company.id)
                ], limit=1)
                fallback_account_id = fallback_account.id if fallback_account else False
                
            if fallback_account_id:
                payment_vals['line_cr_ids'] = [(0, 0, {
                    'type': 'cr',
                    'name': extracted_data['invoice_id'],
                    'account_id': fallback_account_id,
                    'amount_unreconciled': extracted_data.get('amount', 0.0),
                    'amount': extracted_data.get('amount', 0.0),
                    'is_reconciled': False,
                })]

        
        # Odoo 18 date parsing logic could be added here if extracted_data['date'] is valid
        # For safety, defaulting to today if parsing tricky
        
        payment = self.env['tw.account.payment'].create(payment_vals)
        
        # Attach the original file to the newly created payment
        self.env['ir.attachment'].create({
            'name': self.file_name or 'Uploaded Payment Document',
            'type': 'binary',
            'datas': self.file_data,
            'res_model': 'tw.account.payment',
            'res_id': payment.id,
        })
        
        return payment
