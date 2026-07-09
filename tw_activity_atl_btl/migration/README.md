Query export for migration data titik keramaian to tw_titik_keramaian
Query export for migration data mapping titik keramaian to tw_mapping_titik_keramaian

# TODO:
# 1. Lakukan migrasi untuk Titik Keramaian terlebih dahulu
# 2. Pastikan semua data migrasi titik keramaian sudah berhasil
# 3. Lakukan migrasi untuk Mapping Titik Keramaian

Untuk migrasi data activity plan ATL & BTL, perlu di perhatikan bahwa cara migrasi data ini sedikit berbeda.
Karena data activity plan ATL & BTL ini terhubung dengan beberapa tabel.
Ketika membuka excel, Sudah ada contoh data yang di import.
pada query export, ada SELECT dengan label Header Name. Untuk mengetahui data antara header dan line bisa di uncomment SELECT Header Name dan melakukan adjustment pada export excelnya dengan cara lihat header name-nya. jika ada duplikat pada data header, berarti data setelah Header name merupakan data line-nya. hapus saja row data header yang duplikat dan pastikan.
apabila sudah di adjust, kolom Header name bisa hapus pada excel dan di commend kembali pada query export.
