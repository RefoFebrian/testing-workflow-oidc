from odoo import models, api, _


class MutationInternalReport(models.AbstractModel):
    _name = "report.tw_mutation_internal.mutation_internal_report"
    _description = "Mutation Internal Report"
    
    def doc_line(self, move_line):
        lines = [(i+1, line) for i, line in enumerate(move_line)]
        return lines
    
    def time_date(self, date):
        return date.strftime("%d-%m-%Y %H:%M")
    
    def print_user(self):
        return self.env['res.users'].suspend_security().browse(self.env.uid).name
    
    def product_color(self,code):
        query = f"""
            SELECT attr_value.name ->> 'en_US' AS name
                FROM product_product product
                LEFT JOIN product_variant_combination variant ON product.id = variant.product_product_id
                LEFT JOIN product_template_attribute_value attr ON variant.product_template_attribute_value_id = attr.id
                LEFT JOIN product_attribute_value attr_value ON attr.product_attribute_value_id = attr_value.id
            WHERE product.default_code = '{code}'
        """
        self._cr.execute(query)
        data = self._cr.fetchone()
        if data:
            return data[0]
        
        return False
    
    def print_counter(self):
        model_id = self.env.ref('tw_mutation_internal.model_stock_picking').id
        report_id = self.env.ref('tw_mutation_internal.action_report_mutation_internal').id
        transaction_id = self.env.context.get('active_ids', [])[0]

        print_obj = self.env['tw.print.counter'].sudo().search([
            ('report_id', '=', report_id),
            ('model_id', '=', model_id),
            ('transaction_id', '=', transaction_id)
        ], limit=1)

        if not print_obj:
            print_count_obj = self.env['tw.print.counter'].sudo().create({
                'model_id': model_id,
                'transaction_id': transaction_id,
                'print_counter': 1,
                'report_id': report_id
            })
            return print_count_obj.print_counter
        else:
            print_obj.write({'print_counter': print_obj.print_counter + 1})
            
        return print_obj.print_counter
    
    def print_partner_address(self, partner):
        street = partner.street
        rt = partner.rt if partner.rt else '-'
        rw = partner.rw if partner.rw else '-'
        sub_district = partner.sub_district_id.name if partner.sub_district_id else '-'
        district = partner.district_id.name if partner.district_id else '-'
        city = partner.city_id.name if partner.city_id else '-'
        state = partner.state_id.name if partner.state_id else '-'
        
        return (f"{street}, " +
                f"Rt/Rw. {rt} / {rw}," +
                f"Kel. {sub_district.title()}, " +
                f"Kec. {district.title()}, " +
                f"{city.title()}, {state.title()}")
    
    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['stock.picking'].browse(docids)
        
        return {
            'doc_ids': docids,
            'doc_model': 'stock.picking',
            'docs': docs,
            'doc_line': self.doc_line,
            'time_date': self.time_date,
            'print_counter': self.print_counter,
            'print_user': self.print_user,
            'product_color': self.product_color,
            'print_partner_address': self.print_partner_address,
        }