# Proses Migrasi Data Pricelist

Panduan ini menjelaskan urutan dan cara migrasi data Pricelist (General & Service) menggunakan script SQL export dan template Excel yang telah disediakan.

## Prasyarat
Pastikan Anda memiliki akses ke database sumber untuk menjalankan query SQL dan file template Excel yang berada di folder `xlsx_import`.

## Langkah-langkah Migrasi

Proses migrasi harus dilakukan secara berurutan sebagai berikut:

### A. Pricelist General (Sales & Purchase)

#### 1. Pricelist Header
1. Buka dan jalankan script SQL: `sql_export/pricelist_export.sql`
2. Salin hasil query tersebut.
3. Buka file Excel: `xlsx_import/migration_pricelist.xlsx`
4. Tempel (Paste) data ke dalam Excel tersebut.
5. Import file Excel ke sistem Odoo.

#### 2. Pricelist Version
*Catatan: Pastikan Pricelist Header sudah berhasil diimport.*
1. Buka dan jalankan script SQL: `sql_export/pricelist_version_export.sql`
2. Salin hasil query tersebut.
3. Buka file Excel: `xlsx_import/migration_pricelist_version.xlsx`
4. Tempel (Paste) data ke dalam Excel tersebut.
5. Import file Excel ke sistem Odoo.

#### 3. Pricelist Item
*Catatan: Pastikan Pricelist Version sudah berhasil diimport.*
1. Buka dan jalankan script SQL: `sql_export/pricelist_item_export.sql`
2. Salin hasil query tersebut.
3. Buka file Excel: `xlsx_import/migration_pricelist_item.xlsx`
4. Tempel (Paste) data ke dalam Excel tersebut.
5. Import file Excel ke sistem Odoo.

### B. Pricelist Service (Harga Jasa)

1. Buka dan jalankan script SQL: `sql_export/pricelist_service_export.sql`
2. Salin hasil query tersebut.
3. Buka file Excel: `xlsx_import/migration_pricelist_service.xlsx`
4. Tempel (Paste) data ke dalam Excel tersebut.
5. Import file Excel ke sistem Odoo.

### C. Pricelist BBN

Untuk migrasi data Pricelist BBN, silakan merujuk pada dokumentasi khusus yang terdapat di module **`tw_pricelist_bbn`**.

*   Lokasi Readme: `tw_pricelist_bbn/migration/README.md`