Attachment Security (Odoo 10)
-----------------------------
Features:
- Blocks dangerous uploads at ir.attachment create/write:
  * HTML/SVG/JS/XML/SWF and other scriptable types
  * PDF with embedded JavaScript/actions (heuristic)
  * Size limit (25MB default)
  * Filename sanity
  * Mimetype sniffing using python-magic if available
- Serves files with safe headers and forces download for non-image types.

Install:
1) Copy this directory to your addons path.
2) (Optional) pip install python-magic
3) Update Apps list, install "Attachment Security (Upload Filtering & Safe Serving)".
4) Ensure this module loads after 'web'.

Notes:
- For PDFs, detection is heuristic. Consider adding ClamAV or a sanitizer pipeline.
- Adjust ALLOWED_MIME/BLOCKED_MIME and MAX_SIZE_BYTES in models/ir_attachment.py to your policy.
