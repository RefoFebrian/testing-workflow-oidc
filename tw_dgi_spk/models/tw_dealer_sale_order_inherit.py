# -*- coding: utf-8 -*-

from lxml import etree

from odoo import _, models, fields
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


class TwDealerSaleOrderInherit(models.Model):
    _inherit = "tw.dealer.sale.order"

    # DGI Integration Fields
    source_document = fields.Char(
        string='DGI SPK ID',
        help='ID SPK dari DGI (idSpk)',
        index=True,
    )
    is_dgi = fields.Boolean(
        string='Is DGI',
        default=False,
        help='Penanda data dari integrasi DGI',
    )
    dgi_get_date = fields.Datetime(
        string="DGI Get Date",
        copy=False,
        readonly=True,
        help="Tanggal & waktu GET data dari DGI"
    )
    dgi_get_uid = fields.Many2one(
        'res.users',
        string="DGI Get By",
        copy=False,
        readonly=True,
        help="User yang melakukan GET data dari DGI"
    )

    def action_open_dgi_spk_wizard(self):
        """Open DGI SPK sync wizard from DSO list view button"""
        return {
            'name': 'GET DGI DSO',
            'type': 'ir.actions.act_window',
            'res_model': 'tw.dgi.spk.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }

    def action_show_dgi_info(self):
        """Show DGI integration info via popup"""
        self.ensure_one()
        return {
            'name': 'DGI Info',
            'type': 'ir.actions.act_window',
            'res_model': 'tw.dgi.info.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_model': self._name,
                'default_res_id': self.id,
                'default_is_dgi': self.is_dgi,
                'default_source_document': self.source_document,
                'default_dgi_get_date': self.dgi_get_date,
                'default_dgi_get_uid': self.dgi_get_uid.id,
            }
        }
    def action_confirm(self):
        for order in self:
            action = order._validate_dgi_required_data_before_confirm()
            if action:
                return action
        return super().action_confirm()

    def _validate_dgi_required_data_before_confirm(self):
        """Block DGI DSO confirmation when branch setting requires complete internal data."""
        self.ensure_one()
        if not self._should_validate_dgi_required_data():
            return None

        lead = self.lead_id
        if not lead:
            raise ValidationError(
                _("Lead belum terhubung pada DSO ini. Lengkapi relasi Lead sebelum Confirm.")
            )

        missing_fields = self._get_missing_dgi_required_fields(lead)
        missing_documents = self._get_missing_dgi_required_documents(lead)
        if not missing_fields and not missing_documents:
            return None

        # Return action to open lead form in primary edit mode
        return {
            'name': 'Lengkapi Data Lead DGI',
            'type': 'ir.actions.act_window',
            'res_model': 'tw.lead',
            'res_id': lead.id,
            'view_mode': 'form',
            'view_id': self.env.ref('tw_dgi_spk.view_tw_lead_dgi_edit_primary_form').id,
            'target': 'new',
        }

    def _should_validate_dgi_required_data(self):
        """Return True when DSO must be blocked until internal DGI data is completed."""
        self.ensure_one()
        branch_setting = self.company_id.branch_setting_id
        if not branch_setting or not branch_setting.is_dgi_dso_required:
            return False
        return bool(self.spk_id and self.spk_id.is_dgi)

    def _get_missing_dgi_required_fields(self, lead):
        """Return missing lead fields based on required configuration from the lead form view."""
        lead_form = self.env["ir.ui.view"]._get("tw_lead.tw_lead_crm_lead_form_view")
        required_nodes = etree.fromstring(lead_form.arch).xpath(
            "//group[not(ancestor::field[@name='address_ids']) and not(ancestor::field[@name='document_ids'])]"
            "//field[@required]"
        )
        required_fields = []
        for node in required_nodes:
            field_name = node.get("name")
            if not field_name or field_name in required_fields or field_name not in lead._fields:
                continue
            if self._is_required_field_node(lead, node):
                required_fields.append(field_name)

        missing_fields = []
        for field_name in required_fields:
            if lead[field_name]:
                continue
            field_desc = lead._fields[field_name].string or field_name
            missing_fields.append(field_desc)
        return missing_fields

    def _is_required_field_node(self, lead, node):
        """Evaluate required attribute from lead form view for a specific lead record."""
        required_expr = node.get("required")
        if not required_expr:
            return False
        if required_expr == "1":
            return True

        eval_context = {
            "True": True,
            "False": False,
            "None": None,
        }
        eval_context.update({
            field_name: lead[field_name]
            for field_name in (
                "interest",
                "payment_type",
                "down_payment",
                "motor_ownership",
            )
            if field_name in lead._fields
        })
        return bool(safe_eval(required_expr, eval_context))

    def _get_missing_dgi_required_documents(self, lead):
        """Return readable labels for required lead documents missing on DGI-driven DSO."""
        document_types = set(lead.document_ids.mapped("document_type_id.value"))
        required_documents = [
            ("ktp", _("KTP")),
            ("kk", _("KK")),
        ]
        return [
            label for document_code, label in required_documents
            if document_code not in document_types
        ]
