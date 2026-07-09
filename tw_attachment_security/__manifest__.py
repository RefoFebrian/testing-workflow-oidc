{
    "name": "Attachment Security (Upload Filtering & Safe Serving)",
    "summary": "Block dangerous uploads (HTML/SVG/JS/PDF with JS), size limits, and serve files safely.",
    
    'author': "Tunas Honda",
    'website': "http://www.honda-ku.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',
    "depends": ["base", "web"],
    "data": [],
    "installable": True,
    "application": False,
    "auto_install": False,
    "description": "Adds server-side upload validation for ir.attachment (mimetype allowlist, PDF JS detection, size limits). Forces safe headers and download for non-image types to reduce XSS risk.",
}
