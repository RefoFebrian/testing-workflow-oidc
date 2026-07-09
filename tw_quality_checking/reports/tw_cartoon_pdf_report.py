import datetime
import pytz
import logging
import base64
from odoo import models, api, _

_logger = logging.getLogger(__name__)


class CartoonPdfReport(models.AbstractModel):
    _name = "report.tw_quality_checking.cartoon_pdf_report"
    _description = "CARTOON PDF Report"

    def time_date(self, date):
        """Mendapatkan waktu cetak dalam format lokal."""
        user = self.env.user
        now_utc = datetime.datetime.now(pytz.utc)
        tz = pytz.timezone(user.tz) if user.tz else pytz.utc
        now_local = now_utc.astimezone(tz)
        return now_local.strftime("%d-%m-%Y %H:%M")

    def print_user(self):
        """Mendapatkan nama user yang mencetak."""
        return self.env['res.users'].suspend_security().browse(self.env.uid).name

    @api.model
    def _get_report_values(self, docids, data=None):
        """Menyediakan values untuk report CARTOON PDF."""
        docs = self.env['tw.quality.checking'].browse(docids)
        
        # Simpan PDF untuk setiap document yang sudah done
        for doc in docs:
            if doc.state == 'done' and not doc.filename:
                self._save_cartoon_pdf_for_doc(doc)

        return {
            'doc_ids': docids,
            'doc_model': 'tw.quality.checking',
            'docs': docs,
            'time_date': self.time_date,
            'print_user': self.print_user,
        }

    def _save_cartoon_pdf_for_doc(self, doc):
        """Simpan PDF ke file storage dan update filename field."""
        try:
            filename = f"CARTOON_{doc.name.replace('/', '_')}.pdf"
            # Set filename dulu, PDF content akan di-generate oleh proses print
            doc.sudo().write({'filename': filename})
            _logger.info(f"CARTOON PDF filename set: {filename} for doc {doc.id}")
        except Exception as e:
            _logger.error(f"Error saving CARTOON PDF: {e}")


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        """Override untuk menyimpan CARTOON PDF setelah render."""
        result = super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)
        
        # Cek apakah ini CARTOON Report
        try:
            if isinstance(report_ref, str):
                report = self._get_report_from_name(report_ref)
            else:
                report = self.browse(report_ref)
            
            _logger.info(f"Report rendered: {report.report_name if report else 'None'}, res_ids: {res_ids}")
            
            if report and report.report_name == 'tw_quality_checking.cartoon_pdf_report' and res_ids:
                pdf_content = result[0]
                self._save_cartoon_pdf_to_storage(res_ids, pdf_content)
        except Exception as e:
            _logger.error(f"Error in _render_qweb_pdf override: {e}")
        
        return result

    def _save_cartoon_pdf_to_storage(self, res_ids, pdf_content):
        try:
            for doc_id in res_ids:
                doc = self.env['tw.quality.checking'].sudo().browse(doc_id)
                if doc.exists() and doc.state == 'done':
                    filename = f"CARTOON_{doc.name.replace('/', '_')}.pdf"
                    _logger.info(f"Saving CARTOON PDF: {filename}")
                    pdf_base64 = base64.b64encode(pdf_content)
                    self.env['tw.config.files'].suspend_security().upload_file(filename, pdf_base64)
                    doc.write({'filename': filename})
                    _logger.info(f"CARTOON PDF saved successfully: {filename}")
        except Exception as e:
            _logger.error(f"Error saving CARTOON PDF to storage: {e}")
