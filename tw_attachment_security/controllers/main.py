
# -*- coding: utf-8 -*-
from odoo import http, SUPERUSER_ID
from odoo.http import request
from odoo.addons.web.controllers.binary import Binary

# Which mimetypes may be displayed inline (others forced to download)
INLINE_OK = set(['image/png','image/jpeg','image/gif'])

class BinarySafe(Binary):
    # Override content route to apply safe headers and (optionally) force download
    @http.route(['/web/content',
                    '/web/content/<string:id>',
                    '/web/content/<string:id>/<string:filename>',
                    '/web/content/<string:id>-<string:unique>',
                    '/web/content/<string:id>-<string:unique>/<string:filename>'],
                type='http', auth="public")
    def content(self, **kwargs):
        res = super(BinarySafe, self).content(**kwargs)
        try:
            # Always add defensive headers
            res.headers['X-Content-Type-Options'] = 'nosniff'
            res.headers['Referrer-Policy'] = 'no-referrer'
            # Sandbox & no JS; helpful for inline viewers
            # (Note: may be ignored by some browsers for downloads)
            res.headers['Content-Security-Policy'] = "default-src 'none'; sandbox"
            ct = res.headers.get('Content-Type', '').split(';')[0].strip().lower()
            # Force download for non-image files to reduce XSS via inline rendering
            if ct not in INLINE_OK and 'Content-Disposition' in res.headers and 'attachment' not in res.headers['Content-Disposition']:
                # try to fetch filename
                filename = 'file'
                att_id = kwargs.get('id')
                if att_id and att_id.isdigit():
                    att = request.registry['ir.attachment'].browse(request.cr, SUPERUSER_ID, int(att_id), context=request.context)
                    filename = att.datas_fname or att.name or filename
                res.headers['Content-Disposition'] = 'attachment; filename="%s"' % filename.encode('utf-8')
        except Exception:
            # Don't break the file response if header manipulation fails
            return res
        return res
