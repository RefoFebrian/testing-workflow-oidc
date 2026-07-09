# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class InheritAccountAssetAsset(models.Model):
    _inherit = "account.asset.asset"

    asset_adjustment_ids = fields.One2many('tw.asset.adjustment', 'asset_id', string='History Adjustments')