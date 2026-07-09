select 
 tk."name" as "Description"
 , wb.name as "Dealer"
 , 'TitikKeramaianCategory'||'|'||tk.category as "Category"
 , split_part(tk.latlang , ',', 1)::numeric AS "Latitude"
 , split_part(tk.latlang , ',', 2)::numeric AS "Longitude"
 , wk."name" as "Address"
 , coalesce(rcs.code ,rcs."name") as "Provinsi"
 , coalesce(wc.code ,wc.name) as "Kota / Kab"
 , coalesce(wk2.code, wk2.name) as "Kecamatan"
 , coalesce(wk.code ,wk.name) as "Kelurahan"
from titik_keramaian tk
left join wtc_branch wb on wb.id = tk.branch_id 
left join wtc_kelurahan wk on wk.id = tk.kelurahan_id and wk.active is true and wk.code ~ '^[0-9]+$'
left join wtc_kecamatan wk2 on wk2.id = tk.kecamatan_id and wk2.active is true and wk2.code ~ '^[0-9]+$'
left join wtc_city wc on wc.id = wk2.city_id and wc.active is true and wc.code ~ '^[0-9]+$'
left join res_country_state rcs on rcs.id = wc.state_id and rcs.code ~ '^[0-9]+$'
where 1=1
and (tk.latlang IS NULL
    OR tk.latlang ~ '^-?[0-9]+\.[0-9]+,\s*-?\d+\.\d+$'
)