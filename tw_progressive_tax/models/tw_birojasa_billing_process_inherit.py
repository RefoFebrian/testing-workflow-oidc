# -*- coding: utf-8 -*-

# 1: imports of python lib
import difflib
import json
import os
import logging
import re

# 2: import of known third party lib
from datetime import date, timedelta, datetime

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib
class TwBirojasaBillingProcessInherit(models.Model):
    _inherit = "tw.birojasa.billing.process"

    def _get_journals_and_accounts(self, account_setting):
        journal_birojasa, journal_progressive, bbn_debit_acc, bbn_credit_acc = super()._get_journals_and_accounts(account_setting)

        journal_progressive = account_setting.journal_birojasa_progressive_id
        if not journal_progressive:
            raise Warning(_('Journal Pajak Progressive belum diisi, harap isi terlebih dahulu di Account Setting untuk branch %s')
                        % self.company_id.name)


        return journal_birojasa, journal_progressive, bbn_debit_acc, bbn_credit_acc

