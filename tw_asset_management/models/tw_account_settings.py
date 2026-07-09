# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _


class TwAccountSettings(models.Model):
    _inherit = "tw.account.setting"
 
    journal_good_receive_asset_id = fields.Many2one('account.journal',string="Journal Good Receive Asset",domain="[('type','!=','view')]",help="Journal ini dibutuhkan saat proses Good Receive Asset.")
    journal_good_receive_prepaid_id = fields.Many2one('account.journal',string="Journal Good Receive Prepaid",domain="[('type','!=','view')]",help="Journal ini dibutuhkan saat proses Good Receive Prepaid.")
    journal_good_receive_cip_id = fields.Many2one('account.journal',string="Journal Good Receive CIP",domain="[('type','!=','view')]",help="Journal ini dibutuhkan saat proses Good Receive CIP.")
    journal_good_receive_asset_collecting_id = fields.Many2one('account.journal',string="Journal Good Receive Collecting",domain="[('type','!=','view')]",help="Journal ini dibutuhkan saat proses Good Receive Collecting.")
    journal_acquisition_asset_id = fields.Many2one('account.journal',string="Journal Akuisisi Asset",domain="[('type','!=','view')]",help="Journal ini dibutuhkan saat proses Akuisisi Asset.")

    