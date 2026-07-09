# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)



class TwDgiSpkWizard(models.TransientModel):
    """
    Wizard untuk sync SPK dari DGI API.
    Menggunakan mixin dari tw_dgi dan tw_dgi_leasing_mixin.
    """
    _name = "tw.dgi.spk.wizard"
    _description = "DGI SPK Sync Wizard"
    _inherit = ["tw.dgi.wizard.mixin", "tw.dgi.leasing.mixin"]

    # Additional optional fields for SPK sync
    id_spk = fields.Char(
        string='ID SPK',
        help='Optional: Filter by specific SPK ID'
    )
    sales_id = fields.Char(
        string='Sales People ID',
        help='Optional: Filter by specific salesperson ID (ATPM code)'
    )

    def _prepare_api_request_body(self):
        """Override to add idSPK, salesPeopleId, and idProspect to request body"""
        body = super()._prepare_api_request_body()

        # Always send salesPeopleId, empty string if not filled
        body['idSalesPeople'] = self.sales_id or ""

        # Always send idProspect, empty string if not filled
        body['idProspect'] = self.id_prospect or ""

        # Add idSPK if filled
        if self.id_spk:
            body['idSPK'] = self.id_spk

        return body

    def action_get_dgi_data(self):
        """Main action: GET data dari DGI dan process"""
        return self.action_sync_dgi_data(endpoint_code='dgi_spk')

    def _prepare_parse_response(self, endpoint, response_item):
        id_spk = response_item.get('idSpk', '')
        existing = self._get_existing_spk(id_spk)
        if existing:
            self._add_process_log(
                f"Skipped: ID SPK {id_spk} already exists as {existing.name}",
                'WARNING'
            )
            return False

        return True

    def _get_item_identifier(self, endpoint, item):
        """Override to extract SPK-specific identifier for logging."""
        id_spk = item.get('idSpk')
        if id_spk:
            return f"SPK {id_spk}"
        return super()._get_item_identifier(endpoint, item)

    def _prepare_line_vals(self, line_field, vals, source_item, index, endpoint):
        """
        Hook untuk custom processing SPK lines.
        Rename qty ke product_qty untuk tw.dealer.spk.line.
        """
        vals = super()._prepare_line_vals(line_field, vals, source_item, index, endpoint)

        if line_field == 'line_ids':
            # Set defaults
            if not vals.get('product_qty'):
                vals['product_qty'] = 1
            if vals.get('discount') is None:
                vals['discount'] = 0

            # Rename qty ke product_qty untuk tw.dealer.spk.line
            if 'qty' in vals:
                vals['product_qty'] = vals.pop('qty')

        return vals

    def _create_record_from_response(self, endpoint, values):
        """
        Override untuk create SPK dengan logic SPK-specific:
        - Fetch leasing data (jika Credit) SEBELUM Lead di-create/update.
          Jika Credit tetapi data leasing tidak tersedia, seluruh item
          di-rollback (tidak membuat Lead, SPK, maupun DSO).
        - Lead: find/create
        - Auto confirm setelah create

        Partner sudah di-handle oleh engine (create_if_not_found).
        values sudah bersih (tanpa keys yang dimulai _).
        Special keys tersedia di self._context_vals.
        """
        ctx = self.env.context
        partner_vals = ctx.get('_partner_id_vals', {})
        id_prospect = ctx.get('_idProspect', '')
        id_spk = values.get('source_document', '')
        first_product_id = self._get_first_product_id(values.get('line_ids', []))

        # Set specific company and division early so Lead gets them
        target_company_id = values.get('company_id') or self.company_id.id
        values['company_id'] = target_company_id
        values['division'] = "Unit"

        # Fetch leasing values FIRST (before Lead is created/updated) so that
        # tenor & installment are available when Lead write triggers constrains.
        # If Credit but leasing data is not available, the entire item is rolled back.
        lsng_values = None
        leasing_status = False
        if self._is_credit_payment(values.get('payment_type_id')):
            lsng_values, leasing_status = self._fetch_leasing_values(id_prospect, id_spk=id_spk)

            if not lsng_values or not lsng_values.get('tenor'):
                error_msg = (
                    f"Data leasing tidak tersedia untuk SPK Credit {id_spk} "
                    f"(Prospect: {id_prospect}). Status: {leasing_status}"
                )
                raise UserError(error_msg)


        lead, lead_status_type = self._find_or_create_lead(
            values, partner_vals, id_prospect, first_product_id, lsng_values
        )

        # Apply leasing data to Lead atomically (tenor + payment_type_id together)
        if lsng_values and lead:
            self._apply_leasing_to_lead(
                lead, lsng_values,
                payment_type_id=values.get('payment_type_id')
            )

        values.update({
            'lead_reference': id_prospect or False,
            'lead_id': lead.id if lead else False,
            'is_dgi': True,
        })

        # Inject finco_id dari leasing ke SPK sebelum create,
        # agar _prepare_dealer_sale_order_vals() meneruskannya ke DSO
        is_credit_finco = lsng_values and lsng_values.get('finco_id')
        if is_credit_finco:
            values['finco_id'] = lsng_values['finco_id']
            # Inject is_bbn, down_payment, tenor, installment ke SPK lines
            # (Credit + Finco: semua field ini wajib diisi di level SPK line)
            leasing_line_vals = {
                'is_bbn': True,
                'down_payment': float(lsng_values.get('down_payment') or 0),
                'tenor': int(lsng_values.get('tenor') or 0),
                'installment': float(lsng_values.get('installment') or 0),
            }
            for line_vals in values.get('line_ids', []):
                if isinstance(line_vals, (list, tuple)) and len(line_vals) >= 3:
                    line_vals[2].update(leasing_line_vals)

        spk = super()._create_record_from_response(endpoint, values)
        log_context = self._post_create_spk(spk, lead)
        
        # Build standard extra log lines
        extra_logs = []
        lead_name = log_context.get('lead_name', '-')
        lead_type = log_context.get('lead_status_type', 'unknown')
        extra_logs.append(f"Lead: {lead_name} ({lead_type})")

        if leasing_status:
            extra_logs.append(f"Leasing: {leasing_status}")
        if log_context.get('spk_confirmed'):
            extra_logs.append("SPK Confirm: Success")
        if log_context.get('so_created'):
            extra_logs.append("Sales Order: Created")
        if log_context.get('action_deal_skipped'):
            extra_logs.append(f"Deal Action: Skipped (state {log_context['action_deal_skipped']})")
        
        return spk.with_context(dgi_success_log_lines=extra_logs)

    def _get_existing_spk(self, id_spk):
        """Return existing active SPK by DGI source document."""
        if not id_spk:
            return self.env['tw.dealer.spk']

        return self.env['tw.dealer.spk'].sudo().search([
            ('source_document', '=', id_spk),
            ('state', '!=', 'cancelled')
        ], limit=1)

    def _get_first_product_id(self, line_commands):
        """Extract product_id dari line pertama."""
        if line_commands and len(line_commands[0]) > 2:
            return line_commands[0][2].get('product_id')
        return False

    def _find_or_create_lead(self, values, partner_vals, id_prospect, product_id, lsng_values=None):
        """Find existing lead, or fetch prospect from DGI when missing.

        Args:
            lsng_values: Optional dict of pre-fetched leasing data (tenor, installment, etc.)
                         Included in the lead write so Credit constrains pass on first write.
        """
        lead = self._find_existing_lead(values, partner_vals, id_prospect, product_id)
        if lead:
            lead.sudo().write(
                self._prepare_lead_update_vals(values, partner_vals, product_id, lsng_values)
            )
            return lead, 'updated'

        if not id_prospect:
            id_spk = values.get('source_document', '')
            self._add_process_log(
                f"[WARNING] No idProspect for SPK {id_spk}, continuing without Lead",
                'WARNING'
            )
            return False, 'none'

        try:
            lead_wizard = self.env['tw.dgi.lead.wizard'].sudo().create({
                "company_id": values.get("company_id") or self.company_id.id,
                "id_prospect": id_prospect,
                "from_time": self.from_time,
                "to_time": self.to_time,
            })
            lead_wizard.action_get_dgi_data()
            lead = self._get_integrated_lead(id_prospect)

            if lead:
                # Ensure the newly synced lead gets the most up-to-date info from the SPK payload
                lead.sudo().write(
                    self._prepare_lead_update_vals(values, partner_vals, product_id, lsng_values)
                )
                return lead, 'synced'

            self._add_process_log(
                f"[WARNING] DGI API returned no data for idProspect {id_prospect}, creating fallback Lead",
                'WARNING'
            )
            return self._create_fallback_lead(values, partner_vals, id_prospect, product_id, lsng_values), 'fallback'

        except Exception as e:
            self._add_process_log(
                f"[ERROR] Failed to fetch Lead from DGI for SPK: {str(e)}, creating fallback Lead",
                'ERROR'
            )
            return self._create_fallback_lead(values, partner_vals, id_prospect, product_id, lsng_values), 'fallback'

    def _create_fallback_lead(self, values, partner_vals, id_prospect, product_id, lsng_values=None):
        """Create a local Lead if DGI does not return prospect data."""
        # Check if an open lead already exists with this KTP to prevent duplicate error
        no_ktp = partner_vals.get('identification_number')
        if no_ktp:
            existing_lead = self.env['tw.lead'].sudo().search([
                ('identification_number', '=', no_ktp),
                ('state', '=', 'open')
            ], limit=1)
            if existing_lead:
                # Update the existing lead with fallback values
                update_vals = self._prepare_lead_update_vals(values, partner_vals, product_id, lsng_values)
                update_vals.update({
                    'source_document': id_prospect,
                    'is_integration': True,
                })
                existing_lead.sudo().write(update_vals)
                return existing_lead

        lead_vals = self._prepare_lead_update_vals(values, partner_vals, product_id, lsng_values)
        lead_vals.update({
            'source_document': id_prospect,
            'is_integration': True,
        })
        if not lead_vals.get('customer_name'):
            lead_vals['customer_name'] = 'Unknown Prospect'
            
        lead = self.env['tw.lead'].sudo().create(lead_vals)
        return lead

    def _find_existing_lead(self, values, partner_vals, id_prospect, product_id):
        """Find lead by DGI prospect or customer identity."""
        lead = self._get_integrated_lead(id_prospect)
        if lead:
            return lead

        no_ktp = partner_vals.get('identification_number')
        if not no_ktp or not product_id:
            return self.env['tw.lead']

        # First try to find exact match including company and product
        lead = self.env['tw.lead'].sudo().search([
            ('company_id', '=', values.get('company_id') or self.company_id.id),
            ('identification_number', '=', no_ktp),
            ('product_id', '=', product_id),
            ('state', '!=', 'cancel')
        ], limit=1)

        return lead

    def _get_integrated_lead(self, id_prospect):
        """Return integrated lead by prospect id."""
        if not id_prospect:
            return self.env['tw.lead']

        return self.env['tw.lead'].sudo().search([
            ('source_document', '=', id_prospect),
            ('is_integration', '=', True)
        ], limit=1)

    def _prepare_lead_update_vals(self, values, partner_vals, product_id, lsng_values=None):
        """Prepare lead values refreshed from SPK payload.

        Args:
            lsng_values: Optional dict of pre-fetched leasing data to include
                         (tenor, installment, etc.). For Credit payments, this is
                         guaranteed to contain valid tenor since the caller raises
                         before reaching this point if leasing data is unavailable.
        """
        update_vals = {
            'sales_id': values.get('sales_id'),
            'product_id': product_id,
            'company_id': values.get('company_id') or self.company_id.id,
            'payment_type_id': values.get('payment_type_id'),
            'sales_channel_id': values.get('sales_channel_id'),
        }

        if partner_vals.get('name'):
            update_vals['customer_name'] = partner_vals['name']
        if partner_vals.get('phone'):
            update_vals['phone'] = partner_vals['phone']
        if partner_vals.get('identification_number'):
            update_vals['identification_number'] = partner_vals['identification_number']

        # Include pre-fetched leasing financial data so Credit constrains pass on first write
        if lsng_values:
            leasing_field_map = {
                'tenor': int,
                'installment': float,
                'down_payment': float,
                'finco_id': None,
            }
            for field, caster in leasing_field_map.items():
                val = lsng_values.get(field)
                if val not in (None, False, ""):
                    update_vals[field] = caster(val) if caster else val

        # Filter out falsy values so we don't overwrite existing good data with None
        update_vals = {k: v for k, v in update_vals.items() if v}
        return update_vals

    def _post_create_spk(self, spk, lead):
        """Post-create actions: confirm SPK, create SO, and update DSO lines with leasing data."""
        log_data = {}
        
        # Auto confirm SPK
        try:
            spk.action_confirm_spk()
            log_data['spk_confirmed'] = True

            # Auto create SO after SPK confirmation
            spk.action_create_so()
            log_data['so_created'] = True

            # Update DSO lines with leasing data from Lead (from mixin)
            if lead and spk.dealer_sale_order_id:
                self._update_dso_lines_with_leasing(spk.dealer_sale_order_id, lead)

        except Exception as e:
            self._add_process_log(
                f"[WARNING] Failed to confirm SPK or create SO: {str(e)}",
                'WARNING'
            )

        # Update lead state
        if lead:
            log_data['lead_name'] = lead.name
            
            if lead.state == 'open':
                try:
                    lead.sudo().action_deal()
                except Exception as e:
                    self._add_process_log(
                        f"[WARNING] Lead {lead.name}: action_deal skipped — {str(e)}",
                        'WARNING'
                    )
            else:
                log_data['action_deal_skipped'] = lead.state
                
            lead.sudo().write({
                'spk_id': spk.id,
                'state': 'spk'
            })
            
        return log_data
