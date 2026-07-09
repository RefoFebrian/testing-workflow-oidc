# Proses Migrasi Data Bundling

Panduan ini menjelaskan urutan dan cara migrasi data bundling menggunakan script SQL export dan template Excel yang telah disediakan.

## Prasyarat
Pastikan Anda memiliki akses ke database sumber untuk menjalankan query SQL dan file template Excel yang berada di folder `xlsx_import`.

## Langkah-langkah Migrasi

Proses migrasi harus dilakukan secara berurutan sebagai berikut:

### A. Bundling Master Data

1. Buka dan jalankan script SQL: `sql_export/tw_api_master_bundling.sql`
2. Salin hasil query tersebut.
3. Buka file Excel: `xlsx_import/migration_bundling.xlsx`
4. Tempel (Paste) data ke dalam Excel tersebut.
5. Import file Excel ke sistem Odoo.

*Catatan:* Pastikan kolom di Excel sesuai dengan field yang ada pada modul bundling.

### B. Langkah-langkah Lainnya

Jika terdapat migrasi tambahan, ikuti dokumentasi yang relevan di modul terkait.