from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError as Warning
from datetime import datetime, timedelta

class ScheduleShipment(models.Model):
    _name = "tw.schedule.shipment"
    _description = "Jadwal Pengiriman"
    _order = "id DESC"

    # Daftar pilihan model
    MODEL_SELECTION = [
        ('sale_order', 'Sales Order'),
        ('mutation_order', 'Mutation Order'),
    ]

    # Daftar hari dalam bahasa Indonesia
    DAY_SELECTION = [
        ('senin', 'Senin'),
        ('selasa', 'Selasa'),
        ('rabu', 'Rabu'),
        ('kamis', 'Kamis'),
        ('jumat', 'Jumat'),
        ('sabtu', 'Sabtu'),
        ('minggu', 'Minggu'),
    ]

    # Daftar pilihan termin pengiriman
    SHIPMENT_TERM_SELECTION = [
        ('h+0', 'H+0 (Hari yang sama)'),
        ('h+1', 'H+1 (1 Hari setelahnya)'),
        ('h+2', 'H+2 (2 Hari setelahnya)'),
        ('h+3', 'H+3 (3 Hari setelahnya)'),
        ('h+4', 'H+4 (4 Hari setelahnya)'),
        ('h+5', 'H+5 (5 Hari setelahnya)'),
        ('h+6', 'H+6 (6 Hari setelahnya)'),
    ]

    name = fields.Char('Nama', compute='_compute_name', store=True)
    model_id = fields.Selection(
        MODEL_SELECTION, 
        string='Model', 
        required=True,
        help='Model yang akan menggunakan jadwal pengiriman ini'
    )
    day = fields.Selection(
        DAY_SELECTION, 
        string='Hari', 
        required=True,
        help='Hari pengiriman'
    )
    day_sequence = fields.Integer('Urutan Hari', default=10, help='Urutan hari dalam seminggu')
    shipment_term = fields.Selection(
        SHIPMENT_TERM_SELECTION,
        string='Termin Pengiriman',
        default='h+1',
        required=True,
        help='Termin pengiriman (H+berapa hari)'
    )
    shipment_day = fields.Char(
        'Hari Pengiriman', 
        compute='_compute_shipment_day', 
        store=True,
        help='Hari pengiriman yang dihitung berdasarkan hari + termin'
    )
    active = fields.Boolean('Aktif', default=True)

    _sql_constraints = [
        ('model_day_uniq', 'unique(model_id, day)', 'Kombinasi Model dan Hari harus unik!')
    ]

    @api.depends('model_id', 'day')
    def _compute_name(self):
        for record in self:
            model_name = dict(record.MODEL_SELECTION).get(record.model_id, '')
            day_name = dict(record.DAY_SELECTION).get(record.day, '')
            record.name = f"{model_name} - {day_name}"

    @api.depends('day', 'shipment_term')
    def _compute_shipment_day(self):
        day_mapping = {day[0]: idx for idx, day in enumerate(self.DAY_SELECTION)}
        day_names = [day[1] for day in self.DAY_SELECTION]
        
        for record in self:
            if not record.day or not record.shipment_term:
                record.shipment_day = ''
                continue
                
            try:
                # Get day index and days to add
                day_idx = day_mapping.get(record.day)
                if day_idx is None:
                    record.shipment_day = 'Error: Invalid day'
                    continue
                    
                # Parse days to add from shipment_term (e.g., 'h+2' -> 2)
                try:
                    days_to_add = int(record.shipment_term.split('+')[1])
                except (IndexError, ValueError):
                    record.shipment_day = 'Error: Invalid term'
                    continue
                
                # Calculate shipment day index (0-6)
                shipment_day_idx = (day_idx + days_to_add) % 7
                
                # Set the shipment day name
                record.shipment_day = day_names[shipment_day_idx]
                
            except Exception as e:
                record.shipment_day = f'Error: {str(e)}'

    @api.model
    def get_shipment_day(self, model_name, order_date=None):
        """
        Mendapatkan hari pengiriman berdasarkan model dan tanggal pesanan
        :param model_name: Nama model (contoh: 'sale.order')
        :param order_date: Tanggal pesanan (opsional, default hari ini)
        :return: Dictionary berisi {'day': 'senin', 'shipment_day': 'Selasa', 'shipment_term': 'h+1'}
        """
        if not order_date:
            order_date = datetime.now()
        
        # Dapatkan nama hari dalam format lowercase (senin, selasa, dll)
        day_names = [day[0] for day in self.DAY_SELECTION]
        day_idx = order_date.weekday()  # 0=Senin, 6=Minggu
        current_day = day_names[day_idx]
        
        # Cari jadwal pengiriman untuk model dan hari ini
        schedule = self.search([
            ('model_id', '=', model_name),
            ('day', '=', current_day),
            ('active', '=', True)
        ], limit=1)
        
        if not schedule:
            raise Warning(f"Jadwal pengiriman tidak ditemukan untuk model {model_name} dan hari {current_day}")
            
        return {
            'day': schedule.day,
            'shipment_day': schedule.shipment_day,
            'shipment_term': schedule.shipment_term
        }