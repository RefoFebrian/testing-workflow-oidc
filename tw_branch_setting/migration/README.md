# Proses Migrasi Data Branch Setting

Panduan ini menjelaskan urutan dan cara migrasi data Branch Setting.

## Penting: Prasyarat Utama
**SEBELUM** melakukan import pada Branch Setting, Anda **WAJIB** memastikan bahwa data Branch telah terisi dengan benar. Jika belum, lakukan proses export dan import pada module `tw_branch` terlebih dahulu.

## Langkah-langkah Migrasi Branch Setting

1. Pastikan migrasi di `tw_branch` sudah selesai.
2. Buka dan jalankan script SQL: `sql_export/branch_setting_export.sql`
3. Salin hasil query tersebut.
4. Buka file Excel: `xlsx_import/migration_branch_setting.xlsx`
5. Tempel (Paste) data ke dalam Excel tersebut.
6. Import file Excel ke sistem Odoo pada model `tw.branch.setting`.

*Catatan: Pastikan view list pada Branch Setting sudah diaktifkan mode create=true jika diperlukan untuk proses import.*
