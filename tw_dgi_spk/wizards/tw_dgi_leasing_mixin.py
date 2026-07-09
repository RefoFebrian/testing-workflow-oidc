# -*- coding: utf-8 -*-
"""
DGI Leasing API Integration Mixin

This mixin provides methods for fetching and processing leasing data
from the DGI API. It is used by tw_dgi_spk_wizard when the payment
type is Credit.

Separated for easier debugging and maintenance.
"""

from datetime import timedelta

from odoo import api, models
import logging

_logger = logging.getLogger(__name__)


class TwDgiLeasingMixin(models.AbstractModel):
    """
    Mixin untuk integrasi DGI Leasing API.
    Digunakan oleh tw.dgi.spk.wizard untuk fetch data leasing.
    """
    _name = "tw.dgi.leasing.mixin"
    _description = "DGI Leasing Integration Mixin"

    def _fetch_and_update_leasing_data(self, id_prospect, lead, spk_values):
        """Fetch leasing data from DGI API and update Lead.
        Returns a status string to be included in grouped logs."""
        lsng_values, status = self._fetch_leasing_values(id_prospect)
        if lsng_values:
            self._apply_leasing_to_lead(lead, lsng_values)
        return status

    def _fetch_leasing_values(self, id_prospect):
        """
        Fetch and parse leasing data from DGI API for a given Prospect ID.

        Args:
            id_prospect: The Prospect ID to query leasing data for.

        Returns:
            tuple: (dict of parsed leasing values or None, status string)
        """

    def _create_leasing_error_log(self, api_config, endpoint, id_prospect, payload, response_data, error_msg):
        """Wrapper for create_api_log using a separate cursor to persist despite rollbacks."""
        try:
            with self.pool.cursor() as new_cr:
                new_env = api.Environment(new_cr, self.env.uid, self.env.context)
                new_env['tw.api.log'].sudo().create_api_log(
                    name=f"DGI Leasing - Blocked (Prospect: {id_prospect})",
                    url=endpoint.full_url if endpoint else "DGI Leasing API",
                    description=error_msg,
                    ip_address=api_config.base_url if api_config else False,
                    response=response_data,
                    payload=payload,
                    header=False,
                    response_code='0',
                    status_code='error',
                    reference=id_prospect,
                    api_type_id=api_config.api_type_id.id if api_config and api_config.api_type_id else False,
                    company_id=self.company_id.id or self.env.company.id,
                )
                new_cr.commit()
        except Exception as e:
            _logger.error("Failed to create DGI leasing error log for prospect %s: %s", id_prospect, str(e))

    def _fetch_leasing_values(self, id_prospect, id_spk=None):
        """Fetch and parse leasing data menggunakan ID SPK."""
        if not id_spk:
            self._add_process_log("Cannot fetch leasing: no idSPK provided", 'WARNING')
            return None, "No idSPK"

        try:
            api_config, endpoint = self._get_leasing_endpoint()
            if not endpoint:
                self._add_process_log("No dgi_lsng endpoint configured, skipping leasing fetch", 'WARNING')
                return None, "Endpoint not configured"

            payload = self._prepare_leasing_request_body(id_spk=id_spk)
            response = self._call_leasing_endpoint(api_config, endpoint, id_spk=id_spk)

            if not response or not response.get('data'):
                error_msg = f"Not found for SPK {id_spk}"
                self._create_leasing_error_log(api_config, endpoint, id_spk, payload, response, error_msg)
                return None, error_msg

            lsng_data = self._extract_leasing_item(response['data'], id_spk)
            if not lsng_data:
                error_msg = f"No matching data for SPK {id_spk}"
                self._create_leasing_error_log(api_config, endpoint, id_spk, payload, response, error_msg)
                return None, error_msg

            lsng_values = self.env['tw.dgi.engine'].parse_response(endpoint, lsng_data)
            return lsng_values, "Success"

        except Exception as e:
            self._add_process_log(f"Failed to fetch leasing data for SPK {id_spk}: {str(e)}", 'ERROR')
            return None, f"Error: {str(e)}"

    def _apply_leasing_to_lead(self, lead, lsng_values, payment_type_id=None):
        """Apply parsed leasing values to Lead record.

        Performs a single atomic write so that ``tenor`` and
        ``payment_type_id`` are persisted together, which satisfies the
        ``_validate_financials`` constraint.

        Args:
            payment_type_id: If provided, also sets payment_type_id on Lead.
                             Pass this when payment_type was previously cleared
                             to avoid constraint violation before tenor was available.
        """
        if not lead or not lsng_values:
            return

        update_vals = self._prepare_leasing_update_vals(lsng_values)
        if payment_type_id:
            update_vals['payment_type_id'] = payment_type_id

        if update_vals:
            lead.sudo().write(update_vals)

    def _get_leasing_endpoint(self):
        """Return DGI API config and leasing endpoint."""
        api_config = self._get_api_config()
        endpoint = api_config.endpoint_config_ids.filtered(
            lambda endpoint_item: endpoint_item.code == 'dgi_lsng'
        )[:1]
        return api_config, endpoint

    def _call_leasing_endpoint(self, api_config, endpoint, id_spk=None):
        """Call DGI leasing endpoint."""
        body = self._prepare_leasing_request_body(id_spk=id_spk)
        return api_config.action_call_endpoint(
            endpoint=endpoint,
            params=body,
            raise_exception=False
        )

    def _prepare_leasing_request_body(self, id_spk=None):
        """
        Prepare request body for leasing API call.

        Args:
            id_spk: The SPK ID to send as idSPK in the request body.

        Returns:
            dict: Request body for leasing API
        """
        # fromTime untuk leasing selalu 7 hari ke belakang dari toTime
        # agar API mendapatkan cakupan waktu yang cukup untuk menemukan data leasing.
        leasing_from_time = self.to_time - timedelta(days=6)
        body = {
            'fromTime': leasing_from_time.strftime("%Y-%m-%d %H:%M:%S"),
            'toTime': self.to_time.strftime("%Y-%m-%d %H:%M:%S"),
            'idSPK': id_spk,
        }
        if self.company_id:
            body['dealerId'] = self.company_id.atpm_code
        return body

    def _update_lead_with_leasing(self, lead, lsng_data):
        """Update Lead record with canonical leasing values from mapping."""
        if not lead or not lsng_data:
            return

        update_vals = self._prepare_leasing_update_vals(lsng_data)
        if update_vals:
            lead.sudo().write(update_vals)

    def _prepare_leasing_update_vals(self, lsng_data):
        """Prepare canonical leasing values for Lead update."""
        update_vals = {}
        field_specs = {
            "tenor": int,
            "installment": float,
            "down_payment": float,
            "finco_po": None,
            "finco_po_create": None,
            "finco_id": None,
        }

        for field_name, caster in field_specs.items():
            value = lsng_data.get(field_name)
            if value in (None, False, ""):
                continue

            if caster:
                value = caster(value)

            update_vals[field_name] = value

        return update_vals

    def _extract_leasing_item(self, response_data, id_spk):
        """Return the leasing payload that matches the SPK ID."""
        if isinstance(response_data, dict):
            return response_data

        if not isinstance(response_data, list):
            return False

        for item in response_data:
            if item.get('idSPK') == id_spk:
                return item

        return False

    def _update_dso_lines_with_leasing(self, dso, lead):
        """
        Update Dealer Sale Order lines with leasing data from Lead.
        This ensures finco_po_number and finco_po_date are properly set.
        
        Args:
            dso: The Dealer Sale Order record
            lead: The Lead record containing leasing data
        """
        if not dso or not lead:
            return

        if not lead.finco_id and not lead.tenor:
            return

        update_vals = {}

        if lead.tenor:
            update_vals['tenor'] = lead.tenor

        if lead.installment:
            update_vals['installment'] = lead.installment

        if lead.down_payment:
            update_vals['downpayment'] = lead.down_payment

        if lead.finco_po:
            update_vals['finco_po_number'] = lead.finco_po

        if lead.finco_po_create:
            finco_po_date = lead.finco_po_create
            if isinstance(finco_po_date, str):
                try:
                    from datetime import datetime
                    finco_po_date = datetime.strptime(finco_po_date, '%Y-%m-%d').date()
                except ValueError:
                    finco_po_date = None
            update_vals['finco_po_date'] = finco_po_date

        if update_vals:
            main_lines = dso.order_line.filtered(lambda x: x.item_type == 'main')
            for line in main_lines:
                line.sudo().write(update_vals)
            self._add_process_log(
                f"[INFO] Updated DSO {dso.name} lines with leasing data",
                'INFO'
            )

        # Update finco_id di DSO header jika Lead memilikinya
        if lead.finco_id and not dso.finco_id:
            dso.sudo().write({'finco_id': lead.finco_id.id})

    def _is_credit_payment(self, payment_type_id):
        """
        Check if the payment type indicates a Credit transaction.
        
        Args:
            payment_type_id: ID of tw.selection record for payment type
            
        Returns:
            bool: True if Credit payment, False otherwise
        """
        if not payment_type_id:
            return False

        payment_type = self.env['tw.selection'].browse(payment_type_id)
        return bool(payment_type and payment_type.value in ('Credit', 'CREDIT', '2'))
