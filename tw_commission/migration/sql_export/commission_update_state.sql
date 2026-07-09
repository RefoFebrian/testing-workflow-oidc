-- UPDATE STATE COMMISSION
UPDATE tw_commission c
SET state = 'confirm',
    confirm_uid = 1,
    confirm_date = NOW()
FROM ir_model_data imd
WHERE imd.model = 'tw.commission'
  AND imd.res_id = c.id
  AND imd.module = '__import__'
  AND imd.name LIKE 'tw_commission_%';