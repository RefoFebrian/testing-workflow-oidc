# -*- coding: utf-8 -*-

from odoo import models, fields


class TwDGILeadWizard(models.TransientModel):
    """Wizard for syncing Lead/Prospect data from DGI API"""
    _name = "tw.dgi.lead.wizard"
    _inherit = "tw.dgi.wizard.mixin"
    _description = "DGI Lead Sync Wizard"

    # Additional optional field for Lead sync
    sales_id = fields.Char(
        string='Sales People ID',
        help='Optional: Filter by specific salesperson ID (ATPM code)'
    )

    def _prepare_api_request_body(self):
        """Override to add salesPeopleId and idProspect to request body"""
        body = super()._prepare_api_request_body()

        # Always send salesPeopleId, empty string if not filled
        body['idSalesPeople'] = self.sales_id or ""

        # Always send idProspect, empty string if not filled
        body['idProspect'] = self.id_prospect or ""

        return body


    def action_get_dgi_data(self):
        """Main action: GET data dari DGI dan process"""
        return self.action_sync_dgi_data(endpoint_code='dgi_prospect')

    def _prepare_parse_response(self, endpoint, response_item):
        id_prospect = response_item.get('idProspect')
        existing = self._get_existing_dgi_lead(id_prospect)
        if existing and self._is_locked_for_spk(existing):
            self._add_process_log(
                f"Skipped: ID Prospect {id_prospect} already linked to SPK flow "
                f"({existing.name})",
                'WARNING'
            )
            return False

        return True

    def _get_item_identifier(self, endpoint, item):
        """Override to extract Lead-specific identifiers from DGI JSON."""
        if item.get('idProspect'):
            return f"Prospect {item.get('idProspect')}"
        if item.get('noKtp'):
            return f"KTP {item.get('noKtp')}"
        return super()._get_item_identifier(endpoint, item)

    def _create_record_from_response(self, endpoint, values):
        values = self._prepare_record_value(endpoint, values)
        existing = self._get_existing_dgi_lead(values.get('source_document'))

        if existing:
            existing.sudo().write(values)
            return existing

        # Before creating, ensure we don't violate KTP duplicate constraint
        no_ktp = values.get('identification_number')
        if no_ktp:
            existing_ktp_lead = self.env['tw.lead'].sudo().search([
                ('identification_number', '=', no_ktp),
                ('state', '=', 'open')
            ], limit=1)
            if existing_ktp_lead:
                existing_ktp_lead.sudo().write(values)
                return existing_ktp_lead

        return self.env['tw.lead'].sudo().create(values)

    def _get_existing_dgi_lead(self, source_document):
        """Return existing integrated lead by DGI source document."""
        if not source_document:
            return self.env['tw.lead']

        return self.env['tw.lead'].sudo().search([
            ('source_document', '=', source_document),
            ('is_integration', '=', True)
        ], limit=1)

    def _prepare_record_value(self, endpoint, values):
        values = super()._prepare_record_value(endpoint, values)
        """Apply DGI lead defaults before create or update."""
        dgi_source = self.env['tw.selection'].sudo().search([
            ('type', '=', 'DataSource'),
            ('value', '=', 'dgi')
        ], limit=1)

        values.update({
            'is_integration': True,
            'integration_get_date': self.env.cr.now(),
            'integration_get_uid': self.env.user.id,
            'data_source_id': dgi_source.id if dgi_source else False,
            'is_same_ktp': True,
        })
        values.setdefault('company_id', self.company_id.id)

        self._set_domicile_from_ktp(values)
        self._set_default_interest(values)
        return values

    def _set_domicile_from_ktp(self, values):
        """Copy domicile fields from KTP address fields."""
        domicile_field_map = {
            'street': 'street_domicile',
            'state_id': 'state_domicile_id',
            'city_id': 'city_domicile_id',
            'district_id': 'district_domicile_id',
            'sub_district_id': 'sub_district_domicile_id',
            'zip': 'zip_domicile',
        }
        for source_field, target_field in domicile_field_map.items():
            if values.get(source_field):
                values[target_field] = values[source_field]

    def _set_default_interest(self, values):
        """Default DGI lead interest to HOT when not provided."""
        if values.get('interest_id'):
            return

        interest_hot = self.env.ref('tw_lead.tw_lead_interest_hot', False)
        if interest_hot:
            values['interest_id'] = interest_hot.id

    def _is_locked_for_spk(self, lead):
        """Return True when DGI prospect must not overwrite SPK lifecycle data."""
        lead.ensure_one()

        if lead.state == 'spk':
            return True

        if 'spk_id' in lead._fields and lead.spk_id and lead.spk_id.state != 'cancelled':
            return True

        if 'tw.dealer.spk' not in self.env.registry:
            return False

        active_spk = self.env['tw.dealer.spk'].sudo().search([
            ('lead_id', '=', lead.id),
            ('state', '!=', 'cancelled')
        ], limit=1)
        return bool(active_spk)
