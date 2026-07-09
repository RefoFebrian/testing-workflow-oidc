WITH SelectionMapping(category, source_text, target_code) AS (
    VALUES
        -- Mapping Hobby
        ('hobby', 'membaca', 'Hobby|A15'), ('hobby', 'memancing', 'Hobby|A13'), ('hobby', 'badminton', 'Hobby|B1'), ('hobby', 'bernyayi', 'Hobby|A27'), ('hobby', 'menari', 'Hobby|A19'), ('hobby', 'adventure(petualangan)', 'Hobby|A1'), ('hobby', 'aeromodeling', 'Hobby|A2'), ('hobby', 'bercocok tanam', 'Hobby|A3'), ('hobby', 'berkaraoke', 'Hobby|A4'), ('hobby', 'bermain drama', 'Hobby|A5'), ('hobby', 'bermain sulap', 'Hobby|A6'), ('hobby', 'fotografi', 'Hobby|A7'), ('hobby', 'kaligrafi', 'Hobby|A8'), ('hobby', 'koleksi prangko (fillateli)', 'Hobby|A9'), ('hobby', 'makan', 'Hobby|A10'), ('hobby', 'massage', 'Hobby|A11'), ('hobby', 'melukis', 'Hobby|A12'), ('hobby', 'memasak', 'Hobby|A14'), ('hobby', 'membaca puisi', 'Hobby|A16'), ('hobby', 'memelihara binatang peliharaan', 'Hobby|A17'), ('hobby', 'menanam bunga', 'Hobby|A18'), ('hobby', 'mendongeng', 'Hobby|A20'), ('hobby', 'mengaji', 'Hobby|A21'), ('hobby', 'mengarang cerita', 'Hobby|A22'), ('hobby', 'mengambar', 'Hobby|A23'), ('hobby', 'mengkoleksi barang antik', 'Hobby|A24'), ('hobby', 'menjahit', 'Hobby|A25'), ('hobby', 'menulis buku', 'Hobby|A26'), ('hobby', 'origami', 'Hobby|A28'), ('hobby', 'otomotif', 'Hobby|A29'), ('hobby', 'pantonim', 'Hobby|A30'), ('hobby', 'shopping', 'Hobby|A31'), ('hobby', 'surat menyurat', 'Hobby|A32'), ('hobby', 'travelling', 'Hobby|A33'), ('hobby', 'basket', 'Hobby|B2'), ('hobby', 'bersepeda', 'Hobby|B3'), ('hobby', 'bowling', 'Hobby|B4'), ('hobby', 'fitness', 'Hobby|B5'), ('hobby', 'golf', 'Hobby|B6'), ('hobby', 'hiking', 'Hobby|B7'), ('hobby', 'jogging', 'Hobby|B8'), ('hobby', 'renang', 'Hobby|B9'), ('hobby', 'senam', 'Hobby|B10'), ('hobby', 'sepak bola', 'Hobby|B11'), ('hobby', 'tennis', 'Hobby|B14'), ('hobby', 'surfing', 'Hobby|B13'), ('hobby', 'volley', 'Hobby|B15'), ('hobby', 'yoga', 'Hobby|B16'), ('hobby', 'bermain game', 'Hobby|C1'), ('hobby', 'bermain komputer', 'Hobby|C2'), ('hobby', 'bermain musik', 'Hobby|C3'), ('hobby', 'browsing internet', 'Hobby|C4'), ('hobby', 'chatting', 'Hobby|C5'), ('hobby', 'mendengarkan musik', 'Hobby|C6'), ('hobby', 'mendengarkan radio', 'Hobby|C7'), ('hobby', 'menonton bioskop', 'Hobby|C8'), ('hobby', 'menonton film', 'Hobby|C9'), ('hobby', 'menonton tv', 'Hobby|C10'), ('hobby', 'lain', 'Hobby|A34'), ('hobby', 'lain-lain', 'Hobby|A34'), ('hobby', 'lainnya', 'Hobby|A34'), ('hobby', 'lain - lain', 'Hobby|A34'),
        -- Mapping Blood Type
        ('blood_type', 'a', 'BloodType|2'), ('blood_type', 'b', 'BloodType|4'), ('blood_type', 'o', 'BloodType|3'), ('blood_type', 'ab', 'BloodType|1'), ('blood_type', 'lain', 'BloodType|5'), ('blood_type', 'lain-lain', 'BloodType|5'), ('blood_type', 'lainnya', 'BloodType|5'), ('blood_type', 'lain - lain', 'BloodType|5'),
        -- Mapping Housing Tenure
        ('housing_tenure', 'rumah sendiri', 'HousingTenure|1'), ('housing_tenure', 'rumah orang tua', 'HousingTenure|2'), ('housing_tenure', 'rumah sewa', 'HousingTenure|3'), ('housing_tenure', 'lain', 'HousingTenure|3'), ('housing_tenure', 'lain-lain', 'HousingTenure|3'), ('housing_tenure', 'lainnya', 'HousingTenure|3'), ('housing_tenure', 'lain - lain', 'HousingTenure|3'),
        -- Mapping Motor Brand
        ('motor_brand', 'honda', 'MotorBrand|1'), ('motor_brand', 'yamaha', 'MotorBrand|2'), ('motor_brand', 'suzuki', 'MotorBrand|3'), ('motor_brand', 'kawasaki', 'MotorBrand|4'), ('motor_brand', 'motor lain', 'MotorBrand|5'), ('motor_brand', 'belum pernah memiliki', 'MotorBrand|6'), ('motor_brand', 'lain', 'MotorBrand|5'), ('motor_brand', 'lain-lain', 'MotorBrand|5'), ('motor_brand', 'lainnya', 'MotorBrand|5'), ('motor_brand', 'lain - lain', 'MotorBrand|5'),
        -- Mapping Motor Type
        ('motor_type', 'sport', 'MotorType|1'), ('motor_type', 'cub (bebek)', 'MotorType|2'), ('motor_type', 'at (automatic)', 'MotorType|3'), ('motor_type', 'belum pernah memiliki', 'MotorType|4'), ('motor_type', 'lain', 'MotorType|4'), ('motor_type', 'lain-lain', 'MotorType|4'), ('motor_type', 'lainnya', 'MotorType|4'), ('motor_type', 'lain - lain', 'MotorType|4'),
        -- Mapping Motor Utilization
        ('motor_util', 'berdagang', 'MotorUtilization|1'), ('motor_util', 'pemakaian jarak dekat', 'MotorUtilization|2'), ('motor_util', 'ke sekolah/kampus', 'MotorUtilization|3'), ('motor_util', 'rekreasi/olah raga', 'MotorUtilization|4'), ('motor_util', 'kebutuhan keluarga', 'MotorUtilization|5'), ('motor_util', 'bekerja', 'MotorUtilization|7'), ('motor_util', 'lain', 'MotorUtilization|6'), ('motor_util', 'lain-lain', 'MotorUtilization|6'), ('motor_util', 'lainnya', 'MotorUtilization|6'), ('motor_util', 'lain - lain', 'MotorUtilization|6'),
        -- Mapping Motor User
        ('motor_user', 'saya sendiri', 'MotorUser|1'), ('motor_user', 'anak', 'MotorUser|2'), ('motor_user', 'pasangan (suami/istri)', 'MotorUser|3'), ('motor_user', 'lain', 'MotorUser|4'), ('motor_user', 'lain-lain', 'MotorUser|4'), ('motor_user', 'lainnya', 'MotorUser|4'), ('motor_user', 'lain - lain', 'MotorUser|4'),
        -- Mapping Gender
        ('gender', 'lakilaki', 'Gender|1'), ('gender', 'laki-laki', 'Gender|1'), ('gender', 'pria', 'Gender|1'), ('gender', 'perempuan', 'Gender|2'), ('gender', 'wanita', 'Gender|2'),
        -- Mapping Religion
        ('religion', 'islam', 'Religion|1'), ('religion', 'kristen', 'Religion|2'), ('religion', 'katolik', 'Religion|3'), ('religion', 'hindu', 'Religion|4'), ('religion', 'budha', 'Religion|5'), ('religion', 'lain', 'Religion|6'), ('religion', 'lain-lain', 'Religion|6'), ('religion', 'lainnya', 'Religion|6'), ('religion', 'lain - lain', 'Religion|6'),
        -- Mapping Education
        ('education', 'tidak tamat sd', 'Education|1'), ('education', 'sd', 'Education|2'), ('education', 'sltp/smp', 'Education|3'), ('education', 'smp', 'Education|3'), ('education', 'slta/smu', 'Education|4'), ('education', 'sma', 'Education|4'), ('education', 'smk', 'Education|4'), ('education', 'akademi/diploma', 'Education|5'), ('education', 'sarjana', 'Education|6'), ('education', 'pasca sarjana', 'Education|7'), ('education', 'lain', 'Education|7'), ('education', 'lain-lain', 'Education|7'), ('education', 'lainnya', 'Education|7'), ('education', 'lain - lain', 'Education|7'),
        -- Mapping Occupation
        ('occupation', 'pegawai negeri', 'Occupation|1'), ('occupation', 'nelayan', 'Occupation|16'), ('occupation', 'ojek', 'Occupation|3'), ('occupation', 'pegawai swasta', 'Occupation|2'), ('occupation', 'mahasiswa/pelajar', 'Occupation|5'), ('occupation', 'guru/dosen', 'Occupation|6'), ('occupation', 'tni/polri', 'Occupation|7'), ('occupation', 'ibu rumah tangga', 'Occupation|8'), ('occupation', 'dokter', 'Occupation|10'), ('occupation', 'pengacara', 'Occupation|13'), ('occupation', 'wartawan', 'Occupation|14'), ('occupation', 'pertanian/perkebunan/kehutanan/perikanan/peternakan - pegawai swasta', 'Occupation|2a'), ('occupation', 'industri - pegawai swasta', 'Occupation|2b'), ('occupation', 'konstruksi - pegawai swasta', 'Occupation|2c'), ('occupation', 'pertambangan - pegawai swasta', 'Occupation|2d'), ('occupation', 'jasa - pegawai swasta', 'Occupation|2e'), ('occupation', 'perdagangan (retail) - pegawai swasta', 'Occupation|2f'), ('occupation', 'pertanian/perkebunan/kehutanan/perikanan/peternakan - wiraswasta / pedagang', 'Occupation|4a'), ('occupation', 'industri - wiraswasta / pedagang', 'Occupation|4b'), ('occupation', 'konstruksi - wiraswasta / pedagang', 'Occupation|4c'), ('occupation', 'pertambangan - wiraswasta / pedagang', 'Occupation|4d'), ('occupation', 'jasa - wiraswasta / pedagang', 'Occupation|4e'), ('occupation', 'perdagangan (retail) - wiraswasta / pedagang', 'Occupation|4f'), ('occupation', 'wiraswasta / pedagang', 'Occupation|4'), ('occupation', 'petani', 'Occupation|15'), ('occupation', 'lain', 'Occupation|11'), ('occupation', 'lain-lain', 'Occupation|11'), ('occupation', 'lainnya', 'Occupation|11'), ('occupation', 'lain - lain', 'Occupation|11'),
        -- Mapping Expense
        ('expense', '< rp 900.000,-', 'Expense|1'), ('expense', 'rp 900.001- s/d rp 1.250.000,-', 'Expense|2'), ('expense', 'rp 1.250.001- s/d rp1.750.000,-', 'Expense|3'), ('expense', 'rp 1.750.001- s/d rp 2.500.000,-', 'Expense|4'), ('expense', 'rp 2.500.001- s/d rp 4.000.000,-', 'Expense|5'), ('expense', 'rp 4.000.001- s/d rp 6.000.000,-', 'Expense|6'), ('expense', '> rp 6.000.000,-', 'Expense|7'), ('expense', 'lain', 'Expense|7'), ('expense', 'lain-lain', 'Expense|7'), ('expense', 'lainnya', 'Expense|7'), ('expense', 'lain - lain', 'Expense|7')
),
FilteredPartners AS (
    -- 1. Filter awal: Hanya Biro Jasa yang terdaftar di stock.production.lot
    SELECT rp.*
    FROM res_partner rp
    WHERE rp.id > 6 
    AND default_code IN ('STK/23/09/13811','STK/23/06/19178','STK/20/02/11482','STK/15/07/16739','MML1760','STK/20/01/18078','STK/19/04/16802','U0005','STK/19/08/23563','STK/19/10/23999','STK/17/09/08899','SUMO')
),
LatestCDDB AS (
    -- 2. Ambil data CDDB TERBARU
    SELECT DISTINCT ON (cddb.customer_id)
        cddb.customer_id,
        COALESCE(REGEXP_REPLACE(TRIM(cddb.facebook), '[
	]+', ' ', 'g'), '') AS facebook,
        COALESCE(REGEXP_REPLACE(TRIM(cddb.instagram), '[
	]+', ' ', 'g'), '') AS instagram,
        COALESCE(REGEXP_REPLACE(TRIM(cddb.twitter), '[
	]+', ' ', 'g'), '') AS twitter,
        COALESCE(REGEXP_REPLACE(TRIM(cddb.youtube), '[
	]+', ' ', 'g'), '') AS youtube,
        COALESCE(REGEXP_REPLACE(TRIM(cddb.suku), '[
	]+', ' ', 'g'), '') AS suku,
        COALESCE(REGEXP_REPLACE(TRIM(cddb.jabatan), '[
	]+', ' ', 'g'), '') AS jabatan,
        COALESCE(REGEXP_REPLACE(TRIM(cddb.penanggung_jawab), '[
	]+', ' ', 'g'), '') AS penanggung_jawab,
        COALESCE(mhobby.target_code, '') AS hobby_code,
        COALESCE(mblood.target_code, '') AS blood_type_code,
        COALESCE(mhouse.target_code, '') AS housing_tenure_code,
        COALESCE(mbrand.target_code, '') AS motor_brand_code,
        COALESCE(mtype.target_code, '') AS motor_type_code,
        COALESCE(mutil.target_code, '') AS unit_usage_code,
        COALESCE(muser.target_code, '') AS unit_operator_code,
        'CustomerCode|' || cddb.kode_customer AS customer_code_code
    FROM wtc_cddb cddb
    JOIN FilteredPartners fp ON fp.id = cddb.customer_id
    LEFT JOIN wtc_questionnaire q_hobi ON q_hobi.id = cddb.hobi
    LEFT JOIN SelectionMapping mhobby ON mhobby.category = 'hobby' AND mhobby.source_text = LOWER(TRIM(q_hobi.name))
    LEFT JOIN wtc_questionnaire q_gol_darah ON q_gol_darah.id = cddb.gol_darah
    LEFT JOIN SelectionMapping mblood ON mblood.category = 'blood_type' AND mblood.source_text = LOWER(TRIM(q_gol_darah.name))
    LEFT JOIN wtc_questionnaire q_status_rumah ON q_status_rumah.id = cddb.status_rumah_id
    LEFT JOIN SelectionMapping mhouse ON mhouse.category = 'housing_tenure' AND mhouse.source_text = LOWER(TRIM(q_status_rumah.name))
    LEFT JOIN wtc_questionnaire q_merkmotor ON q_merkmotor.id = cddb.merkmotor_id
    LEFT JOIN SelectionMapping mbrand ON mbrand.category = 'motor_brand' AND mbrand.source_text = LOWER(TRIM(q_merkmotor.name))
    LEFT JOIN wtc_questionnaire q_jenismotor ON q_jenismotor.id = cddb.jenismotor_id
    LEFT JOIN SelectionMapping mtype ON mtype.category = 'motor_type' AND mtype.source_text = LOWER(TRIM(q_jenismotor.name))
    LEFT JOIN wtc_questionnaire q_penggunaan ON q_penggunaan.id = cddb.penggunaan_id
    LEFT JOIN SelectionMapping mutil ON mutil.category = 'motor_util' AND mutil.source_text = LOWER(TRIM(q_penggunaan.name))
    LEFT JOIN wtc_questionnaire q_pengguna ON q_pengguna.id = cddb.pengguna_id
    LEFT JOIN SelectionMapping muser ON muser.category = 'motor_user' AND muser.source_text = LOWER(TRIM(q_pengguna.name))
    ORDER BY cddb.customer_id, cddb.id DESC
),
RawData AS (
    SELECT
        rp.id AS raw_id,
        rp.is_company,
        rp.default_code,
        COUNT(*) OVER (PARTITION BY NULLIF(TRIM(rp.default_code), '')) AS code_count,        
        -- Clean digits (dihitung sekali, dipakai berkali-kali)
        REGEXP_REPLACE(NULLIF(TRIM(rp.phone), ''), '\D', '', 'g') AS digits_phone,
        REGEXP_REPLACE(NULLIF(TRIM(rp.mobile), ''), '\D', '', 'g') AS digits_mobile,
        REGEXP_REPLACE(NULLIF(TRIM(rp.no_ktp), ''), '\D', '', 'g') AS digits_ktp,
        REGEXP_REPLACE(NULLIF(TRIM(rp.npwp), ''), '\D', '', 'g') AS digits_npwp,
        -- Normalized Name for Deduplication (Strip PT/CV to catch variations like PT.Summit vs Summit)
        REGEXP_REPLACE(REGEXP_REPLACE(LOWER(TRIM(rp.name)), '^(pt\.|pt\s+|cv\.|cv\s+)', '', 'g'), '[^a-z0-9]', '', 'g') AS norm_name,
        'res_partner_' || REPLACE(LOWER(TRIM(rp.default_code)), ' ', '_') AS "id",
        EXISTS (SELECT 1 FROM res_users ru WHERE ru.partner_id = rp.id) AS is_user,
        rp.active AS "active",
        CASE WHEN rp.is_company THEN 'company' ELSE 'person' END AS "company_type",
        COALESCE(REGEXP_REPLACE(TRIM(rp.name), '[
	]+', ' ', 'g'), '') AS "name",
        COALESCE(REGEXP_REPLACE(TRIM(rp.default_code), '[
	]+', ' ', 'g'), '') AS "code",
        -- Clean Phone & Standardized Format
        CASE 
            WHEN REGEXP_REPLACE(NULLIF(TRIM(rp.phone), ''), '\D', '', 'g') ~ '(\d)\1{5,}' THEN ''
            WHEN REGEXP_REPLACE(NULLIF(TRIM(rp.phone), ''), '\D', '', 'g') ~ '(\d{2,4})\1{2,}' THEN ''
            WHEN REGEXP_REPLACE(NULLIF(TRIM(rp.phone), ''), '\D', '', 'g') LIKE '%111111%' THEN ''
            WHEN LENGTH(REGEXP_REPLACE(NULLIF(TRIM(rp.phone), ''), '\D', '', 'g')) < 7 THEN ''
            WHEN REGEXP_REPLACE(NULLIF(TRIM(rp.phone), ''), '\D', '', 'g') LIKE '0%' AND LENGTH(REGEXP_REPLACE(NULLIF(TRIM(rp.phone), ''), '\D', '', 'g')) > 13 THEN ''
            WHEN REGEXP_REPLACE(NULLIF(TRIM(rp.phone), ''), '\D', '', 'g') LIKE '62%' AND LENGTH(REGEXP_REPLACE(NULLIF(TRIM(rp.phone), ''), '\D', '', 'g')) > 14 THEN ''
            WHEN LENGTH(REGEXP_REPLACE(NULLIF(TRIM(rp.phone), ''), '\D', '', 'g')) > 15 THEN ''
            WHEN REGEXP_REPLACE(NULLIF(TRIM(rp.phone), ''), '\D', '', 'g') LIKE '0%' 
            THEN '+62' || SUBSTRING(REGEXP_REPLACE(NULLIF(TRIM(rp.phone), ''), '\D', '', 'g') FROM 2)
            WHEN REGEXP_REPLACE(NULLIF(TRIM(rp.phone), ''), '\D', '', 'g') LIKE '62%'
            THEN '+62' || SUBSTRING(REGEXP_REPLACE(NULLIF(TRIM(rp.phone), ''), '\D', '', 'g') FROM 3)
            WHEN NULLIF(TRIM(rp.phone), '') LIKE '+62%'
            THEN NULLIF(TRIM(rp.phone), '')
            ELSE '' 
        END AS "phone",
        -- Standardized Mobile Logic
        CASE 
            WHEN REGEXP_REPLACE(NULLIF(TRIM(rp.mobile), ''), '\D', '', 'g') ~ '(\d)\1{6,}' THEN ''
            WHEN REGEXP_REPLACE(NULLIF(TRIM(rp.mobile), ''), '\D', '', 'g') ~ '(\d{2,4})\1{2,}' THEN ''
            WHEN REGEXP_REPLACE(NULLIF(TRIM(rp.mobile), ''), '\D', '', 'g') LIKE '%111111%' THEN ''
            WHEN REGEXP_REPLACE(NULLIF(TRIM(rp.mobile), ''), '\D', '', 'g') ~ '^080|^6280' THEN ''
            WHEN LENGTH(REGEXP_REPLACE(NULLIF(TRIM(rp.mobile), ''), '\D', '', 'g')) < 10 THEN ''
            WHEN REGEXP_REPLACE(NULLIF(TRIM(rp.mobile), ''), '\D', '', 'g') LIKE '0%' AND LENGTH(REGEXP_REPLACE(NULLIF(TRIM(rp.mobile), ''), '\D', '', 'g')) > 13 THEN ''
            WHEN REGEXP_REPLACE(NULLIF(TRIM(rp.mobile), ''), '\D', '', 'g') LIKE '62%' AND LENGTH(REGEXP_REPLACE(NULLIF(TRIM(rp.mobile), ''), '\D', '', 'g')) > 14 THEN ''
            WHEN LENGTH(REGEXP_REPLACE(NULLIF(TRIM(rp.mobile), ''), '\D', '', 'g')) > 15 THEN ''
            WHEN REGEXP_REPLACE(NULLIF(TRIM(rp.mobile), ''), '\D', '', 'g') LIKE '08%' 
            THEN '+628' || SUBSTRING(REGEXP_REPLACE(NULLIF(TRIM(rp.mobile), ''), '\D', '', 'g') FROM 3)
            WHEN REGEXP_REPLACE(NULLIF(TRIM(rp.mobile), ''), '\D', '', 'g') LIKE '628%'
            THEN '+628' || SUBSTRING(REGEXP_REPLACE(NULLIF(TRIM(rp.mobile), ''), '\D', '', 'g') FROM 4)
            WHEN NULLIF(TRIM(rp.mobile), '') LIKE '+628%'
            THEN NULLIF(TRIM(rp.mobile), '')
            ELSE '' 
        END AS "mobile_std",
        -- Clean Email
        CASE 
            WHEN rp.email IS NULL OR TRIM(rp.email) = '' THEN ''
            WHEN LOWER(TRIM(rp.email)) NOT LIKE '%@%.%' THEN ''
            WHEN LOWER(TRIM(rp.email)) ~ '\y(test|dummy|none|noemail|x|y|a|email|gmail)\y' THEN ''
            ELSE COALESCE(REGEXP_REPLACE(TRIM(rp.email), '[
	]+', ' ', 'g'), '')
        END AS "email",
        COALESCE(REGEXP_REPLACE(TRIM(rp.website), '[
	]+', ' ', 'g'), '') AS "website",
        COALESCE(REGEXP_REPLACE(TRIM(rp.comment), '[
	]+', ' ', 'g'), '') AS "comment",
        CASE WHEN rp.branch IS TRUE THEN 'internal' ELSE 'external' END AS "route_type",
        -- Category ID (Tags)
        CONCAT_WS(',', CASE WHEN rp.customer THEN 'Customer' END, CASE WHEN rp.biro_jasa THEN 'Birojasa' END, CASE WHEN rp.ahass THEN 'AHASS' END, CASE WHEN rp.is_bank THEN 'Bank' END, CASE WHEN rp.branch THEN 'Branch' END, CASE WHEN rp.direct_customer THEN 'Direct Customer' END, CASE WHEN rp.dealer THEN 'Dealer' END, CASE WHEN rp.is_fintech THEN 'Fintech' END, CASE WHEN rp.is_one_time_supplier THEN 'One Time Supplier' END, CASE WHEN rp.principle THEN 'Principle' END, CASE WHEN rp.forwarder THEN 'Forwarder' END, CASE WHEN rp.supplier THEN 'General Supplier' END, CASE WHEN rp.showroom THEN 'Showroom' END, CASE WHEN rp.finance_company THEN 'Finance Company' END) AS "category_id",
        CASE WHEN rp.is_fintech THEN 'TRUE' ELSE 'FALSE' END AS "is_fintech",
        CASE WHEN rp.pkp THEN 'TRUE' ELSE 'FALSE' END AS "is_pkp",
        -- NPWP Validation (Mendukung 15 dan 16 Digit)
        CASE 
            WHEN REGEXP_REPLACE(NULLIF(TRIM(rp.npwp), ''), '\D', '', 'g') ~ '(\d)\1{6,}' THEN ''
            WHEN REGEXP_REPLACE(NULLIF(TRIM(rp.npwp), ''), '\D', '', 'g') = '123456789012345' THEN ''
            WHEN LENGTH(REGEXP_REPLACE(NULLIF(TRIM(rp.npwp), ''), '\D', '', 'g')) IN (15, 16) 
            THEN REGEXP_REPLACE(NULLIF(TRIM(rp.npwp), ''), '\D', '', 'g')
            ELSE '' 
        END AS "clean_npwp", 
        -- Clean Alamat PKP
        CASE 
            WHEN rp.alamat_pkp IS NULL OR TRIM(rp.alamat_pkp) = '' THEN ''
            WHEN TRIM(rp.alamat_pkp) IN ('-', '.', 'no', 'none', 'tidak ada', 'kosong', 'null') THEN ''
            ELSE COALESCE(REGEXP_REPLACE(TRIM(rp.alamat_pkp), '[
	]+', ' ', 'g'), '')
        END AS "alamat_pkp",
        CASE 
            WHEN CAST(rp.tgl_kukuh AS VARCHAR) ~ '^\d{4}-\d{2}-\d{2}' THEN SUBSTRING(CAST(rp.tgl_kukuh AS VARCHAR) FROM 1 FOR 10) 
            ELSE '' 
        END AS "tgl_pengukuhan",
        -- KTP Validation (Penyaringan Angka Palsu & Kode Wilayah)
        CASE 
            WHEN REGEXP_REPLACE(NULLIF(TRIM(rp.no_ktp), ''), '\D', '', 'g') ~ '(\d)\1{6,}' THEN ''
            WHEN REGEXP_REPLACE(NULLIF(TRIM(rp.no_ktp), ''), '\D', '', 'g') LIKE '00%' THEN '' -- Kode wilayah tidak valid
            WHEN REGEXP_REPLACE(NULLIF(TRIM(rp.no_ktp), ''), '\D', '', 'g') = '1234567890123456' THEN ''
            WHEN LENGTH(REGEXP_REPLACE(NULLIF(TRIM(rp.no_ktp), ''), '\D', '', 'g')) = 16 
            THEN REGEXP_REPLACE(NULLIF(TRIM(rp.no_ktp), ''), '\D', '', 'g')
            ELSE '' 
        END AS "clean_ktp",
        COALESCE(REGEXP_REPLACE(TRIM(rp.no_kk), '[
	]+', ' ', 'g'), '') AS "identification_family_number",
        CASE 
            WHEN rp.birthdate IS NOT NULL AND rp.birthdate ~ '^\d{4}-\d{2}-\d{2}' THEN
                CASE 
                    WHEN DATE_PART('year', AGE(CURRENT_DATE, rp.birthdate::DATE)) >= 18 THEN rp.birthdate
                    ELSE NULL
                END
            ELSE NULL 
        END AS "birthdate",
        '' AS "another_job",
        COALESCE(mgender.target_code, '') AS "gender_id",
        COALESCE(mreligion.target_code, '') AS "religion_id",
        COALESCE(meducation.target_code, '') AS "education_id",
        COALESCE(moccupation.target_code, '') AS "occupation_id",
        COALESCE(mexpense.target_code, '') AS "expense_id",
        COALESCE(TRIM(cddb.customer_code_code), '') AS "customer_code_id",
        COALESCE(TRIM(cddb.housing_tenure_code), '') AS "housing_tenure_id",
        COALESCE(TRIM(cddb.hobby_code), '') AS "hobby_id",
        COALESCE(TRIM(cddb.blood_type_code), '') AS "blood_type_id",
        COALESCE(TRIM(cddb.motor_brand_code), '') AS "motor_brand_id",
        COALESCE(TRIM(cddb.motor_type_code), '') AS "motor_type_id",
        COALESCE(TRIM(cddb.unit_usage_code), '') AS "unit_usage_id",
        COALESCE(TRIM(cddb.unit_operator_code), '') AS "unit_operator_id",
        -- Clean Address Fields
        CASE 
            WHEN rp.street IS NULL OR TRIM(rp.street) = '' THEN ''
            WHEN TRIM(rp.street) IN ('-', '.', 'no', 'none', 'tidak ada', 'kosong', 'null') THEN ''
            ELSE COALESCE(REGEXP_REPLACE(TRIM(rp.street), '[
	]+', ' ', 'g'), '')
        END AS "street",
        CASE 
            WHEN rp.street2 IS NULL OR TRIM(rp.street2) = '' THEN ''
            WHEN TRIM(rp.street2) IN ('-', '.', 'no', 'none', 'tidak ada', 'kosong', 'null') THEN ''
            ELSE COALESCE(REGEXP_REPLACE(TRIM(rp.street2), '[
	]+', ' ', 'g'), '')
        END AS "street2",
        REGEXP_REPLACE(COALESCE(TRIM(rp.rt), ''), '\D', '', 'g') AS "rt",
        REGEXP_REPLACE(COALESCE(TRIM(rp.rw), ''), '\D', '', 'g') AS "rw",
        COALESCE(TRIM(rp.zip), '') AS "zip",
        COALESCE(TRIM(rco.code), '') AS "country_id",
        COALESCE(TRIM(rcs.code), '') AS "state_id",
        COALESCE(REGEXP_REPLACE(TRIM(rcs.name), '[
	]+', ' ', 'g'), '') AS "state_text",
        CASE WHEN TRIM(wcity.code) = '332306' THEN '3323' WHEN TRIM(wcity.code) = '3911' THEN '1607' ELSE COALESCE(TRIM(wcity.code), '') END AS "city_id",
        COALESCE(REGEXP_REPLACE(TRIM(wcity.name), '[
	]+', ' ', 'g'), COALESCE(REGEXP_REPLACE(TRIM(rp.city), '[
	]+', ' ', 'g'), ''), '') AS "city_text",
        CASE 
            WHEN TRIM(wkec.code) = '1906030' THEN '190601' 
            WHEN TRIM(wkec.code) = '3602150' THEN '360217' 
            WHEN TRIM(wkec.code) = '1371060' THEN '137103' 
            WHEN TRIM(wkec.code) = '1708080' THEN '170805' 
            WHEN TRIM(wkec.code) = '09998' THEN '317306'
            WHEN TRIM(wkec.code) = '3674061001' THEN '367306'
            WHEN TRIM(wkec.code) = '3604290' THEN '360411'
            WHEN TRIM(wkec.code) = 'PADANGSAMBIAN' THEN '517103'
            WHEN TRIM(wkec.code) = '3603030' THEN '360318'
            WHEN TRIM(wkec.code) = '3671070' THEN '367113'
            WHEN TRIM(wkec.code) = '9404180' THEN '940401'
            WHEN TRIM(wkec.code) = '740240' THEN '740326'
            WHEN TRIM(wkec.code) = '1236' THEN '317108'
            WHEN TRIM(wkec.code) = '011123' THEN '317106'
            WHEN TRIM(wkec.code) = 'PA' THEN '367303'
            WHEN TRIM(wkec.code) = '3673040' THEN '367401'
            WHEN TRIM(wkec.code) = 'TANJUNG BARAT' THEN ''
            WHEN TRIM(wkec.code) = '1308060' THEN ''
            ELSE COALESCE(TRIM(wkec.code), '') 
        END AS "district_id",
        COALESCE(REGEXP_REPLACE(TRIM(wkec.name), '[
	]+', ' ', 'g'), COALESCE(REGEXP_REPLACE(TRIM(rp.kecamatan), '[
	]+', ' ', 'g'), ''), '') AS "district_text",
        COALESCE(TRIM(wkel.code), '') AS "sub_district_id",
        COALESCE(REGEXP_REPLACE(TRIM(wkel.name), '[
	]+', ' ', 'g'), COALESCE(REGEXP_REPLACE(TRIM(rp.kelurahan), '[
	]+', ' ', 'g'), ''), '') AS "sub_district_text",
        CASE 
            WHEN rp.street_tab IS NULL OR TRIM(rp.street_tab) = '' THEN ''
            WHEN TRIM(rp.street_tab) IN ('-', '.', 'no', 'none', 'tidak ada', 'kosong', 'null') THEN ''
            ELSE COALESCE(REGEXP_REPLACE(TRIM(rp.street_tab), '[
	]+', ' ', 'g'), '')
        END AS "street_domicile",
        CASE 
            WHEN rp.street2_tab IS NULL OR TRIM(rp.street2_tab) = '' THEN ''
            WHEN TRIM(rp.street2_tab) IN ('-', '.', 'no', 'none', 'tidak ada', 'kosong', 'null') THEN ''
            ELSE COALESCE(REGEXP_REPLACE(TRIM(rp.street2_tab), '[
	]+', ' ', 'g'), '')
        END AS "street2_domicile",
        REGEXP_REPLACE(COALESCE(TRIM(rp.rt_tab), ''), '\D', '', 'g') AS "rt_domicile",
        REGEXP_REPLACE(COALESCE(TRIM(rp.rw_tab), ''), '\D', '', 'g') AS "rw_domicile",
        COALESCE(TRIM(rcs_tab.code), '') AS "state_domicile_id",
        CASE WHEN TRIM(wcity_tab.code) = '332306' THEN '3323' WHEN TRIM(wcity_tab.code) = '3911' THEN '1607' ELSE COALESCE(TRIM(wcity_tab.code), '') END AS "city_domicile_id",
        CASE 
            WHEN TRIM(wkec_tab.code) = '1906030' THEN '190601' 
            WHEN TRIM(wkec_tab.code) = '3602150' THEN '360217' 
            WHEN TRIM(wkec_tab.code) = '1371060' THEN '137103' 
            WHEN TRIM(wkec_tab.code) = '1708080' THEN '170805' 
            WHEN TRIM(wkec_tab.code) = '09998' THEN '317306'
            WHEN TRIM(wkec_tab.code) = '3674061001' THEN '367306'
            WHEN TRIM(wkec_tab.code) = '3604290' THEN '360411'
            WHEN TRIM(wkec_tab.code) = 'PADANGSAMBIAN' THEN '517103'
            WHEN TRIM(wkec_tab.code) = '3603030' THEN '360318'
            WHEN TRIM(wkec_tab.code) = '3671070' THEN '367113'
            WHEN TRIM(wkec_tab.code) = '9404180' THEN '940401'
            WHEN TRIM(wkec_tab.code) = '740240' THEN '740326'
            WHEN TRIM(wkec_tab.code) = '1236' THEN '317108'
            WHEN TRIM(wkec_tab.code) = '011123' THEN '317106'
            WHEN TRIM(wkec_tab.code) = 'PA' THEN '367303'
            WHEN TRIM(wkec_tab.code) = '3673040' THEN '367401'
            WHEN TRIM(wkec_tab.code) = 'TANJUNG BARAT' THEN ''
            WHEN TRIM(wkec_tab.code) = '1308060' THEN ''
            ELSE COALESCE(TRIM(wkec_tab.code), '') 
        END AS "district_domicile_id",
        COALESCE(TRIM(wkel_tab.code), '') AS "sub_district_domicile_id",
        COALESCE(REGEXP_REPLACE(TRIM(cddb.facebook), '[
	]+', ' ', 'g'), '') AS "facebook",
        COALESCE(REGEXP_REPLACE(TRIM(cddb.instagram), '[
	]+', ' ', 'g'), '') AS "instagram",
        COALESCE(REGEXP_REPLACE(TRIM(cddb.twitter), '[
	]+', ' ', 'g'), '') AS "twitter",
        COALESCE(REGEXP_REPLACE(TRIM(cddb.youtube), '[
	]+', ' ', 'g'), '') AS "youtube",
        COALESCE(REGEXP_REPLACE(TRIM(cddb.penanggung_jawab), '[
	]+', ' ', 'g'), '') AS "responsible",
        COALESCE(REGEXP_REPLACE(TRIM(cddb.suku), '[
	]+', ' ', 'g'), '') AS "ethnic_group",
        COALESCE(REGEXP_REPLACE(TRIM(rp.rl_bri_number), '[
	]+', ' ', 'g'), '') AS "nomor_rl_bri",
        COALESCE(REGEXP_REPLACE(TRIM(rp.rl_permata_number), '[
	]+', ' ', 'g'), '') AS "nomor_rl_permata",
        COALESCE(REGEXP_REPLACE(TRIM(rp.jadwal_hari_pengiriman), '[
	]+', ' ', 'g'), '') AS "hari_pengiriman_sparepart",
        rp.credit_limit_sparepart AS "credit_limit_sparepart",
        rp.credit_limit_unit AS "credit_limit_unit",
        rp.drawdown_sparepart AS "drawdown_sparepart",
        rp.drawdown AS "drawdown",
        COALESCE(REGEXP_REPLACE(TRIM(aa_rec.code || ' ' || aa_rec.name), '[
	]+', ' ', 'g'), '') AS "account_receivable",
        COALESCE(REGEXP_REPLACE(TRIM(aa_pay.code || ' ' || aa_pay.name), '[
	]+', ' ', 'g'), '') AS "account_payable",
        COALESCE(CASE 
            WHEN TRIM(apt_term.name) = '30 Net Days' THEN '30 Days' 
            WHEN TRIM(apt_term.name) = '1 Day' THEN 'Immediate Payment' 
            ELSE REGEXP_REPLACE(TRIM(apt_term.name), E'[\r\n\t]+', ' ', 'g') 
        END, '') AS "customer_payment_term",
        COALESCE(CASE 
            WHEN TRIM(apt_sup.name) = '30 Net Days' THEN '30 Days' 
            WHEN TRIM(apt_sup.name) = '1 Day' THEN 'Immediate Payment' 
            ELSE REGEXP_REPLACE(TRIM(apt_sup.name), E'[\r\n\t]+', ' ', 'g') 
        END, '') AS "vendor_payment_term"
    FROM FilteredPartners rp
    LEFT JOIN wtc_city wcity ON wcity.id = rp.city_id AND wcity.active IS TRUE
    LEFT JOIN wtc_kecamatan wkec ON wkec.id = rp.kecamatan_id AND wkec.active IS TRUE
    LEFT JOIN wtc_kelurahan wkel ON wkel.id = rp.zip_id AND wkel.active IS TRUE
    LEFT JOIN res_country_state rcs ON rcs.id = rp.state_id
    LEFT JOIN res_country rco ON rco.id = rp.country_id
    LEFT JOIN wtc_city wcity_tab ON wcity_tab.id = rp.city_tab_id AND wcity_tab.active IS TRUE
    LEFT JOIN wtc_kecamatan wkec_tab ON wkec_tab.id = rp.kecamatan_tab_id AND wkec_tab.active IS TRUE
    LEFT JOIN wtc_kelurahan wkel_tab ON wkel_tab.id = rp.zip_tab_id AND wkel_tab.active IS TRUE
    LEFT JOIN res_country_state rcs_tab ON rcs_tab.id = rp.state_tab_id
    LEFT JOIN wtc_branch wb ON wb.id = rp.branch_id
    LEFT JOIN LatestCDDB cddb ON cddb.customer_id = rp.id
    LEFT JOIN SelectionMapping mgender ON mgender.category = 'gender' AND mgender.source_text = LOWER(TRIM(rp.gender))
    LEFT JOIN SelectionMapping mreligion ON mreligion.category = 'religion' AND mreligion.source_text = LOWER(TRIM(rp.religion))
    LEFT JOIN SelectionMapping meducation ON meducation.category = 'education' AND meducation.source_text = LOWER(TRIM(rp.pendidikan))
    LEFT JOIN SelectionMapping moccupation ON moccupation.category = 'occupation' AND moccupation.source_text = LOWER(TRIM(rp.pekerjaan))
    LEFT JOIN SelectionMapping mexpense ON mexpense.category = 'expense' AND mexpense.source_text = LOWER(TRIM(rp.pengeluaran))
    -- Optimized Property Joins (Eliminates Correlated Subqueries)
    LEFT JOIN ir_property ip_rec ON ip_rec.name = 'property_account_receivable' 
        AND ip_rec.res_id = 'res.partner,' || rp.id 
        AND ip_rec.company_id = rp.company_id
    LEFT JOIN ir_property ip_rec_glob ON ip_rec_glob.name = 'property_account_receivable' 
        AND ip_rec_glob.res_id IS NULL 
        AND ip_rec_glob.company_id = rp.company_id
    LEFT JOIN account_account aa_rec ON aa_rec.id = CAST(REPLACE(NULLIF(COALESCE(ip_rec.value_reference, ip_rec_glob.value_reference), ''), 'account.account,', '') AS INTEGER)

    LEFT JOIN ir_property ip_pay ON ip_pay.name = 'property_account_payable' 
        AND ip_pay.res_id = 'res.partner,' || rp.id 
        AND ip_pay.company_id = rp.company_id
    LEFT JOIN ir_property ip_pay_glob ON ip_pay_glob.name = 'property_account_payable' 
        AND ip_pay_glob.res_id IS NULL 
        AND ip_pay_glob.company_id = rp.company_id
    LEFT JOIN account_account aa_pay ON aa_pay.id = CAST(REPLACE(NULLIF(COALESCE(ip_pay.value_reference, ip_pay_glob.value_reference), ''), 'account.account,', '') AS INTEGER)

    LEFT JOIN ir_property ip_term ON ip_term.name = 'property_payment_term' 
        AND ip_term.res_id = 'res.partner,' || rp.id 
        AND ip_term.company_id = rp.company_id
    LEFT JOIN ir_property ip_term_glob ON ip_term_glob.name = 'property_payment_term' 
        AND ip_term_glob.res_id IS NULL 
        AND ip_term_glob.company_id = rp.company_id
    LEFT JOIN account_payment_term apt_term ON apt_term.id = CAST(REPLACE(NULLIF(COALESCE(ip_term.value_reference, ip_term_glob.value_reference), ''), 'account.payment.term,', '') AS INTEGER)

    LEFT JOIN ir_property ip_sup ON ip_sup.name = 'property_supplier_payment_term' 
        AND ip_sup.res_id = 'res.partner,' || rp.id 
        AND ip_sup.company_id = rp.company_id
    LEFT JOIN ir_property ip_sup_glob ON ip_sup_glob.name = 'property_supplier_payment_term' 
        AND ip_sup_glob.res_id IS NULL 
        AND ip_sup_glob.company_id = rp.company_id
    LEFT JOIN account_payment_term apt_sup ON apt_sup.id = CAST(REPLACE(NULLIF(COALESCE(ip_sup.value_reference, ip_sup_glob.value_reference), ''), 'account.payment.term,', '') AS INTEGER)
),
MobileFilter AS (
    SELECT 
        *,
        FIRST_VALUE(norm_name) OVER (
            PARTITION BY NULLIF(mobile_std, '') 
            ORDER BY 
                CASE WHEN clean_ktp != '' THEN 2 ELSE 0 END + CASE WHEN clean_npwp != '' THEN 1 ELSE 0 END DESC, 
                raw_id DESC
        ) AS primary_mobile_name
    FROM RawData
),
FilledIdentities AS (
    SELECT 
        *,
        CASE 
            WHEN NULLIF(mobile_std, '') IS NOT NULL 
                 AND norm_name != '' AND primary_mobile_name != '' 
                 AND LEFT(norm_name, 3) != LEFT(primary_mobile_name, 3) 
            THEN '' 
            ELSE mobile_std 
        END AS valid_mobile_std,
        
        COALESCE(
            NULLIF(clean_ktp, ''),
            MAX(NULLIF(clean_ktp, '')) OVER (PARTITION BY 
                COALESCE(
                    NULLIF(CASE WHEN NULLIF(mobile_std, '') IS NOT NULL AND norm_name != '' AND primary_mobile_name != '' AND LEFT(norm_name, 3) != LEFT(primary_mobile_name, 3) THEN '' ELSE mobile_std END, ''),
                    'NO_MOB_' || raw_id::VARCHAR
                )
            )
        ) AS filled_ktp,
        COALESCE(
            NULLIF(clean_npwp, ''),
            MAX(NULLIF(clean_npwp, '')) OVER (PARTITION BY 
                COALESCE(
                    NULLIF(CASE WHEN NULLIF(mobile_std, '') IS NOT NULL AND norm_name != '' AND primary_mobile_name != '' AND LEFT(norm_name, 3) != LEFT(primary_mobile_name, 3) THEN '' ELSE mobile_std END, ''),
                    'NO_MOB_' || raw_id::VARCHAR
                )
            )
        ) AS filled_npwp
    FROM MobileFilter
),
PreRankedData AS (
    SELECT 
        *,
        CASE 
            -- 0. Code / Reference kembar mutlak terhitung duplikat (HANYA jika code tersebut dipakai > 1 baris)
            WHEN code_count > 1 AND NULLIF(TRIM("code"), '') IS NOT NULL AND TRIM("code") !~ '^(0|-|\.)$' THEN 'CODE_' || LOWER(TRIM("code"))

            -- 1. Instansi/Perusahaan (Company-like) dikelompokkan berdasarkan nama saja agar unik
            WHEN (is_company OR LOWER("name") ~* '\y(pt|cv|ud|toko|pd|koperasi|yayasan|group|tbk|firma|perum|agency|asuransi|finance|cv\.|pt\.)\y') AND norm_name != '' 
            THEN 'COMPANY_' || norm_name

            -- 2. NPWP Valid (NPWP adalah pengenal pajak unik badan/perorangan)
            WHEN LENGTH(filled_npwp) >= 15 AND filled_npwp !~ '^(.)\1+$' THEN 'NPWP_' || filled_npwp

            -- 3. KTP Valid (untuk perorangan)
            WHEN LENGTH(filled_ktp) = 16 AND filled_ktp !~ '^(.)\1+$' THEN 'KTP_' || filled_ktp

            -- 4. Nama + Alamat identik (Sangat kuat, bahkan menimpa Mobile jika kosong/berbeda di salah satu)
            -- Menggunakan 20 karakter pertama dari alamat yang sudah dibersihkan untuk mentolerir perbedaan kecil di ujung teks
            WHEN norm_name != '' AND LENGTH(REGEXP_REPLACE(LOWER(TRIM("street")), '[^a-z0-9]', '', 'g')) >= 10
            THEN 'NAME_STR_' || norm_name || '_' || SUBSTRING(REGEXP_REPLACE(LOWER(TRIM("street")), '[^a-z0-9]', '', 'g') FROM 1 FOR 20)

            -- 5. Mobile Valid
            WHEN valid_mobile_std != '' THEN 'MOBILE_' || valid_mobile_std

            -- 6. Fallback ke Nama (jika tidak ada KTP/Mobile/NPWP/Alamat Valid)
            WHEN norm_name != '' AND default_code LIKE '%-%' THEN 'NAME_' || norm_name || '_' || LOWER(TRIM(default_code))
            WHEN norm_name != '' THEN 'NAME_' || norm_name
            ELSE 'ID_' || CAST(raw_id AS VARCHAR) 
        END AS alasan_gabung,
        (
            CASE WHEN LENGTH(clean_npwp) >= 15 THEN 2 ELSE 0 END +
            CASE WHEN LENGTH(clean_ktp) = 16 THEN 2 ELSE 0 END +
            CASE WHEN valid_mobile_std != '' THEN 1 ELSE 0 END +
            CASE WHEN email != '' THEN 1 ELSE 0 END +
            CASE WHEN street != '' THEN 1 ELSE 0 END
        ) AS kelengkapan_score
    FROM FilledIdentities
),
RankedData AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY alasan_gabung
            ORDER BY 
                CASE WHEN "name" IS NULL OR TRIM("name") = '' OR TRIM("name") ~ '^[^a-zA-Z0-9]+$' THEN 0 ELSE 1 END DESC,
                CASE WHEN LENGTH(TRIM("code")) = 3 THEN 2 WHEN NULLIF(TRIM("code"), '') IS NOT NULL THEN 1 ELSE 0 END DESC,
                kelengkapan_score DESC,
                raw_id DESC 
        ) as rn,
        FIRST_VALUE("code") OVER (
            PARTITION BY alasan_gabung
            ORDER BY 
                CASE WHEN "name" IS NULL OR TRIM("name") = '' OR TRIM("name") ~ '^[^a-zA-Z0-9]+$' THEN 0 ELSE 1 END DESC,
                CASE WHEN LENGTH(TRIM("code")) = 3 THEN 2 WHEN NULLIF(TRIM("code"), '') IS NOT NULL THEN 1 ELSE 0 END DESC,
                kelengkapan_score DESC,
                raw_id DESC 
        ) as kode_standarisasi
    FROM PreRankedData
)
, BankData AS (
    SELECT 
        rd.*,
        rpba.account_number AS bank_acc_number,
        REGEXP_REPLACE(rpba.account_holder, '^[\-\s=+]+', '', 'g') AS bank_acc_holder,
        rpba.flag_check_account AS bank_flag_check,
        rb.name AS bank_name,
        rd."name" AS name_sort,
        ROW_NUMBER() OVER(PARTITION BY rd.raw_id ORDER BY rpba.id ASC) as rn_bank,
        -- Nomor urut per partner (untuk batching). Semua bank row milik 1 partner mendapat nomor yang SAMA.
        DENSE_RANK() OVER (ORDER BY rd."name", rd.rn, rd.raw_id) AS partner_num
    FROM RankedData rd
    LEFT JOIN (
        -- Deduplikasi Bank Account: Ambil yang paling baru (id DESC) jika ada duplikat no rekening di bank yang sama untuk partner yang sama
        SELECT DISTINCT ON (partner_id, account_number) 
               id, partner_id, bank_id, 
               account_number, 
               account_holder, flag_check_account
        FROM res_partner_bank_account
        WHERE 1=1
          AND account_number ~ '^[0-9]+$'
          AND account_number != ''
          AND account_number NOT IN ('1234567890', '1234567899', '123456789', '0', '123456', '1111111111', '12345')
          AND account_number !~ '^(\d)\1+$'
          AND UPPER(TRIM(COALESCE(account_holder, ''))) != 'TEST'
          AND bank_id NOT IN (SELECT id FROM res_bank WHERE name ILIKE '%PT TDM METRO%' OR name ILIKE '%BPD KALTIM & KALTARA SYARIAH%')
        ORDER BY partner_id, account_number, id DESC
    ) rpba ON rpba.partner_id = rd.raw_id
    LEFT JOIN res_bank rb ON rb.id = rpba.bank_id
)
SELECT 
    CASE 
        WHEN is_user THEN '❌ DIELIMINASI (IS USER)'
        WHEN "route_type" = 'internal' THEN '❌ DIELIMINASI (IS BRANCH)'
        WHEN rn > 1 OR "name" IS NULL OR TRIM("name") = '' OR TRIM("name") ~ '^[^a-zA-Z0-9]+$' THEN '❌ DIELIMINASI'
        WHEN rn_bank > 1 THEN ''
        ELSE '✅ DIPERTAHANKAN' 
    END AS "Status Migrasi",
    CASE WHEN rn_bank = 1 THEN "id" ELSE '' END AS "External ID",
    CASE WHEN rn_bank = 1 THEN "active"::VARCHAR ELSE '' END AS "Active",
    CASE WHEN rn_bank = 1 THEN "company_type" ELSE '' END AS "Company Type",
    CASE WHEN rn_bank = 1 THEN "name" ELSE '' END AS "Name",
    CASE WHEN rn_bank = 1 THEN "code" ELSE '' END AS "Reference",
    CASE WHEN rn_bank = 1 THEN CASE WHEN "phone" != '' THEN '''' || "phone" ELSE '' END ELSE '' END AS "Phone",
    CASE WHEN rn_bank = 1 THEN CASE WHEN valid_mobile_std != '' THEN '''' || valid_mobile_std ELSE '' END ELSE '' END AS "Mobile", 
    CASE WHEN rn_bank = 1 THEN "email" ELSE '' END AS "Email",
    CASE WHEN rn_bank = 1 THEN "website" ELSE '' END AS "Website Link",
    CASE WHEN rn_bank = 1 THEN "comment" ELSE '' END AS "Notes",
    CASE WHEN rn_bank = 1 THEN "route_type" ELSE '' END AS "Route Type",
    CASE WHEN rn_bank = 1 THEN "category_id" ELSE '' END AS "Tags/External ID",
    CASE WHEN rn_bank = 1 THEN "is_fintech" ELSE '' END AS "Is Fintech",
    CASE WHEN rn_bank = 1 THEN "is_pkp" ELSE '' END AS "PKP",
    CASE WHEN rn_bank = 1 THEN CASE WHEN "clean_npwp" != '' THEN '''' || "clean_npwp" ELSE '' END ELSE '' END AS "Tax ID",
    CASE WHEN rn_bank = 1 THEN "alamat_pkp" ELSE '' END AS "Alamat PKP",
    CASE WHEN rn_bank = 1 THEN COALESCE("tgl_pengukuhan", '') ELSE '' END AS "Tanggal Pengukuhan",
    CASE WHEN rn_bank = 1 THEN CASE WHEN "clean_ktp" != '' THEN '''' || "clean_ktp" ELSE '' END ELSE '' END AS "No KTP",
    CASE WHEN rn_bank = 1 THEN CASE WHEN "identification_family_number" != '' THEN '''' || "identification_family_number" ELSE '' END ELSE '' END AS "No KK",
    CASE WHEN rn_bank = 1 AND NULLIF(TRIM("birthdate"::TEXT), '') IS NOT NULL THEN TO_CHAR("birthdate"::DATE, 'YYYY-MM-DD') ELSE '' END AS "Date of Birth",
    CASE WHEN rn_bank = 1 THEN "another_job" ELSE '' END AS "Pekerjaan Sampingan",
    CASE WHEN rn_bank = 1 THEN "gender_id" ELSE '' END AS "Jenis Kelamin/Code",
    CASE WHEN rn_bank = 1 THEN "religion_id" ELSE '' END AS "Agama/Code",
    CASE WHEN rn_bank = 1 THEN "education_id" ELSE '' END AS "Pendidikan/Code",
    CASE WHEN rn_bank = 1 THEN "occupation_id" ELSE '' END AS "Pekerjaan/Code",
    CASE WHEN rn_bank = 1 THEN "expense_id" ELSE '' END AS "Monthly Expense/Code",
    CASE WHEN rn_bank = 1 THEN "customer_code_id" ELSE '' END AS "Customer Code",
    CASE WHEN rn_bank = 1 THEN "street" ELSE '' END AS "Street",
    CASE WHEN rn_bank = 1 THEN "street2" ELSE '' END AS "Street 2",
    CASE WHEN rn_bank = 1 THEN "rt" ELSE '' END AS "RT",
    CASE WHEN rn_bank = 1 THEN "rw" ELSE '' END AS "RW",
    CASE WHEN rn_bank = 1 THEN "zip" ELSE '' END AS "Zip",
    CASE WHEN rn_bank = 1 THEN "country_id" ELSE '' END AS "Country/External ID",
    CASE WHEN rn_bank = 1 THEN "state_id" ELSE '' END AS "State/External ID",
    CASE WHEN rn_bank = 1 THEN "city_id" ELSE '' END AS "City/External ID",
    CASE WHEN rn_bank = 1 THEN "district_id" ELSE '' END AS "Kecamatan/External ID",
    CASE WHEN rn_bank = 1 THEN "sub_district_id" ELSE '' END AS "Kelurahan/External ID",
    CASE WHEN rn_bank = 1 THEN "street_domicile" ELSE '' END AS "Street (Domisili)",
    CASE WHEN rn_bank = 1 THEN "rt_domicile" ELSE '' END AS "RT (Domisili)",
    CASE WHEN rn_bank = 1 THEN "rw_domicile" ELSE '' END AS "RW (Domisili)",
    CASE WHEN rn_bank = 1 THEN "state_domicile_id" ELSE '' END AS "State (Domisili)/External ID",
    CASE WHEN rn_bank = 1 THEN "city_domicile_id" ELSE '' END AS "City (Domisili)/External ID",
    CASE WHEN rn_bank = 1 THEN "district_domicile_id" ELSE '' END AS "Kecamatan (Domisili)/External ID",
    CASE WHEN rn_bank = 1 THEN "sub_district_domicile_id" ELSE '' END AS "Kelurahan (Domisili)/External ID",
    CASE WHEN rn_bank = 1 THEN "facebook" ELSE '' END AS "Facebook",
    CASE WHEN rn_bank = 1 THEN "instagram" ELSE '' END AS "Instagram",
    CASE WHEN rn_bank = 1 THEN "twitter" ELSE '' END AS "Twitter",
    CASE WHEN rn_bank = 1 THEN "youtube" ELSE '' END AS "Youtube",
    CASE WHEN rn_bank = 1 THEN "responsible" ELSE '' END AS "Penanggung Jawab",
    CASE WHEN rn_bank = 1 THEN "ethnic_group" ELSE '' END AS "Suku",
    CASE WHEN rn_bank = 1 THEN "nomor_rl_bri" ELSE '' END AS "RL BRI Number",
    CASE WHEN rn_bank = 1 THEN "nomor_rl_permata" ELSE '' END AS "RL Permata Number",
    CASE WHEN rn_bank = 1 THEN "hari_pengiriman_sparepart" ELSE '' END AS "Jadwal Hari Pengiriman",
    CASE WHEN rn_bank = 1 THEN "credit_limit_sparepart"::VARCHAR ELSE '' END AS "Credit Limit Sparepart",
    CASE WHEN rn_bank = 1 THEN "credit_limit_unit"::VARCHAR ELSE '' END AS "Credit Limit Unit",
    CASE WHEN rn_bank = 1 THEN "drawdown_sparepart"::VARCHAR ELSE '' END AS "Drawdown Sparepart",
    CASE WHEN rn_bank = 1 THEN "drawdown"::VARCHAR ELSE '' END AS "Drawdown",
    CASE WHEN rn_bank = 1 THEN CASE WHEN "account_receivable" = '0' THEN '' ELSE "account_receivable" END ELSE '' END AS "Account Receivable/External ID",
    CASE WHEN rn_bank = 1 THEN CASE WHEN "account_payable" = '0' THEN '' ELSE "account_payable" END ELSE '' END AS "Account Payable/External ID",
    CASE WHEN rn_bank = 1 THEN CASE WHEN "customer_payment_term" = '11319999 Piutang Lainnya' THEN '' ELSE "customer_payment_term" END ELSE '' END AS "Customer Payment Terms/Name",
    CASE WHEN rn_bank = 1 THEN CASE WHEN "vendor_payment_term" = '216101 Customer Guarantee' THEN '' ELSE "vendor_payment_term" END ELSE '' END AS "Vendor Payment Terms/Name",
    
    -- Bank One2many Fields
    CASE WHEN bank_acc_number IS NOT NULL AND bank_acc_number != '' THEN '''' || bank_acc_number ELSE '' END AS "Bank Accounts/Account Number",
    COALESCE(bank_name, '') AS "Bank Accounts/Bank/Name",
    COALESCE(bank_acc_holder, '') AS "Bank Accounts/Account Holder Name",
    CASE WHEN bank_acc_number IS NOT NULL THEN 'res_partner_bank_' || bank_acc_number || '_' || CAST("raw_id" AS VARCHAR) ELSE '' END AS "Bank Accounts/External ID",
    CASE WHEN bank_acc_number IS NOT NULL THEN (CASE WHEN COALESCE(bank_flag_check, FALSE) THEN 'TRUE' ELSE 'FALSE' END) ELSE '' END AS "Bank Accounts/Cek Nama Ke Popeye",
    CASE WHEN bank_acc_number IS NOT NULL THEN '' ELSE '' END AS "Bank Accounts/Is Match Check Account",
    CASE WHEN rn_bank = 1 THEN CASE WHEN "code" != kode_standarisasi THEN "code" ELSE '' END ELSE '' END AS "Kode Awal",
    CASE WHEN rn_bank = 1 THEN CASE WHEN "code" != kode_standarisasi THEN kode_standarisasi ELSE '' END ELSE '' END AS "Kode Baru (Standarisasi)"
FROM BankData 
-- ============================================================================
-- BATCH CONTROL: Ubah range di bawah untuk mengatur batch import.
-- partner_num menomori per PARTNER (bukan per baris), sehingga 
-- semua bank account milik 1 partner dijamin tidak terpotong.
-- 
-- Contoh:
--   Batch 1: AND partner_num BETWEEN 1     AND 5000
--   Batch 2: AND partner_num BETWEEN 5001  AND 10000
--   Batch 3: AND partner_num BETWEEN 10001 AND 15000
-- ============================================================================
WHERE NOT (
    is_user 
    OR "route_type" = 'internal' 
    OR rn > 1 
    OR "name" IS NULL 
    OR TRIM("name") = '' 
    OR TRIM("name") ~ '^[^a-zA-Z0-9]+$'
)
-- AND partner_num BETWEEN 1 AND 5000
ORDER BY name_sort, rn, raw_id, rn_bank;
