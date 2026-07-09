from odoo import models, fields, api
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

class StockDistributionInherit(models.Model):
    _inherit = "tw.stock.distribution"

    def check_and_notify(self, model, last_running_rpa, range_hours, message_type, sd_message_type, pic_number):
        filter = [ ('create_date', '>=', last_running_rpa.strftime("%Y-%m-%d %H:%M:%S")), ('division','=','Sparepart') ]
        if model == 'tw.sale.order':
            filter += [('state', 'not in', ('cancel', 'unused'))]
        else:
            filter += [('state', '!=', 'cancelled')]

        records = self.env[model].sudo().search(filter, order='id DESC')
        if records :
            if not any(record.is_rpa for record in records):
                self.create_whatsapp_outbox_and_send_it(message_type, pic_number)
        else:
            rpa_sd = self.check_rpa_activity_sd(range_hours)
            if not rpa_sd:
                self.create_whatsapp_outbox_and_send_it(sd_message_type, pic_number)

    def schedulle_check_is_rpa_running(self, range_hours):
        last_running_rpa = datetime.now() - relativedelta(hours=(7 + range_hours))
        pic_number = self.env['ir.config_parameter'].sudo().get_param('pic_number_rpa_distribution')

        # Cek dan kirim notifikasi untuk sale.order
        self.check_and_notify('tw.sale.order', last_running_rpa, range_hours, 'sale_order', 'sd_sale_order', pic_number)

        # Cek dan kirim notifikasi untuk tw.mutation.order
        self.check_and_notify('tw.mutation.order', last_running_rpa, range_hours, 'mutation_order', 'sd_mutation_order', pic_number)

    def check_rpa_activity_sd(self, range_hours):
        last_running_rpa = datetime.now() - relativedelta(hours=(7 + range_hours))
        rpa_sd_running = self.env['tw.stock.distribution'].sudo().search([
            ('confirm_date', '>=', last_running_rpa.strftime("%Y-%m-%d %H:%M:%S")),
            ('state', '=', 'open')
        ], order='id DESC')
        if rpa_sd_running and not any(rpa_sd.is_rpa for rpa_sd in rpa_sd_running):
            return False
        else:
            return True

    def create_whatsapp_outbox_and_send_it(self, name, pic_number):
        tmpl_obj = self.env.ref('rpa_sparepart_distribution.tw_rpa_distribution_whatsapp_template')

        text_wa = ''
        template_wa = str(tmpl_obj.content)

        text_wa = template_wa.replace('{{1}}', datetime.now().strftime('%Y-%m-%d'))
        text_wa = text_wa.replace('{{2}}', name.replace('_', ' ').title())
            
        outbox_obj = self.env['tw.whatsapp.outbox'].create({
            'name' : 'PIC PART',
            'phone_number' : pic_number,
            'whatsapp_params_ids' : [],
            'origin': 'notification_gagal_running_rpa_%s' % (name),
            'message' : text_wa,
            'message_type' : 'template',
            'template_id' : tmpl_obj.id,
            'date': date.today(),
        })
        if outbox_obj:
            outbox_obj.action_send_wa_rpa_distribution()