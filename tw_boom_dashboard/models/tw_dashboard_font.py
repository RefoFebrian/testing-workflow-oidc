from odoo import models, fields

class DashboardFont(models.Model):
    _name = "tw.dashboard.font"
    _description = "Dashboard Fonts"

    name = fields.Char(string="Font Name")
    font_family_css = fields.Char(string="Font Family CSS", help="e.g. 'Roboto', sans-serif")
    google_fonts_url = fields.Char(
        string="Google Fonts URL", 
        help="Optional: Paste the Google Fonts import URL here (e.g. https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap). Leave empty for system fonts."
    )
