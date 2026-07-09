
# -*- coding: utf-8 -*-
import base64
import re
from odoo import models, api, SUPERUSER_ID, _
from odoo.exceptions import ValidationError

try:
    import magic  # python-magic (libmagic)
except Exception:
    magic = None

# Patterns indicating active content in PDFs
PDF_JS_PATTERNS = [
    br'/JavaScript', br'/JS', br'/Launch', br'/RichMedia', br'/SubmitForm'
]
_JS_SIGNS = [
    br'/S\s*/JavaScript',            # explicit JS action
    br'/AA\s*<<[^>]*?/S\s*/JavaScript',  # additional actions with JS
    br'/OpenAction\s*<<[^>]*?/S\s*/JavaScript',  # OpenAction that runs JS
    br'/OpenAction\s*\[[^\]]*?/JavaScript',      # array form referencing JS
]

# Adjust allow/block lists to your policy
ALLOWED_MIME = set([
    'image/png','image/jpeg','image/gif','application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/plain'
    'text/css'
])

BLOCKED_MIME = set([
    'text/html','application/xhtml+xml','application/javascript','text/javascript',
    'image/svg+xml','text/xml','application/x-shockwave-flash'
])

MAX_SIZE_BYTES = 25 * 1024 * 1024  # 25MB default

def _sniff_mime(raw, fname):
    """Try content-based detection first, then fallback by extension."""
    if magic:
        try:
            m = magic.Magic(mime=True)
            return m.from_buffer(raw[:4096])
        except Exception:
            pass
    ext = (fname or '').lower().rsplit('.', 1)[-1] if '.' in (fname or '') else ''
    return {
        'png':'image/png','jpg':'image/jpeg','jpeg':'image/jpeg','gif':'image/gif',
        'pdf':'application/pdf','txt':'text/plain',
        'docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xlsx':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    }.get(ext, 'application/octet-stream')

def _pdf_contains_active_js(raw):
    head = raw[:10*1024*1024]
    # quick wins
    if re.search(br'/JavaScript|/JS\b', head):
        return True
    # action dictionaries
    for pat in _JS_SIGNS:
        if re.search(pat, head, re.DOTALL):
            return True
    # treat Launch/RichMedia/SubmitForm as risky
    if re.search(br'/Launch|/RichMedia|/SubmitForm', head):
        return True
    return False

class IrAttachment(models.Model):
    _inherit = "ir.attachment"
    
    def _uploader_is_superuser(self):
        return self.env.uid == SUPERUSER_ID

    def _validate_payload(self, vals):
        raw = vals.get('raw')
        fname = vals.get('datas_fname') or vals.get('name') or ''
        if not raw:
            return

        # size
        if len(raw) > MAX_SIZE_BYTES:
            raise ValidationError(_("File too large (limit %s MB).") % (MAX_SIZE_BYTES // (1024*1024)))

        # filename sanity
        if fname and any(x in fname for x in ['..','/','\\','%00']):
            raise ValidationError(_("Invalid filename."))

        mime = _sniff_mime(raw, fname)

        # strict blocklist
        if mime in BLOCKED_MIME:
            if not self._uploader_is_superuser():
                raise ValidationError(_("This file type is not allowed (security policy)."))

        # (optional) allow-list enforcement
        if ALLOWED_MIME and mime not in ALLOWED_MIME:
            if not self._uploader_is_superuser():
                raise ValidationError(_("This file type is not permitted."))

        # special PDF hygiene
        if mime == 'application/pdf' and _pdf_contains_active_js(raw):
            raise ValidationError(_("PDF rejected: embedded JavaScript/actions detected."))

        # persist detected mimetype for later serving logic
        vals['mimetype'] = mime

    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._validate_payload(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._validate_payload(vals)
        return super().write(vals)
