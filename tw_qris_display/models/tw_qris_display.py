# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

# Utility: panggil ini dari flow pembayaran setelah QR dibuat
def send_qris_update(env, display_code, amount, qris_base64, expires_at=None, note=None):
    payload = {
        "display_code": display_code,
        "amount": amount,
        "qris_base64": qris_base64,  # tanpa prefix, hanya payload base64
        "expires_at": expires_at,
        "note": note,
    }
    env["bus.bus"]._sendone(env.user.partner_id, "qris_notif", payload)

# ? Contoh pemakaian
# from odoo.addons.tw_qris_display.models.tw_qris_display import send_qris_update
# def generate_qris(self):
#   send_qris_update(self.env, display_code="KASIR-01", amount=1250000, qris_base64=qr_b64, expires_at=datetime.now() + timedelta(hours=1))