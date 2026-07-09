# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)

def migrate(cr, version):
    """
    Pre-migration: DROP tables to ensure a fresh start.
    This deletes all existing data in these tables!
    """
    # TODO: Hapus jika sudah tidak perlu
    _logger.info("=" * 80)
    _logger.info("PRE-MIGRATION: DROPPING TABLES FOR FRESH START")
    _logger.info("=" * 80)
    
    # tables_to_drop = [
    #     'tw_good_receive_asset_line',      # Child table first (FK)
    #     'tw_good_receive_collecting_rel',  # M2M table
    #     'tw_good_receive_collecting',      # Related table
    #     'tw_good_receive_collecting_line',      # Related table
    #     'tw_good_receive',                 # Parent table
    #     'good_receive_line_tax',
    #     'account_asset_good_receive_line_rel',
    #     'purchase_order_asset_tw_good_receive_asset_line_rel',
    #     'tw_good_receive_assets',
    #     'invoice_good_recieve_collecting_line_id'
    # ]
    
    # try:
    #     for table in tables_to_drop:
    #         _logger.info(f"Dropping table {table} if exists...")
    #         cr.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
            
    #     _logger.info("=" * 80)
    #     _logger.info("✓✓✓ CLEANUP SUCCESS! Tables dropped. Odoo will recreate them empty.")
    #     _logger.info("=" * 80)
        
    # except Exception as e:
    #     _logger.error(f"✗✗✗ CLEANUP FAILED: {str(e)}")
    #     raise
