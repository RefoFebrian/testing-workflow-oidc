# Proses Migrasi Data Pricelist BBN

Panduan ini menjelaskan urutan dan cara migrasi data Pricelist BBN menggunakan script SQL export dan template Excel yang telah disediakan.

## Prasyarat
Pastikan Anda memiliki akses ke database sumber untuk menjalankan query SQL dan file template Excel yang berada di folder `xlsx_import`.

## Langkah-langkah Migrasi

Proses migrasi harus dilakukan secara berurutan sebagai berikut:

### 1. Pricelist Header
1. Buka dan jalankan script SQL: `sql_export/pricelist_bbn_export.sql`
2. Salin hasil query tersebut.
3. Buka file Excel: `xlsx_import/migration_pricelist_bbn.xlsx`
4. Tempel (Paste) data ke dalam Excel tersebut.
5. Import file Excel ke sistem Odoo.

### 2. Pricelist Version
1. Buka dan jalankan script SQL: `sql_export/pricelist_version_bbn_export.sql`
2. Salin hasil query tersebut.
3. Buka file Excel: `xlsx_import/migration_pricelist_version_bbn.xlsx`
4. Tempel (Paste) data ke dalam Excel tersebut.
5. Import file Excel ke sistem Odoo.

5. Import file Excel ke sistem Odoo.



## Lanjutan

Setelah proses migrasi Pricelist BBN selesai, langkah selanjutnya adalah melakukan konfigurasi pada **Branch Setting**. Silakan merujuk ke folder migration pada module `tw_branch_setting` yang juga menyediakan script `sql_export` dan template `xlsx_import` terkait.




