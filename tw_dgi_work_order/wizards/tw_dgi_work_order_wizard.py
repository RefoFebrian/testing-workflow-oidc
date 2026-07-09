# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import models, fields, Command
from odoo.exceptions import UserError

class DGIWorkOrderWizard(models.TransientModel):
    _name = "tw.dgi.work.order.wizard"
    _inherit = "tw.dgi.wizard.mixin"
    _description = "DGI Work Order Wizard"

    no_work_order = fields.Char(string="Nomor Work Order")

    def action_get_dgi_data(self):
        """Main action: GET data dari DGI dan process"""
        return self.action_sync_dgi_data(endpoint_code='dgi_wo')

    def _prepare_api_request_body(self):
        prepare = super()._prepare_api_request_body()
        if self.no_work_order:
            prepare['noWorkOrder'] = self.no_work_order
        return prepare

    def _prepare_parse_response(self, endpoint, response_item):
        """Validate and determine create vs update flow."""
        no_wo = response_item.get('noWorkOrder')
        existing = self.env['tw.work.order'].sudo().search([
            ('md_reference_pkb', '=', no_wo)
        ], limit=1)
        
        if existing:
            if existing.is_invoiced:
                # Sudah invoice → skip
                return {
                    'proceed': False,
                    'message': f"WO {no_wo} sudah di-invoice: {existing.name}",
                    'log_type': 'WARNING'
                }
            # Belum invoice → simpan ref untuk update di _create_record
            response_item['_existing_wo_id'] = existing.id

        # Validate services + parts not both empty
        services = response_item.get('services') or []
        parts = response_item.get('parts') or []
        if not services and not parts:
            return {
                'proceed': False,
                'message': f"WO {no_wo}: services dan parts kosong",
                'log_type': 'WARNING'
            }
            
        return super()._prepare_parse_response(endpoint, response_item)

    def _get_item_identifier(self, endpoint, item):
        return f"WO {item.get('noWorkOrder', 'Unknown')}"

    def _create_record_from_response(self, endpoint, values):
        """Override: handle create/update, partner, lot, order_line."""
        existing_wo_id = values.pop('_existing_wo_id', False)
        
        # Build complex values (partner, lot, order_line)
        wo_vals = self._build_work_order_vals(endpoint, values)
        
        if existing_wo_id:
            # UPDATE existing WO — hanya tambahkan line yang belum ada
            wo = self.env['tw.work.order'].sudo().browse(existing_wo_id)

            # Kumpulkan product_id yang sudah ada di WO lama
            existing_product_ids = set(wo.order_line.mapped('product_id').ids)

            # Filter: hanya ambil line baru yang product-nya belum ada
            new_lines = []
            for cmd in wo_vals.get('order_line', []):
                if cmd[0] == 0 and isinstance(cmd[2], dict):
                    product_id = cmd[2].get('product_id')
                    if product_id and product_id not in existing_product_ids:
                        new_lines.append(cmd)
                        existing_product_ids.add(product_id)

            wo_vals['order_line'] = new_lines
            wo_vals['state'] = 'draft'  # Reset ke Draft setelah update DGI
            wo.sudo().write(wo_vals)
            action = "Updated"
        else:
            # CREATE new WO
            # is_dgi/dgi_get_date/dgi_get_uid diisi otomatis oleh _prepare_record_value di super()
            wo = super()._create_record_from_response(endpoint, wo_vals)
            action = "Created"

        extra_logs = [
            f"Action: {action}",
            f"Type: {wo.type_id.value if wo.type_id else 'REG'}",
            f"Status DGI: {wo.state_dgi or '-'}",
            f"Lines: {len(wo.order_line)} items",
        ]
        return wo.with_context(dgi_success_log_lines=extra_logs)

    def _build_work_order_vals(self, endpoint, values):
        """Orchestrator: gabungkan semua sub-method jadi vals lengkap"""
        company_id = values.get('company_id')
        if not company_id:
            company_id = self.company_id.id or self.env.company.id

        # Parse dates
        tanggal_wo = datetime.now().date()
        tanggal_servis_str = values.get('tanggalServis')
        if tanggal_servis_str:
            try:
                tanggal_wo = datetime.strptime(tanggal_servis_str, '%d/%m/%Y').date()
            except ValueError:
                pass

        lot_id = values.get('lot_id')
        product_id = False
        is_own_dealer = False
        
        if lot_id:
            lot = self.env['stock.lot'].sudo().browse(lot_id)
            product_id = lot.product_id.id
            if lot.company_id.id == company_id:
                is_own_dealer = True
        
        # Determine WO Type and Claim Type
        type_id, claim_type_id, previous_wo_id = self._resolve_wo_type(values, company_id)

        # Build lines
        services = values.get('services') or []
        parts = values.get('parts') or []
        
        service_lines, service_kpb_lines, final_kpb_ke = self._build_service_lines(services, company_id)
        part_lines = self._build_part_lines(parts, company_id, final_kpb_ke)

        # Jika KPB, rules KPB berlaku
        order_line_commands = service_lines + service_kpb_lines + part_lines

        # Update values with complex computations, allowing DGI Engine's output template to handle the rest
        values.update({
            'lot_id': lot_id,
            'product_id': product_id,
            'is_own_dealer': 'ya' if is_own_dealer else 'tidak',
            'purchase_date': tanggal_wo,
            'type_id': type_id,
            'claim_type_id': claim_type_id,
            'previous_work_order_id': previous_wo_id,
            'kpb_ke': final_kpb_ke,
            'order_line': order_line_commands,
        })

        # Fallback purchase_date from lot if exists
        if lot_id:
            lot = self.env['stock.lot'].sudo().browse(lot_id)
            if lot.invoice_date:
                values['purchase_date'] = lot.invoice_date
                
        return values


    def _build_service_lines(self, services, company_id):
        service_lines = []
        service_kpb_lines = []
        kpb_ke = False
        
        branch_setting = self.env['tw.branch.setting'].sudo().search([('company_id', '=', company_id)], limit=1)
        pricelist_service = branch_setting.pricelist_service_id if branch_setting else False
        company = self.env['res.company'].sudo().browse(company_id)
        
        for service in services:
            id_job = service.get('idJob')
            
            # Lookup ke master mapping jasa
            master_jasa = self.env['tw.dgi.mapping.master.jasa.line'].sudo().search([
                ('mapping_id.main_dealer_id', '=', company.default_supplier_id.id),
                ('product_md', '=', id_job)
            ], limit=1)
            
            if master_jasa and master_jasa.product_id:
                product = master_jasa.product_id
            else:
                product = self.env['product.product'].sudo().search([
                    ('division', '=', 'Service'),
                    ('default_code', '=', id_job)
                ], limit=1)
                
            if not product:
                continue
                
            price = pricelist_service._price_get(product, 1)[pricelist_service.id] if pricelist_service else product.lst_price
            
            # Deteksi KPB dari idJob / namaPekerjaan (tiap MD beda pattern)
            is_kpb = False
            nama_pekerjaan = service.get('namaPekerjaan', '').upper()
            if 'KPB' in nama_pekerjaan:
                is_kpb = True
                if '1' in nama_pekerjaan or 'PERTAMA' in nama_pekerjaan: kpb_ke = '1'
                elif '2' in nama_pekerjaan or 'KEDUA' in nama_pekerjaan: kpb_ke = '2'
                elif '3' in nama_pekerjaan or 'KETIGA' in nama_pekerjaan: kpb_ke = '3'
                elif '4' in nama_pekerjaan or 'KEEMPAT' in nama_pekerjaan: kpb_ke = '4'
                
            # Coba deteksi KPB dari master jasa type
            if master_jasa and master_jasa.mapping_id.type == 'KPB':
                is_kpb = True
                
            line_vals = Command.create({
                'division': 'Service',
                'product_id': product.id,
                'name': product.display_name,
                'product_uom_qty': 1,
                'price_unit': price,
                'product_uom': 1,
                'warranty': product.categ_id.warranty,
            })
            
            if is_kpb:
                service_kpb_lines.append(line_vals)
            else:
                service_lines.append(line_vals)
                
        return service_lines, service_kpb_lines, kpb_ke

    def _build_part_lines(self, parts, company_id, kpb_ke):
        part_lines = []
        branch_setting = self.env['tw.branch.setting'].sudo().search([('company_id', '=', company_id)], limit=1)
        pricelist_part = branch_setting.pricelist_sale_sparepart_id if branch_setting else False
        
        for part in parts:
            parts_number = part.get('partsNumber') or part.get('PartsNumber')
            if not parts_number:
                continue
                
            product = self.env['product.product'].sudo().search([
                ('default_code', '=', parts_number),
                ('division', '=', 'Sparepart')
            ], limit=1)
            
            if not product:
                product = self.env['product.product'].sudo().search([
                    ('name', '=', parts_number),
                    ('division', '=', 'Sparepart')
                ], limit=1)
                
            if not product:
                continue
                
            qty = part.get('kuantitas') or 1
            price = pricelist_part._price_get(product, qty)[pricelist_part.id] if pricelist_part else product.lst_price
            
            part_lines.append(Command.create({
                'division': 'Sparepart',
                'product_id': product.id,
                'name': product.display_name,
                'product_uom_qty': qty,
                'price_unit': price,
                'product_uom': 1,
                'warranty': product.categ_id.warranty,
            }))
            
        return part_lines

    def _resolve_wo_type(self, values, company_id):
        type_code = 'REG'
        claim_type_id = False
        previous_wo_id = False
        
        # Check WAR (Job Return)
        if values.get('noWorkOrderJobReturn'):
            type_code = 'WAR'
            prev_wo = self.env['tw.work.order'].sudo().search([
                ('md_reference_pkb', '=', values.get('noWorkOrderJobReturn')),
                ('company_id', '=', company_id)
            ], limit=1)
            if prev_wo:
                previous_wo_id = prev_wo.id
        else:
            # Check KPB from services
            for svc in (values.get('services') or []):
                nama = svc.get('namaPekerjaan', '').upper()
                if 'KPB' in nama:
                    type_code = 'KPB'
                    break
        
        type_id = self.env['tw.selection'].sudo().search([
            ('type', '=', 'WorkOrderType'),
            ('value', '=', type_code)
        ], limit=1).id
        
        if type_code == 'CLA':
            claim_type_id = self.env['tw.selection'].sudo().search([
                ('type', '=', 'WorkOrderClaimType'),
                ('value', '=', 'KPB')
            ], limit=1).id
            
        return type_id, claim_type_id, previous_wo_id