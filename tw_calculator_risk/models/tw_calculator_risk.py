# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


CATEGORY = [
    ('extreme', 'Extreme'),
    ('very_high', 'Very High'),
    ('high', 'High'),
    ('medium', 'Medium'),
    ('low', 'Low'),
    ('no_risk', 'No Risk'),
]


class TwCalculatorRisk(models.Model):
    """
    Master data untuk Calculator Risk.
    
    Digunakan untuk menghitung risk score berdasarkan kombinasi
    Financial, SLA, dan Percentage. Setiap kombinasi menghasilkan
    code unik dan score berdasarkan category.
    
    Fields:
        financial: Nilai financial (integer).
        service_level_agreement: Nilai SLA (integer).
        percentage: Nilai percentage (integer).
        code: Kombinasi dari financial + SLA + percentage.
        category: Kategori risk (extreme, very_high, high, medium, low, no_risk).
        score: Skor numerik berdasarkan category (0-5).
    """
    _name = "tw.calculator.risk"
    _description = 'Master Calculator Risk'
    _rec_name = 'code'
    _order = 'code DESC'

    name = fields.Char(string="Name")
    financial = fields.Integer(string="Financial")
    service_level_agreement = fields.Integer(string="SLA")
    percentage = fields.Integer(string="Percentage")
    code = fields.Char(string="Code")
    category = fields.Selection(CATEGORY, string="Category")
    score = fields.Integer(string="Score")

    @api.onchange('financial', 'service_level_agreement', 'percentage')
    def _onchange_risk_code(self):
        """Generate code dari kombinasi financial, SLA, dan percentage."""
        for line in self:
            line.code = str(line.financial) + str(line.service_level_agreement) + str(line.percentage)

    @api.onchange('category')
    def _onchange_risk_score(self):
        """Hitung score berdasarkan category yang dipilih."""
        score_mapping = {
            'extreme': 5,
            'very_high': 4,
            'high': 3,
            'medium': 2,
            'low': 1,
            'no_risk': 0,
        }
        for line in self:
            line.score = score_mapping.get(line.category, 0)
