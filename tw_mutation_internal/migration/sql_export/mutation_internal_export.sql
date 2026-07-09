SELECT
    picking.name AS "name",
    branch.code AS "company_id",
    picking_type.name AS "picking_type_id",
    picking.date AS "date",
    picking.division AS "division",
    'stock_location_' || header_dest_loc.id::varchar AS "location_dest_id",
    'stock_location_' || header_src_loc.id::varchar AS "location_id",
    product.default_code AS "picking_line_ids/product_id",
    lot.name AS "picking_line_ids/lot_id",
    move.is_rfs AS "picking_line_ids/is_rfs",
    'stock_location_' || line_dest_loc.id::varchar AS "picking_line_ids/location_dest_id",
    'stock_location_' || line_src_loc.id::varchar AS "picking_line_ids/location_id",
    move.product_uom_qty AS "picking_line_ids/quantity"
FROM stock_picking picking
LEFT JOIN stock_move move ON move.picking_id = picking.id
LEFT JOIN stock_picking_type picking_type ON picking_type.id = picking.picking_type_id
LEFT JOIN stock_location header_src_loc ON header_src_loc.id = picking.internal_location_id
LEFT JOIN stock_location header_dest_loc ON header_dest_loc.id = picking.internal_location_dest_id
LEFT JOIN stock_location line_src_loc ON line_src_loc.id = move.location_id
LEFT JOIN stock_location line_dest_loc ON line_dest_loc.id = move.location_dest_id
LEFT JOIN wtc_branch branch ON branch.id = picking.branch_id
LEFT JOIN product_product product ON product.id = move.product_id
LEFT JOIN stock_production_lot lot ON lot.id = move.restrict_lot_id
LEFT JOIN wtc_approval_line app_line ON app_line.transaction_id = picking.id
WHERE picking_type.code = 'internal'
AND picking.state not in ('done','cancel')

