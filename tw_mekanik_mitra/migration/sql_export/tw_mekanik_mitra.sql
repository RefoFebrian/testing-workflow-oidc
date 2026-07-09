SELECT
    'tw_hr_employee_' || he.nip AS "External ID",
    he.name_related AS "Name",
    branch.code AS "Branch",
    '' AS "Area",
    '' AS "Work Email",
    '' AS "Work Phone",
    '' AS "Work Mobile",
    'MEKANIK MITRA' AS "Job Position",
    'Mitra' AS "Tags",
    '' AS "Coach",
    '' AS "Manager",
    mitra.start_date AS "Working Start Date",
    mitra.end_date AS "Working End Date",
    '' AS "No NPWP",
    '' AS "No Kontrak",
    'PT Tunas Dwipa Matra' AS "Work Address",
    '' AS "Private Street",
    '' AS "Private Street2",
    '' AS "Private State",
    '' AS "Private City",
    '' AS "Private Zip",
    'Indonesia' AS "Private Country",
    '' AS "Private Email",
    'Single' AS "Marital Status",
    'Indonesia' AS "Nationality Country",
    '' AS "Identification No",
    '' AS "Passport No",
    '' AS "Gender",
    '' AS "Date Of Birth",
    '' AS "User",
    mitra.no_rekening AS "Nomor Rekening",
    mitra.nama_rekening AS "Nama Pemilik Rekening",
    CASE
        WHEN mitra.bank_name ILIKE 'Mandiri' THEN '118' --'BMRIIDJA'
        WHEN mitra.bank_name ILIKE 'BRI' THEN '111' --'BRINIDJA'
        WHEN mitra.bank_name ILIKE 'BCA' THEN '101' --'CENAIDJA'
        WHEN mitra.bank_name ILIKE 'BNI' THEN '103' --'BNINIDJA'
        WHEN mitra.bank_name ILIKE 'BSI' THEN '112' --'BSI'
        WHEN mitra.bank_name ILIKE 'BANK LAMPUNG' THEN '81' --'PDLPIDJ1'
        WHEN mitra.bank_name ILIKE 'BANK SUMSEL BABEL' THEN '97' --'BSSPIDSP'
        ELSE '118' --'BMRIIDJA'
    END AS "Bank Identifier Code",
    UPPER(mitra.bank_name) AS "Bank",
    mitra.perjanjian_ke AS "Perjanjian Ke",
    mitra.start_date AS "Tanggal Mulai",
    mitra.end_date AS "Tanggal Selesai",
    mitra.keterangan AS "Keterangan",
    mitra.surat_perjanjian AS "Agreement Letter",
    mitra.absen_finger AS "Absensi Finger ID"
FROM teds_master_mekanik_mitra mitra
LEFT JOIN hr_employee he
    ON he.id = mitra.mekanik_id
LEFT JOIN wtc_branch branch
    ON branch.id = mitra.branch_id