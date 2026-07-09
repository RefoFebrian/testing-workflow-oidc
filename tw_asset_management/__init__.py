# -*- coding: utf-8 -*-

from . import controllers
from . import models


import logging
from odoo.tools import sql

_logger = logging.getLogger(__name__)

def pre_init_hook(env):
    """
    Hook ini dijalankan sebelum modul diinstal untuk membersihkan data relasi asset.
    Memeriksa keberadaan tabel sebelum mencoba menghapus data darinya.
    """
    tables_to_clean = [
        'account_move_purchase_order_asset_rel',
        'purchase_order_asset_stock_picking_rel',
        'product_category_purchase_order_asset_rel',
    ]

    for table in tables_to_clean:
        if sql.table_exists(env.cr, table):
            _logger.info(f"Table '{table}' exists. Deleting its records.")
            try:
                env.cr.execute(f"DELETE FROM {table};")
            except Exception as e:
                _logger.warning(f"Could not delete records from table {table}: {e}")
        else:
            _logger.info(f"Table '{table}' does not exist. Skipping.")



def uninstall_hook(env):
    """Clean up data when module is uninstalled"""

    tables_to_clean = [
        'account_tax_purchase_order_asset_line_rel',
        'account_move_purchase_order_asset_rel',
        'purchase_order_asset_stock_picking_rel',
        'product_category_purchase_order_asset_rel',
    ]

    for table in tables_to_clean:
        if sql.table_exists(env.cr, table):
            _logger.info(f"Table '{table}' exists. Deleting its records.")
            try:
                env.cr.execute(f"DELETE FROM {table};")
            except Exception as e:
                _logger.warning(f"Could not delete records from table {table}: {e}")
        else:
            _logger.info(f"Table '{table}' does not exist. Skipping.")
