
import logging

from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.exceptions import UserError as Warning
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)


class RPASparepartDistributionMutationOrder(models.Model):
    _inherit = "tw.mutation.order"
    # INFO : RPA Sparepart Distribution Mutation Order

    is_auto_confirm = fields.Boolean(string='Is Auto Confirm ?',default=False)
    is_rpa = fields.Boolean(string='RPA',default=False)
    failed_rpa_reason = fields.Char(string='Alasan Gagal RPA')

    def generate_hari_pengiriman(self):
        schedule = self.env['tw.schedule.shipment'].get_shipment_day('mutation_order')
        return schedule.get('shipment_day').lower()


    def auto_generate_mo_sparepart(self, is_check_current_hour=True,limit=150):
        current_hour = datetime.now().hour + 7
        if (current_hour >= 9 and current_hour <= 15) or (is_check_current_hour == False):
            query_where = "WHERE 1=1"
            query_where += " AND (sd.end_date >= '%s' OR sd.end_date is null)" % (date.today().strftime('%Y-%m-%d'))

            branch_config = self.env['tw.branch.setting']._check_rpa_branch_locations(self.env['res.company'].get_default_main_dealer_code())

            query_where += " AND loc.id in ({additional_loc_id},{topup_loc_id},{hotline_loc_id},{bck_hotline_loc_id})".format(
                additional_loc_id=branch_config.rpa_additional_location_id.id,
                topup_loc_id=branch_config.rpa_topup_location_id.id,
                hotline_loc_id=branch_config.rpa_hotline_location_id.id,
                bck_hotline_loc_id=branch_config.rpa_backup_hotline_location_id.id,
            )
            
            query = f"""
                SELECT DISTINCT sd_id from (
                    SELECT DISTINCT sd.id AS sd_id
                        ,pot.name = 'Topup'
                        , SUM(quant.quantity) qty_stock
                        , COALESCE((SELECT sum(mol.qty) 
                            FROM tw_mutation_order as mo 
                            LEFT JOIN tw_mutation_order_line as mol on mol.mutation_order_id = mo.id 
                            AND mol.product_id = product.id
                            WHERE mo.stock_distribution_id = sd.id 
                            AND mo.state not in ('cancelled','draft')
                            ),0) as qty_mo
                        , sdl.approved_qty as qty_sdl
                        , COALESCE((
                            SELECT SUM(product_uom_qty) 
                                FROM stock_move sm 
                                LEFT JOIN stock_picking sp ON sm.picking_id = sp.id 
                                LEFT JOIN stock_picking_type spt ON sp.picking_type_id = spt.id
                                    WHERE spt.code IN ('outgoing','interbranch_out','internal') 
                                    AND sp.company_id = b.id 
                                    AND sp.state not IN ('draft','cancel','done') 
                                    AND sp.division = 'Sparepart' 
                                    AND sm.product_id = product.id
                                    AND sm.location_id = loc.id),0)
                            AS qty_reserved
                        , CASE WHEN pot.name != 'Hotline' THEN dealer.jadwal_hari_pengiriman 
            			ELSE 'True' END as jadwal_hari_pengiriman
                    FROM tw_stock_distribution sd
                        LEFT JOIN res_company b on sd.company_id = b.id
                        LEFT JOIN res_partner branch_requester on sd.requester_id = branch_requester.id
                        LEFT JOIN tw_purchase_order_type pot on sd.purchase_order_type_id = pot.id
                        LEFT JOIN res_partner dealer on sd.requester_id = dealer.id
                        LEFT JOIN tw_stock_distribution_line sdl on sd.id = sdl.stock_distribution_id
                        LEFT JOIN product_product product on sdl.product_id = product.id
                        LEFT JOIN product_template prod_template on product.product_tmpl_id = prod_template.id
                        LEFT JOIN product_category prod_cat on prod_template.categ_id = prod_cat.id
                        JOIN stock_location loc on loc.id = (CASE 
                             WHEN pot.name IN ('Additional', 'Fix') THEN {branch_config.rpa_additional_location_id.id}
                                WHEN pot.name IN ('Simpart', 'Topup') THEN {branch_config.rpa_topup_location_id.id}
                                WHEN pot.name = 'Hotline' AND sd.origin_transaction_id ISNULL THEN {branch_config.rpa_hotline_location_id.id}
                                WHEN pot.name = 'Hotline' AND sd.origin_transaction_id NOTNULL THEN {branch_config.rpa_backup_hotline_location_id.id}
                        END) AND loc.usage = 'internal' 
                        LEFT JOIN tw_sparepart_substitusi subs on product.id = subs.part_old_id
                        JOIN stock_quant quant on product.id = quant.product_id and quant.location_id = loc.id
                        {query_where}
                            AND sd.division = 'Sparepart'
                            AND sd.state = 'open'
                            AND subs.id is null
                            AND b.code = '{branch_config.company_id.get_default_main_dealer_code()}'
                            AND branch_requester.code != 'DLL'
                        GROUP BY sd.id, b.id, dealer.id, loc.id, pot.name, product.id, sdl.id
                        ORDER BY pot.name = 'Topup', sd.id ASC) as distribution  
                    WHERE distribution.qty_stock - distribution.qty_reserved > 0
                    AND qty_sdl != qty_mo 
                    AND distribution.jadwal_hari_pengiriman in ('True','{self.generate_hari_pengiriman()}')
                    LIMIT {limit}
            """
            self._cr.execute(query)
            ress = self._cr.dictfetchall()
            
            if ress:
                for res in ress:
                    sd_obj = self.env['tw.stock.distribution'].browse(res['sd_id'])
                    mo_obj = self.env['tw.mutation.order'].search([
                        ('stock_distribution_id','=',sd_obj.id),
                        ('state','=','draft')
                    ])
                    
                    # Create MO, if none (not clicked on web)
                    if not mo_obj:
                        sd_obj.suspend_security().action_create_mutation_order()
                        mo_obj = self.env['tw.mutation.order'].search([
                            ('stock_distribution_id','=',sd_obj.id),
                            ('state','=','draft')
                        ])
                    
                    if mo_obj:
                        if sd_obj.purchase_order_type_id.name == 'Additional':
                            location_id = branch_config.rpa_additional_location_id.id
                        elif sd_obj.purchase_order_type_id.name in ('Simpart','Topup'):
                            location_id = branch_config.rpa_topup_location_id.idc
                        elif sd_obj.purchase_order_type_id.name == 'Hotline':
                            location_id = branch_config.rpa_hotline_location_id.id
                            if sd_obj.is_add_from_hotline:
                                location_id = branch_config.rpa_backup_hotline_location_id.id
                        mo_obj.suspend_security().write({'location_id':location_id})
                        mo_obj.suspend_security().renew_available()

                        for mo_line in mo_obj.mutation_order_ids:
                            if mo_line.qty_available <= 0:
                                mo_line.suspend_security().unlink()
                            elif mo_line.qty_available < mo_line.qty:
                                mo_line.suspend_security().write({
                                    'qty':mo_line.qty_available
                                })    
                        # sementara sampai ada maintanance selanjutnya
                        if not mo_obj.mutation_order_ids:
                            mo_obj.action_generate_mo_line()
                        else:
                            mo_obj.suspend_security().renew_available()
                            try:
                                mo_obj.suspend_security().write({
                                    'is_rpa':True,
                                    'is_auto_confirm':True
                                })
                                mo_obj.suspend_security().action_request_approval()
                                mo_obj.suspend_security().approva_all_approval(reason='Auto Approved by RPA Sparepart Distribution')
                                mo_obj.suspend_security().action_confirm()
                            except Exception as e:
                                mo_obj.suspend_security().write({
                                    'failed_rpa_reason': str(e),
                                    'is_rpa':True,
                                    'is_auto_confirm':False
                                })
                            
                        sd_obj.write({
                            'is_rpa':True
                        })

    def action_generate_mo_line(self):
        for line in self.stock_distribution_id.stock_distribution_ids :
            if (line.approved_qty - line.qty) > 0:
                order_line_vals = {
                    'mutation_order_id': self.id,
                    'product_id': line.product_id.id,
                    'description': line.description,
                    'qty': line.approved_qty - line.qty,
                    'price': line.price,
                    'qty_available': 0
                }
                self.env['tw.mutation.order.line'].suspend_security().create(order_line_vals)
    
    def auto_confirm_rpa_sparepart_mo(self):
        query = """
            SELECT mo.id
                FROM tw_stock_distribution sd
                    LEFT JOIN tw_mutation_order mo ON sd.id = mo.stock_distribution_id
                    LEFT JOIN res_partner dealer on sd.requester_id = dealer.id
                        WHERE 1=1
                            AND mo.state = 'approved'
                            AND mo.division = 'Sparepart'
                            AND sd.is_rpa = True
                            AND mo.is_rpa = True
                            AND mo.failed_rpa_reason is not null
        """
        self._cr.execute(query)
        ress = self._cr.fetchall()

        if ress:
            mo_obj = self.env['tw.mutation.order'].sudo().search([('id','in',ress)])
            for mo in mo_obj:
                try:
                    mo.sudo().action_confirm()
                    mo.sudo().write({
                        'is_auto_confirm':True,
                        'failed_rpa_reason':None
                    })
                except Exception as e:
                    mo.sudo().write({
                        'failed_rpa_reason': 'Gagal Confirm karena ' + str(e),
                        'is_auto_confirm':False
                    })
