select 
'tw_matrix_mekanik_mitra_' || lower(branch.code) as "External ID",
branch.code,
'tw_matrix_mekanik_mitra_detail_' || lower(branch.code) || '_' || min_ue || '_' || max_ue as "Detail/External ID",
mmmd.min_ue,
mmmd.max_ue,
mmmd.hari_kerja,
mmmd.jasa,
mmmd.part
from teds_matrix_mekanik_mitra mmm
left join wtc_branch branch on branch.id = mmm.branch_id
left join teds_matrix_mekanik_mitra_detail mmmd on mmmd.matrix_id = mmm.id
order by branch.code