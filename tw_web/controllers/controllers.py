# -*- coding: utf-8 -*-

# 1: imports of python lib
import base64
import json
import mimetypes

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import http

# 4:  imports from odoo modules
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.tools import file_open
from odoo.addons.web.controllers.webmanifest import WebManifest as WebManifest

# 5: local imports

# 6: Import of unknown third party lib


class InheritWebManifest(WebManifest):

    def _icon_path(self):
        return 'tw_web/static/img/teds2-icon-192x192.png'

    @http.route('/web/offline', type='http', auth='public', methods=['GET'])
    def offline(self):
        """ Returns the offline page delivered by the service worker """
        return request.render('tw_web.webclient_offline_teds2', {
            'odoo_icon': base64.b64encode(file_open(self._icon_path(), 'rb').read())
        })
