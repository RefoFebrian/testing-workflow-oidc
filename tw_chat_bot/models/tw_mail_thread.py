# -*- coding: utf-8 -*-

# 1: imports of python lib
import time
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib
from markupsafe import Markup

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib
import requests
import json

class TwMailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _get_message_create_valid_field_names(self):
        valid_field = super()._get_message_create_valid_field_names()
        valid_field.update({
            'chatbot_message_id',
            'chatbot_conversation_id',
            'chatbot_space_id'
            }) 
        return valid_field