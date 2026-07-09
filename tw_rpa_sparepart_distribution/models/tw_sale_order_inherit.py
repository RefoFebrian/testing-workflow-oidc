from datetime import datetime, date
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning

import logging
_logger = logging.getLogger(__name__)


class RPASparepartDistributionSalesOrder(models.Model):
    _inherit = "tw.sale.order"
    # INFO : RPA Sparepart Distribution Sales Order

    is_auto_confirm = fields.Boolean(string='Is Auto Confirm ?',default=False)
    is_rpa = fields.Boolean(string='RPA',default=False)
    failed_rpa_reason = fields.Char(string='Alasan Gagal RPA')
    
    
    def generate_hari_pengiriman(self):
        schedule = self.env['tw.schedule.shipment'].get_shipment_day('sale_order')
        return schedule.get('shipment_day').lower()
    
    def outstanding_stock_distribution(self, branch_config, limit=150):
        query_where = "WHERE 1=1"
        query_where += " AND (sd.end_date >= '%s' OR sd.end_date is null)" % (date.today().strftime('%Y-%m-%d'))
        
        query_where += " AND loc.id in ({additional_loc_id},{topup_loc_id},{hotline_loc_id},{bck_hotline_loc_id})".format(
            additional_loc_id=branch_config.rpa_additional_location_id.id,
            topup_loc_id=branch_config.rpa_topup_location_id.id,
            hotline_loc_id=branch_config.rpa_hotline_location_id.id,
            bck_hotline_loc_id=branch_config.rpa_backup_hotline_location_id.id,
        )

        query = f"""
            SELECT DISTINCT ON (sd_id) sd_id,
                is_oil_gmo,
                distribution.ar_group_id
            FROM (
                    SELECT sd.id AS sd_id,
                        MAX(CASE WHEN prod_cat.name IN ('OIL', 'GMO') THEN 1 ELSE 0 END) AS is_oil_gmo,
                        COALESCE(SUM(quant.quantity),0) qty_stock,
                        COALESCE((
                            SELECT SUM(product_uom_qty)
                            FROM stock_move sm
                                LEFT JOIN stock_picking sp ON sm.picking_id = sp.id
                                LEFT JOIN stock_picking_type spt ON sp.picking_type_id = spt.id
                            WHERE spt.code IN ('outgoing', 'interbranch_out', 'internal')
                                AND sp.company_id = b.id
                                AND sp.state NOT IN ('draft', 'cancel', 'done')
                                AND sp.division = 'Sparepart'
                                AND sm.product_id = product.id
                                AND sm.location_id = loc.id
                        ), 0) AS qty_reserved,
                        COALESCE((
                            SELECT SUM(sol.product_uom_qty)
                            FROM tw_sale_order so
                                LEFT JOIN tw_sale_order_line sol ON so.id = sol.order_id
                            WHERE so.stock_distribution_id = sd.id
                                AND sol.product_id = sdl.product_id
                                AND so.state NOT IN ('cancel', 'draft', 'unused')
                        ), 0) AS qty_so,
                        sdl.approved_qty AS qty_sdl,
                        dealer.dealer_group_id AS dealer_group_id,
                        CASE
                            WHEN pot.name NOT IN ('Hotline', 'Direct Gift')
                            AND dealer.dealer_group_id IS NOT NULL THEN dealer.dealer_group_id
                            ELSE NULL
                        END AS ar_group_id,
                        CASE
                            WHEN pot.name NOT IN ('Hotline', 'Direct Gift')
                            AND invoice.id IS NOT NULL THEN 'Stop'
                            ELSE 'Process'
                        END AS is_hotline,
                        CASE
                            WHEN pot.name NOT IN ('Hotline', 'Direct Gift') THEN dealer.jadwal_hari_pengiriman
                            ELSE 'True'
                        END AS jadwal_hari_pengiriman
                    FROM tw_stock_distribution AS sd
                        LEFT JOIN tw_stock_distribution_line sdl ON sd.id = sdl.stock_distribution_id
                        LEFT JOIN tw_purchase_order_type pot ON sd.purchase_order_type_id = pot.id
                        LEFT JOIN res_company b ON sd.company_id = b.id
                        LEFT JOIN res_partner dealer ON sd.requester_id = dealer.id
                        LEFT JOIN product_product product ON sdl.product_id = product.id
                        LEFT JOIN product_template prod_template ON product.product_tmpl_id = prod_template.id
                        LEFT JOIN product_category prod_cat ON prod_template.categ_id = prod_cat.id
                        JOIN stock_location loc ON loc.id = (
                            CASE
                                WHEN pot.name IN ('Additional', 'Fix') THEN {branch_config.rpa_additional_location_id.id}
                                WHEN pot.name IN ('Simpart', 'Topup') THEN {branch_config.rpa_topup_location_id.id}
                                WHEN pot.name = 'Hotline' AND sd.origin_transaction_id ISNULL THEN {branch_config.rpa_hotline_location_id.id}
                                WHEN pot.name = 'Hotline' AND sd.origin_transaction_id NOTNULL THEN {branch_config.rpa_backup_hotline_location_id.id}
                            END
                        )
                        LEFT JOIN tw_sparepart_substitusi subs ON product.id = subs.part_old_id
                        JOIN stock_quant quant ON product.id = quant.product_id AND quant.location_id = loc.id
                        LEFT JOIN LATERAL (
                            SELECT am.id
                            FROM account_move am
                            LEFT JOIN account_move_line aml ON aml.move_id = am.id 
                            LEFT JOIN tw_sale_order_line_invoice_rel rel ON aml.id = rel.invoice_line_id 
                            WHERE dealer.id = am.partner_id
                            AND am.invoice_date_due < (NOW() + INTERVAL '7 hours')::date
                            AND am.state = 'posted'
                            AND am.payment_state = 'not_paid'
                            AND am.amount_total != 0
                            AND am.division = 'Sparepart'
                            AND rel.invoice_line_id notnull
                        ) invoice ON TRUE
                           {query_where}
                            AND sd.division = 'Sparepart'
                            AND sd.state = 'open'
                            AND subs.id IS NULL
                            AND sd.mutation_request_id IS NULL
                            AND b.code = '{branch_config.company_id.get_default_main_dealer_code()}'
                    GROUP BY sd.id, dealer.id, b.id, product.id, loc.id, sdl.id, invoice.id, pot.name
                ) AS distribution
            WHERE distribution.qty_stock - distribution.qty_reserved > 0
                AND qty_sdl != qty_so
                AND distribution.is_hotline != 'Stop'
                AND distribution.jadwal_hari_pengiriman IN ('True', '{self.generate_hari_pengiriman()}')
            LIMIT {limit}
        """
        try:
            self._cr.execute(query)
        except Exception as err:
            raise Warning("Query failed to execute!\n(%s)" % str(err))
        
        return self._cr.dictfetchall()
    
    def get_sales_order_by_stock_distribution(self, stock_distribution_id):
        sales_order = self.suspend_security().search([
            ('stock_distribution_id', '=', stock_distribution_id),
            ('state', '=', 'draft')
        ])
        if not sales_order:
            stock_distribution = self.env['tw.stock.distribution'].suspend_security().browse(stock_distribution_id)
            stock_distribution.suspend_security().action_create_sale_order()

            return self.suspend_security().search([('stock_distribution_id', '=', stock_distribution.id), ('state', '=', 'draft')])

        return sales_order
    
    def update_source_location_by_stock_dist_type(self, branch_config):
        for record in self:
            source_location_id = False
            distribution = record.stock_distribution_id

            # Fill Source Location by Stock Distribution PO Type
            record.suspend_security().action_renew_price()
            if distribution.purchase_order_type_id.name in ('Additional','Fix'):
                source_location_id = branch_config.rpa_additional_location_id.id
            elif distribution.purchase_order_type_id.name in ('Simpart','Topup'):
                source_location_id = branch_config.rpa_topup_location_id.id
            elif distribution.purchase_order_type_id.name == 'Hotline':
                source_location_id = branch_config.rpa_hotline_location_id.id
                if distribution.is_add_from_hotline:
                    source_location_id = branch_config.rpa_backup_hotline_location_id.id
            
            record.location_id = source_location_id

    def update_line_discount_by_stock_distribution_type(self):
        order_line = []
        master_discount = self.env['tw.sale.discount.items']

        for record in self:
            if not record.stock_distribution_id.purchase_order_type_id:
                record.suspend_security().write({ 'failed_rpa_reason': "Stock Distribution Type tidak ada!" })
                continue

            distribution_type = record.stock_distribution_id.purchase_order_type_id.name
            for line in record.order_line:
                product_id = line.product_id.id
                domain = [('categ_id', '=', line.product_id.categ_id.id),
                          ('product_id', '=', False)]
                if product_id:
                    domain.append(('product_id', '=', product_id))
                master_discount_obj = master_discount.suspend_security().search(domain, limit=1)
                if not master_discount_obj:
                    continue

                if distribution_type == 'Additional':
                    discount = master_discount_obj.additional
                elif distribution_type == 'Topup':
                    discount = master_discount_obj.topup
                elif distribution_type == 'Simpart':
                    discount = master_discount_obj.simpart
                elif distribution_type == 'Hotline':
                    discount = master_discount_obj.hotline
                elif distribution_type == 'Fix':
                    discount = master_discount_obj.fix
    
                order_line.append([1, line.id, { 'discount': discount }])
            
            if order_line:
                record.suspend_security().write({ 'order_line': order_line })
    
    def update_discount_percent(self, is_oil_gmo):
        is_error = False
        ahass_top_line = self.env['tw.master.ahass.top.line']
        for record in self:
            failed_reason = ""
            distribution = record.stock_distribution_id
            domain = [('master_ahass_top_id.partner_id', '=', record.partner_id.id),
                      ('discount_cash_id.type_id', '=', distribution.purchase_order_type_id.id)]
            
            categ_name = [line.categ_id.name if is_oil_gmo == 1 else False for line in record.order_line]
            categ_id = [line.categ_id.id for line in record.order_line if is_oil_gmo == 1]
            if categ_id:
                domain += [('categ_id', 'in', categ_id)]
            else:
                domain += [('categ_id', '=', False)]
            
            ahass_top_obj = ahass_top_line.suspend_security().search(domain, limit=1)
            if not ahass_top_obj:
                is_error = True
                dealer = str(record.partner_id.name)
                failed_reason += "Master AHASS TOP pada SO ini Belum Terdaftar!" + \
                                 "Dealer: %s, Product Category: %s" % (dealer, categ_name)
            
            # Get or create cash discount line
            cash_discount = record.discount_ids.filtered(
                lambda d: d.discount_id and d.discount_id.discount_type == 'percentage' 
                and d.discount_id.type == 'out_receipt'
            )[:1]
            if not cash_discount:
                is_error = True
                failed_reason += "Master Discount Cash (%) tidak ditemukan!"
            
            if is_error:
                record.suspend_security().write({
                    'failed_rpa_reason': failed_reason,
                })
                continue

            discount_percent = float(ahass_top_obj.discount_cash_id.discount_percent)
            
            # Update payment term and discount amount in a single operation
            record.suspend_security().write({
                'payment_term_id': ahass_top_obj.discount_cash_id.payment_term_id.id,
                'failed_rpa_reason': failed_reason,
                'discount_ids': [(1, cash_discount.id, {'amount': discount_percent})]
            })

        return is_error

    def remove_line_by_invalid_category(self, is_oil_gmo, is_do_while_rpa):
        for record in self:
            order_line = []
            for line in record.order_line:
                if is_oil_gmo == 1 and line.categ_id.name not in ('OIL', 'GMO'):
                    is_do_while_rpa = True
                    order_line.append([2, line.id])

                elif line.qty_available <= 0:
                    order_line.append([2, line.id])

            if order_line:
                # Update record and reset discounts in a single operation
                record.suspend_security().write({
                    'order_line': order_line,
                })
                # Update all discount amounts in a single operation
                if record.discount_ids:
                    record.discount_ids.sudo().write({'amount': 0})

        return is_do_while_rpa

    def update_line_by_available_quantity(self):
        for record in self:
            order_line = []
            for line in record.order_line:
                if line.qty_available < line.product_uom_qty:
                    # INFO : The Process of Updating product_uom_qty and product_uos_qty if it Exceeds the Quantity Available
                    order_line.append([1, line.id, {
                        'product_uom_qty': line.qty_available,
                        'product_uos_qty': line.qty_available
                    }])
            
            if order_line:
                record.suspend_security().write({ 'order_line': order_line })

    def validate_plafond_limit(self):
        is_available = True
        is_continue_to_process = False
        so_line_to_process = []

        for record in self:
            invoice_total = record.amount_invoiced
            diff_invoice_limit = record.credit_limit - invoice_total

            if diff_invoice_limit < record.amount_total:
                # INFO : The Process of Checking Whether the Branch has Reached the 'Plafond' limit or not
                while is_available == True:
                    line_diff_limit = record.order_line.with_context(selisih_limit_invoice=diff_invoice_limit,
                                                                     so_line_to_process=so_line_to_process)
                    line_so_obj = line_diff_limit.filtered(lambda so: so.price_subtotal <= so._context['selisih_limit_invoice']
                                                                      and so.id not in so._context['so_line_to_process'])
                    if line_so_obj:
                        so_line_to_process += line_so_obj.ids
                        diff_invoice_limit = diff_invoice_limit - sum([line.price_subtotal for line in line_so_obj])
                    else:
                        is_available = False
                        continue
                
                if not so_line_to_process:
                    record.suspend_security().write({
                        'is_auto_confirm': False,
                        'failed_rpa_reason': 'Gagal Terproses Karena Plafond Limit !'
                    })
                    return is_continue_to_process
                
                else:
                    # INFO : The Process of Deleting Products that Have Reached the 'Plafond' limit
                    discontinue_line = record.order_line.filtered(lambda line: line.id not in so_line_to_process)
                    discontinue_line.suspend_security().unlink()
                    is_continue_to_process = True
        
        return is_continue_to_process
    
    def action_generate_so_line(self):
        pricelist = self.get_pricelist()
        sale_order_line = []
        existing_product = [line.product_id for line in self.order_line]
        for line in self.stock_distribution_id.distribution_line:
            if line.product_id in existing_product:
                continue

            if (line.approved_qty - line.qty) > 0 :
                sale_order_line.append([0,False,{
                    'categ_id': line.product_id.categ_id.id,
                    'product_id': line.product_id.id,
                    'description': line.product_id.name,
                    'product_uom_qty': line.approved_qty - line.qty,
                    'price_unit': self.stock_distribution_id._get_price_unit(pricelist, line.product_id.id),
                    'tax_id': [(6,0,[x.id for x in line.product_id.taxes_id])],
                }])
        self.order_line = sale_order_line
    
    def get_ar_master_group_dealer(self):
        query = """
            SELECT DISTINCT rp.dealer_group_id as dealer_group_id
            FROM res_partner rp 
                LEFT JOIN account_move AS invoice ON rp.id = invoice.partner_id
                    WHERE invoice.invoice_date_due < (now() + INTERVAL'7 hours')::date
                    AND invoice.move_type = 'md_sale_sparepart'
                    AND invoice.state = 'posted'
                    AND invoice.payment_state = 'not_paid'
                    AND invoice.amount_total != 0
                    AND invoice.division = 'Sparepart'
                    AND invoice.invoice_date >= '2025-01-01'
                    AND rp.dealer_group_id is not null
        """
        self._cr.execute(query)
        result = self._cr.dictfetchall()
        ids = [res['dealer_group_id'] for res in result]
        return ids
    
    @api.model
    def auto_generate_so_sparepart(self, is_check_current_hour=True, limit=150):
        current_hour = datetime.now().hour + 7
        if (current_hour >= 9 and current_hour <= 15) or (is_check_current_hour == False):
            branch_config = self.env['tw.branch.setting']._check_rpa_branch_locations(self.env['res.company'].get_default_main_dealer_code())
            ress = self.outstanding_stock_distribution(branch_config, limit=limit)
            if ress:
                group_dealer_ids = self.get_ar_master_group_dealer()
                
                for res in ress:
                    is_auto_confirm = False
                    is_do_while_rpa = True
                    
                    if res['ar_group_id'] in group_dealer_ids:
                        sales_order = self.get_sales_order_by_stock_distribution(res.get('sd_id'))
                        sales_order.suspend_security().write({
                            'is_auto_confirm': is_auto_confirm,
                            'failed_rpa_reason': 'Terdapat AR Group Dealer !'
                        })
                        continue
                    
                    
                    while is_do_while_rpa:
                        stock_distribution_id = res.get('sd_id')
                        is_do_while_rpa = is_error = False
                        sales_order = self.get_sales_order_by_stock_distribution(stock_distribution_id)
                        if not sales_order:
                            _logger.error("RPA Part Distribution: Sales Order not found with distribution id %s" % stock_distribution_id)
                            continue
                        
                        distribution = sales_order.stock_distribution_id
                        sales_order.update_source_location_by_stock_dist_type(branch_config)
                        
                        sales_order.suspend_security().renew_available()
                        sales_order.update_line_by_available_quantity()
                        is_do_while_rpa = sales_order.remove_line_by_invalid_category(res.get('is_oil_gmo'), is_do_while_rpa)
                        
                        sales_order.suspend_security().update_line_discount_by_stock_distribution_type()
                        is_error = sales_order.update_discount_percent(res.get('is_oil_gmo'))

                        plafond_avaibility = amount_total = 0
                        for order in sales_order:
                            plafond_avaibility += order.plafond_avaibility
                            amount_total += sales_order.amount_total
                    
                        is_continue_to_process = sales_order.validate_plafond_limit()

                        if not is_error:
                            if amount_total < plafond_avaibility or is_continue_to_process == True:
                                for order in sales_order:
                                    if not order.order_line:
                                        order.action_generate_so_line()
                                        order.suspend_security().write({
                                            'is_rpa': True,
                                            'is_auto_confirm': False,
                                            'failed_rpa_reason': 'Gagal Terproses Karena QTY AVB = 0'
                                        })
                                        continue
                                    
                                    try:
                                        order.suspend_security().write({
                                            'is_auto_confirm': True,
                                            'failed_rpa_reason': False,
                                            'is_rpa': True
                                        })
                                    except Exception as e:
                                        order.suspend_security().write({
                                            'failed_rpa_reason': 'Gagal Update SO: %s ' % (str(e)),
                                            'is_rpa': True,
                                            'is_auto_confirm': is_auto_confirm
                                        })
                                        continue
                                    
                                    try:
                                        order.suspend_security().action_request_approval()
                                        order.suspend_security().approva_all_approval(reason='Auto Approved by RPA Sparepart Distribution')
                                    except Exception as e:
                                        order.suspend_security().write({
                                            'failed_rpa_reason': 'Gagal Auto Confirm RPA: %s ' % (str(e)),
                                            'is_rpa': True,
                                            'is_auto_confirm': is_auto_confirm
                                        })

                                    distribution.suspend_security().write({ 'is_rpa': True })
                            else:
                                sales_order.suspend_security().write({
                                    'is_auto_confirm': is_auto_confirm,
                                    'failed_rpa_reason': 'Gagal Terproses Karena Plafond Limit !'
                                })
                        self._cr.commit()