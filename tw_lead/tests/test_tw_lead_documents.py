# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError
import base64


@tagged('post_install', '-at_install', 'tw_lead')
class TestTwLeadDocuments(TransactionCase):
    """Test cases for tw.lead.documents model"""

    @classmethod
    def setUpClass(cls):
        super(TestTwLeadDocuments, cls).setUpClass()
        
        cls.Lead = cls.env['tw.lead']
        cls.LeadDocument = cls.env['tw.lead.documents']
        cls.Selection = cls.env['tw.selection']
        cls.Company = cls.env['res.company']
        
        # Create test company
        cls.test_company = cls.env['res.company'].search([('parent_id', '!=', False)], limit=1)
        if not cls.test_company:
            parent_company = cls.env['res.company'].search([], limit=1)
            cls.test_company = cls.Company.create({
                'name': 'Test Branch',
                'parent_id': parent_company.id,
                'code': 'TBR'
            })
        
        # Get or create document type selections
        cls.doc_type_ktp = cls.Selection.search([('type', '=', 'DocumentType'), ('value', '=', 'ktp')], limit=1)
        if not cls.doc_type_ktp:
            cls.doc_type_ktp = cls.Selection.create({'name': 'KTP', 'value': 'ktp', 'type': 'DocumentType'})
        
        cls.doc_type_kk = cls.Selection.search([('type', '=', 'DocumentType'), ('value', '=', 'kk')], limit=1)
        if not cls.doc_type_kk:
            cls.doc_type_kk = cls.Selection.create({'name': 'KK', 'value': 'kk', 'type': 'DocumentType'})
        
        cls.doc_type_slip_gaji = cls.Selection.search([('type', '=', 'DocumentType'), ('value', '=', 'slip_gaji')], limit=1)
        if not cls.doc_type_slip_gaji:
            cls.doc_type_slip_gaji = cls.Selection.create({'name': 'Slip Gaji', 'value': 'slip_gaji', 'type': 'DocumentType'})
        
        # Get or create other necessary selections
        cls.interest_cold = cls.Selection.search([('type', '=', 'Interest'), ('value', '=', 'cold')], limit=1)
        if not cls.interest_cold:
            cls.interest_cold = cls.Selection.create({'name': 'Cold', 'value': 'cold', 'type': 'Interest'})
        
        cls.data_source = cls.Selection.search([('type', '=', 'DataSource'), ('value', '=', 'web')], limit=1)
        if not cls.data_source:
            cls.data_source = cls.Selection.create({'name': 'Web', 'value': 'web', 'type': 'DataSource'})
        
        # Create test lead
        cls.test_lead = cls.Lead.create({
            'customer_name': 'Test Customer for Documents',
            'mobile': '081234567890',
            'identification_number': '1234567890123456',
            'company_id': cls.test_company.id,
            'interest_id': cls.interest_cold.id,
            'data_source_id': cls.data_source.id,
        })
        
        # Create test file content (simple PDF-like binary)
        cls.test_file_content = base64.b64encode(b'Test PDF content')

    def test_01_create_document_basic(self):
        """Test basic document creation without file"""
        document = self.LeadDocument.create({
            'lead_id': self.test_lead.id,
            'document_type_id': self.doc_type_ktp.id,
        })
        
        self.assertTrue(document.id, "Document should be created")
        self.assertTrue(document.upload_date, "Upload date should be set")

    def test_02_document_name_generation(self):
        """Test that document name is auto-generated"""
        document = self.LeadDocument.create({
            'lead_id': self.test_lead.id,
            'document_type_id': self.doc_type_ktp.id,
        })
        
        # Force compute
        document._compute_name()
        
        self.assertTrue(document.name, "Name should be generated")
        if document.name:
            self.assertIn('LEADS-DOC', document.name, "Name should contain LEADS-DOC code")

    def test_03_create_document_with_file(self):
        """Test document creation with file upload"""
        document = self.LeadDocument.create({
            'lead_id': self.test_lead.id,
            'document_type_id': self.doc_type_ktp.id,
            'document_file': self.test_file_content,
            'document_filename': 'test_ktp.pdf',
        })
        
        self.assertTrue(document.id, "Document with file should be created")
        self.assertTrue(document.document_filename, "Filename should be stored")

    def test_04_filename_generated_from_type(self):
        """Test that filename is generated based on document type and lead"""
        document = self.LeadDocument.create({
            'lead_id': self.test_lead.id,
            'document_type_id': self.doc_type_ktp.id,
            'document_file': self.test_file_content,
            'document_filename': 'original_name.pdf',
        })
        
        # Filename should be transformed to: tw_lead-{type}-{lead_id}.pdf
        expected_pattern = f'tw_lead-ktp-{self.test_lead.id}.pdf'
        self.assertEqual(
            document.document_filename,
            expected_pattern,
            "Filename should follow naming convention"
        )

    def test_05_multiple_documents_per_lead(self):
        """Test that multiple documents can be attached to a lead"""
        doc1 = self.LeadDocument.create({
            'lead_id': self.test_lead.id,
            'document_type_id': self.doc_type_ktp.id,
        })
        
        doc2 = self.LeadDocument.create({
            'lead_id': self.test_lead.id,
            'document_type_id': self.doc_type_kk.id,
        })
        
        doc3 = self.LeadDocument.create({
            'lead_id': self.test_lead.id,
            'document_type_id': self.doc_type_slip_gaji.id,
        })
        
        self.assertEqual(len(self.test_lead.document_ids), 3, "Should have 3 documents")

    def test_06_lead_relationship(self):
        """Test relationship between document and lead"""
        document = self.LeadDocument.create({
            'lead_id': self.test_lead.id,
            'document_type_id': self.doc_type_ktp.id,
        })
        
        self.assertEqual(document.lead_id.id, self.test_lead.id)
        self.assertIn(document, self.test_lead.document_ids)

    def test_07_upload_date_automatic(self):
        """Test that upload date is automatically set"""
        before_create = datetime.now().replace(microsecond=0)
        
        document = self.LeadDocument.create({
            'lead_id': self.test_lead.id,
            'document_type_id': self.doc_type_ktp.id,
        })
        
        after_create = datetime.now().replace(microsecond=0) + timedelta(seconds=1)
        
        self.assertTrue(document.upload_date, "Upload date should be set")
        # Compare without microseconds for reliability
        doc_date = document.upload_date.replace(microsecond=0)
        self.assertGreaterEqual(doc_date, before_create)
        self.assertLessEqual(doc_date, after_create)

    def test_08_document_type_relationship(self):
        """Test document type selection relationship"""
        document = self.LeadDocument.create({
            'lead_id': self.test_lead.id,
            'document_type_id': self.doc_type_ktp.id,
        })
        
        self.assertEqual(document.document_type_id.id, self.doc_type_ktp.id)
        self.assertEqual(document.document_type_id.value, 'ktp')

    def test_09_different_file_extensions(self):
        """Test handling different file extensions"""
        extensions = ['pdf', 'jpg', 'png', 'jpeg']
        
        for ext in extensions:
            document = self.LeadDocument.create({
                'lead_id': self.test_lead.id,
                'document_type_id': self.doc_type_ktp.id,
                'document_file': self.test_file_content,
                'document_filename': f'test_file.{ext}',
            })
            
            self.assertTrue(
                document.document_filename.endswith(f'.{ext}'),
                f"Should preserve {ext} extension"
            )

    def test_10_compute_document_display(self):
        """Test document display computation"""
        document = self.LeadDocument.create({
            'lead_id': self.test_lead.id,
            'document_type_id': self.doc_type_ktp.id,
            'document_file': self.test_file_content,
            'document_filename': 'test.pdf',
        })
        
        # The _compute_document method should retrieve the file
        # This test verifies the method exists and can be called
        document._compute_document()
        
        # Note: Actual file retrieval depends on tw.config.files implementation

    def test_11_document_without_filename(self):
        """Test document behavior when no file is uploaded"""
        document = self.LeadDocument.create({
            'lead_id': self.test_lead.id,
            'document_type_id': self.doc_type_kk.id,
        })
        
        document._compute_document()
        
        self.assertFalse(document.document_show, "Should not show document if no file")

    def test_12_multiple_same_type_documents(self):
        """Test that multiple documents of the same type can be created"""
        # Note: In the original code, filename includes lead_id, so same type
        # documents would overwrite. This test documents current behavior.
        
        doc1 = self.LeadDocument.create({
            'lead_id': self.test_lead.id,
            'document_type_id': self.doc_type_ktp.id,
            'document_file': self.test_file_content,
            'document_filename': 'ktp1.pdf',
        })
        
        doc2 = self.LeadDocument.create({
            'lead_id': self.test_lead.id,
            'document_type_id': self.doc_type_ktp.id,
            'document_file': self.test_file_content,
            'document_filename': 'ktp2.pdf',
        })
        
        # Both will have same generated filename, so file might be overwritten
        # But records should both exist
        self.assertTrue(doc1.id and doc2.id, "Both documents should exist as records")
