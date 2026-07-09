# 📖 PANDUAN PENGGUNA OPERASI ASSET

## Daftar Isi

1. [Pendahuluan](#pendahuluan)
2. [Asset Adjustment (Penyesuaian Aset)](#asset-adjustment-penyesuaian-aset)
3. [Asset Barcode (Pencetakan Label)](#asset-barcode-pencetakan-label)
4. [Asset Disposal (Penghapusan Aset)](#asset-disposal-penghapusan-aset)
5. [Asset Mutation (Mutasi Antar Cabang)](#asset-mutation-mutasi-antar-cabang)
6. [Asset Lending & Return (Peminjaman & Pengembalian)](#asset-lending--return-peminjaman--pengembalian)
7. [FAQ - Pertanyaan Umum](#faq---pertanyaan-umum)

---

## Pendahuluan

### Tentang Dokumen Ini

Dokumen ini adalah **lanjutan** dari Panduan Asset Management yang membahas proses akuisisi aset. Dokumen ini membahas **operasi lanjutan** setelah aset tercatat dalam sistem, yaitu:

| Modul                      | Fungsi                                 |
| -------------------------- | -------------------------------------- |
| **Asset Adjustment**       | Mengubah data aset yang sudah tercatat |
| **Asset Barcode**          | Mencetak label identitas aset          |
| **Asset Disposal**         | Menghapus aset (jual/buang)            |
| **Asset Mutation**         | Memindahkan aset antar cabang          |
| **Asset Lending & Return** | Meminjam dan mengembalikan aset        |

### Hubungan Antar Modul

```
                         ┌─────────────────────┐
                         │    MASTER ASSET     │
                         │ (Aset yang tercatat)│
                         └──────────┬──────────┘
                                    │
     ┌──────────────┬───────────────┼───────────────┬──────────────┐
     │              │               │               │              │
     ▼              ▼               ▼               ▼              ▼
┌─────────┐  ┌───────────┐  ┌─────────────┐  ┌──────────┐  ┌────────────┐
│ADJUSTMENT│  │  BARCODE  │  │  DISPOSAL   │  │ MUTATION │  │LENDING/    │
│(Ubah)    │  │ (Label)   │  │ (Hapus)     │  │(Pindah)  │  │RETURN      │
└─────────┘  └───────────┘  └─────────────┘  └──────────┘  │(Pinjam)    │
                                                           └────────────┘
```

---

## Asset Adjustment (Penyesuaian Aset)

### Apa itu Asset Adjustment?

Asset Adjustment adalah proses **mengubah data aset** yang sudah tercatat dalam sistem. Perubahan ini bisa berupa perubahan nilai, kategori, cabang pemilik, atau periode depresiasi.

### Kapan Menggunakan Asset Adjustment?

| Alasan                      | Contoh Kasus                                  |
| --------------------------- | --------------------------------------------- |
| **Koreksi kesalahan**       | Salah input nilai atau kategori saat akuisisi |
| **Kapitalisasi**            | Menambah nilai aset (misal: upgrade komputer) |
| **Pindah cabang**           | Aset dipindahkan kepemilikan ke cabang lain   |
| **Ubah periode depresiasi** | Estimasi masa pakai berubah                   |
| **Ganti pengguna**          | Aset berpindah tangan ke karyawan lain        |

### Cara Mengakses Menu

```
Menu: Asset Management → Asset Adjustment → Asset Adjustment
```

### Cara Membuat Asset Adjustment

1. **Klik "New"**
2. **Pilih Branch** — Cabang pemilik aset saat ini
3. **Pilih Asset No** — Aset yang akan diubah
4. **Data saat ini otomatis terisi** — Category, Value, dll.
5. **Isi perubahan** di kolom "New ..."
6. **Jika ada kapitalisasi**, isi Tab Kapitalisasi
7. **Klik "Post Adjustment"** untuk menerapkan perubahan

### Penjelasan Field-field

#### Bagian Header

| Field        | Keterangan                   |
| ------------ | ---------------------------- |
| **Branch**   | Cabang pemilik aset saat ini |
| **Date**     | Tanggal adjustment           |
| **Asset No** | Pilih aset yang akan diubah  |

#### Bagian Data Saat Ini vs Perubahan

| Field Saat Ini         | Field Perubahan                | Keterangan                 |
| ---------------------- | ------------------------------ | -------------------------- |
| Category               | **New Category**               | Kategori aset              |
| Gross Value            | **New Gross Value**            | Nilai perolehan aset       |
| Number of Depreciation | **New Number of Depreciation** | Periode depresiasi (bulan) |
| Branch                 | **New Branch**                 | Cabang pemilik             |
| Effective Date         | **New Effective Date**         | Tanggal efektif            |
| Pengguna Asset         | **New Pengguna Asset**         | Karyawan pengguna          |

> [!NOTE] > **Tidak wajib mengubah semua field!**  
> Cukup isi field "New ..." yang ingin diubah saja. Field yang tidak diubah akan tetap sama.

#### Bagian Opsi Jurnal

| Field                          | Keterangan                                                 |
| ------------------------------ | ---------------------------------------------------------- |
| **Create Journal Category**    | ☑️ Centang jika perubahan kategori perlu dicatat di jurnal |
| **Create Journal Gross Value** | ☑️ Centang jika perubahan nilai perlu dicatat di jurnal    |
| **Create Journal Branch**      | ☑️ Centang jika perpindahan cabang perlu dicatat di jurnal |

> [!IMPORTANT] > **Kapan TIDAK centang opsi jurnal?**
>
> - Jika perubahan hanya koreksi data internal tanpa dampak akuntansi
> - Jika jurnal sudah dibuat manual di sistem lain

#### Tab Kapitalisasi (Opsional)

Tab ini digunakan untuk **menambah nilai aset** dari penerimaan barang (GR) yang belum ter-akuisisi.

| Field            | Keterangan                         |
| ---------------- | ---------------------------------- |
| **Good Receive** | Pilih GR yang berisi item tambahan |
| **GR Line**      | Pilih item dari GR tersebut        |
| **Qty**          | Jumlah yang dikapitalisasi         |
| **Price**        | Harga per unit                     |

**Contoh Penggunaan:**

```
Aset: Laptop Dell (Nilai: Rp 15.000.000)
Kapitalisasi: RAM Tambahan dari GR (Rp 1.000.000)

Hasil:
- New Gross Value = 15.000.000 + 1.000.000 = 16.000.000
- Depresiasi akan dihitung ulang dengan nilai baru
```

> [!WARNING] > **Perhatian Kapitalisasi!**
>
> - Qty tidak boleh melebihi Qty Available di GR Line
> - GR Line yang sudah dipakai di Adjustment lain tidak bisa dipakai lagi
> - Setelah di-post, GR Line akan ter-mark sebagai "acquired"

### Apa yang Terjadi Saat Post Adjustment?

1. **Data aset diupdate** sesuai perubahan
2. **Journal entry dibuat** (jika opsi dicentang):
   - Perubahan kategori → Pindah buku dari akun lama ke baru
   - Perubahan nilai → Debit/Credit sesuai selisih
   - Perubahan cabang → Transfer antar company
3. **Catch-up Depreciation dihitung** — Jika nilai berubah, depresiasi yang sudah lewat disesuaikan
4. **Jadwal depresiasi dihitung ulang**

### Status Adjustment

| Status     | Keterangan                       |
| ---------- | -------------------------------- |
| **Draft**  | Belum di-post, masih bisa diedit |
| **Posted** | Sudah di-post, tidak bisa diubah |

---

## Asset Barcode (Pencetakan Label)

### Apa itu Asset Barcode?

Asset Barcode adalah modul untuk **mencetak label identitas aset** berupa QR Code. Label ini ditempel pada fisik aset untuk memudahkan identifikasi dan stock take.

### Mengapa Perlu Label Barcode?

| Manfaat                | Keterangan                         |
| ---------------------- | ---------------------------------- |
| **Identifikasi cepat** | Scan QR = langsung tahu info aset  |
| **Stock take mudah**   | Tidak perlu catat manual           |
| **Audit trail**        | Bukti aset sudah ter-register      |
| **Tracking lokasi**    | Mudah cari aset berdasarkan lokasi |

### Cara Mengakses Menu

```
Menu: Asset Management → Asset Barcode → Print Label Asset
```

### Cara Mencetak Label

1. **Klik "New"** untuk membuat sesi pencetakan baru
2. **Pilih Filter:**
   - **Dealer** — Pilih cabang (bisa lebih dari 1)
   - **Asset Code** — Pilih kategori aset atau "ALL"
   - **Label Status** — Terlabel / Tidak / Semua
3. **Klik "Listing Asset"** — Daftar aset muncul
4. **Centang aset yang akan dicetak** — Kolom "Print"
5. **Klik "Print Barcode Label"** — PDF label siap cetak

### Penjelasan Field-field Filter

| Field            | Keterangan                                  | Default        |
| ---------------- | ------------------------------------------- | -------------- |
| **Dealer**       | Cabang mana yang mau dicetak (multi-select) | -              |
| **Asset Code**   | Kategori aset (ALL = semua kategori)        | ALL            |
| **Label Status** | Status label aset                           | Tidak Terlabel |

### Penjelasan Kolom Hasil Listing

| Kolom             | Keterangan                            |
| ----------------- | ------------------------------------- |
| **Print**         | Centang untuk mencetak label aset ini |
| **Asset Number**  | Nomor registrasi aset                 |
| **Asset Code**    | Kode aset                             |
| **Asset Name**    | Nama produk/aset                      |
| **Category**      | Kategori aset                         |
| **Purchase Date** | Tanggal pembelian                     |
| **Partner**       | Vendor asal pembelian                 |
| **Status**        | Terlabel / Tidak Terlabel             |

### Tips Penggunaan

> [!TIP] > **Cetak Batch untuk Aset Baru:**
>
> 1. Filter: Label Status = "Tidak Terlabel"
> 2. Listing Asset
> 3. Klik "Checklist All" untuk centang semua
> 4. Print

> [!NOTE] > **Setelah label dicetak dan ditempel:**  
> Status aset otomatis berubah menjadi "Terlabel" sehingga tidak muncul lagi di filter "Tidak Terlabel".

---

## Asset Disposal (Penghapusan Aset)

### Apa itu Asset Disposal?

Asset Disposal adalah proses **mengeluarkan aset dari daftar aktif perusahaan**. Aset yang di-dispose tidak lagi didepresiasi dan dianggap tidak ada.

### Tipe Disposal

| Tipe      | Keterangan                | Dampak Finansial                       |
| --------- | ------------------------- | -------------------------------------- |
| **Sold**  | Aset dijual ke pihak lain | Ada penerimaan uang (Other Receivable) |
| **Scrap** | Aset dibuang/rusak        | Nilai sisa masuk beban (Expense)       |

### Cara Mengakses Menu

```
Menu: Asset Management → Asset Disposal → Asset Disposal
```

### Cara Membuat Disposal - Type SOLD

1. **Klik "New"**
2. **Pilih Type = "Sold"**
3. **Pilih Branch**
4. **Pilih Partner** — Siapa yang membeli aset
5. **Isi Payment Terms** — Termin pembayaran
6. **Tambah item di Tab "Disposal Sold Lines":**
   - Pilih Asset
   - Isi Amount (harga jual)
   - Pilih Tax
7. **Isi Tab "Alokasi Hutang Lain"** — WAJIB untuk type Sold
8. **Klik "Confirm"**

### Cara Membuat Disposal - Type SCRAP

1. **Klik "New"**
2. **Pilih Type = "Scrap"**
3. **Pilih Branch**
4. **Tambah item di Tab "Disposal Scrap Lines":**
   - Pilih Asset
   - Isi Note (alasan scrap)
5. **Klik "Confirm"**

### Penjelasan Field-field

#### Bagian Header

| Field              | Keterangan              | Wajib Sold | Wajib Scrap |
| ------------------ | ----------------------- | ---------- | ----------- |
| **Type**           | Sold atau Scrap         | ✅         | ✅          |
| **Branch**         | Cabang pemilik aset     | ✅         | ✅          |
| **Date**           | Tanggal disposal        | ✅         | ✅          |
| **Partner**        | Pembeli (untuk Sold)    | ✅         | ❌          |
| **Payment Terms**  | Termin pembayaran       | ❌         | ❌          |
| **Invoice Number** | Nomor invoice penjualan | ❌         | ❌          |

#### Tab Disposal Lines

| Field      | Keterangan                      |
| ---------- | ------------------------------- |
| **Asset**  | Pilih aset yang akan di-dispose |
| **Amount** | Harga jual (untuk Sold)         |
| **Tax**    | Pajak yang berlaku (PPN)        |
| **Note**   | Catatan/alasan disposal         |

#### Tab Alokasi Hutang Lain (Khusus SOLD)

> [!CAUTION] > **Wajib diisi untuk Type SOLD!**  
> Total alokasi harus sama dengan Amount Total penjualan.

| Field                | Keterangan                                   |
| -------------------- | -------------------------------------------- |
| **HL (Hutang Lain)** | Pilih record Hutang Lain                     |
| **HL Balance**       | Saldo HL yang tersedia                       |
| **Allocation**       | Jumlah yang dialokasikan untuk penjualan ini |

### Apa yang Terjadi Saat Confirm Disposal?

#### Untuk Type SOLD:

```
Journal Entry:
┌─────────────────────────────┬──────────────┬──────────────┐
│ Akun                        │ Debit        │ Credit       │
├─────────────────────────────┼──────────────┼──────────────┤
│ Other Receivable            │ Harga Jual   │              │
│ Akumulasi Penyusutan        │ Akum. Depr   │              │
│ Aset Tetap                  │              │ Nilai Buku   │
│ Gain/Loss Disposal          │ Loss / (Gain)│              │
│ PPN Out                     │              │ Pajak        │
└─────────────────────────────┴──────────────┴──────────────┘
```

**Perhitungan Gain/Loss:**

```
Gain/Loss = Harga Jual (sebelum pajak) - Nilai Buku Aset

Jika positif = Gain (Keuntungan) → Credit
Jika negatif = Loss (Kerugian) → Debit
```

#### Untuk Type SCRAP:

```
Journal Entry:
┌─────────────────────────────┬──────────────┬──────────────┐
│ Akun                        │ Debit        │ Credit       │
├─────────────────────────────┼──────────────┼──────────────┤
│ Akumulasi Penyusutan        │ Akum. Depr   │              │
│ Expense Asset               │ Nilai Sisa   │              │
│ Aset Tetap                  │              │ Nilai Buku   │
└─────────────────────────────┴──────────────┴──────────────┘
```

### Status Disposal

| Status        | Keterangan                           |
| ------------- | ------------------------------------ |
| **Draft**     | Belum dikonfirmasi                   |
| **Confirmed** | Sudah dikonfirmasi, aset ter-dispose |
| **Cancelled** | Dibatalkan                           |

---

## Asset Mutation (Mutasi Antar Cabang)

### Apa itu Asset Mutation?

Asset Mutation adalah proses **memindahkan aset dari satu cabang ke cabang lain**. Proses ini melibatkan dua pihak: cabang pengirim dan cabang penerima.

### Mengapa Perlu Proses Terpisah?

| Tahap                         | Keterangan                            |
| ----------------------------- | ------------------------------------- |
| **Mutation (Request)**        | Cabang penerima mengajukan permintaan |
| **Distribution (Penerimaan)** | Cabang pengirim konfirmasi penerimaan |

Proses terpisah memastikan **kedua pihak mengkonfirmasi** perpindahan aset.

### Cara Mengakses Menu

```
Menu: Asset Management → Asset Mutation → Mutation Request (untuk request)
Menu: Asset Management → Asset Mutation → Distribution Asset (untuk terima)
```

### Flow Mutasi Asset

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FLOW MUTASI ASSET                            │
└─────────────────────────────────────────────────────────────────────┘

  CABANG PENERIMA                           CABANG PENGIRIM
  ================                          ================

  ┌───────────────────┐
  │ 1. Buat Mutation  │
  │    Request        │
  │    (Minta aset)   │
  └─────────┬─────────┘
            │
            │ Confirm
            ▼
  ┌───────────────────┐                   ┌───────────────────┐
  │ 2. Status = Open  │ ─────────────────►│ 3. Muncul di menu │
  │    Distribution   │  Auto-create      │    Distribution   │
  │    dibuat         │                   │    Asset          │
  └───────────────────┘                   └─────────┬─────────┘
                                                    │
                                                    │ Confirm
                                                    ▼
                                          ┌───────────────────┐
                                          │ 4. Asset Adjust-  │
                                          │    ment dibuat    │
                                          │    (ganti branch) │
                                          └─────────┬─────────┘
                                                    │
                                                    │
                                                    ▼
  ┌───────────────────┐                   ┌───────────────────┐
  │ 5. Status = Done  │◄──────────────────│ 5. Stock Picking  │
  │    Aset sudah     │                   │    dibuat         │
  │    pindah         │                   │                   │
  └───────────────────┘                   └───────────────────┘
```

### Cara Membuat Mutation Request (Cabang Penerima)

1. **Klik "New"**
2. **Pilih Branch Sender** — Cabang yang memiliki aset saat ini
3. **Pilih Branch Request** — Cabang yang minta aset (otomatis terisi cabang Anda)
4. **Tambah Detail:**
   - Pilih Asset
   - Pilih Location Asset (lokasi aset saat ini)
   - Isi New Pengguna (opsional, jika pengguna berubah)
   - Isi Note
5. **Klik "Confirm"**

### Penjelasan Field Mutation Request

| Field              | Keterangan                          |
| ------------------ | ----------------------------------- |
| **Branch Sender**  | Cabang yang mengirim aset           |
| **Branch Request** | Cabang yang menerima aset           |
| **PIC Asset**      | Penanggung jawab di cabang pengirim |
| **Date**           | Tanggal request                     |

#### Tab Detail

| Field              | Keterangan                              |
| ------------------ | --------------------------------------- |
| **Asset**          | Aset yang diminta                       |
| **Code**           | Kode aset (otomatis)                    |
| **Category**       | Kategori aset (otomatis)                |
| **Location Asset** | Lokasi fisik aset saat ini              |
| **New Pengguna**   | Pengguna baru setelah pindah (opsional) |
| **Note**           | Catatan                                 |

### Cara Konfirmasi Distribution (Cabang Pengirim)

1. **Buka menu "Distribution Asset"**
2. **Cari distribution dengan status "Requested"**
3. **Review detail aset yang akan dikirim**
4. **Isi PIC Asset** — Penanggung jawab pengiriman
5. **Pastikan Location Asset terisi** — Wajib!
6. **Klik "Confirm"**

### Apa yang Terjadi Saat Distribution Dikonfirmasi?

1. **Asset Adjustment dibuat** — Mengubah company_id aset
2. **Stock Picking dibuat** — Perpindahan stok/fisik
3. **Pengguna aset diupdate** — Jika new_employee_user_id diisi
4. **Status Mutation = Done**
5. **Status Distribution = Done**

### Status Mutation & Distribution

| Model            | Status Flow         |
| ---------------- | ------------------- |
| **Mutation**     | Draft → Open → Done |
| **Distribution** | Requested → Done    |

---

## Asset Lending & Return (Peminjaman & Pengembalian)

### Apa itu Asset Lending & Return?

Modul ini untuk mencatat **peminjaman sementara** aset oleh karyawan atau cabang lain, serta **pengembalian** aset tersebut.

### Perbedaan dengan Mutation

| Aspek        | Mutation                      | Lending                            |
| ------------ | ----------------------------- | ---------------------------------- |
| **Sifat**    | Permanen (pindah kepemilikan) | Sementara (pinjam)                 |
| **Pengguna** | Berubah permanen              | Berubah sementara, kembali ke asli |
| **Cabang**   | Berubah                       | Tetap                              |
| **Jurnal**   | Ada                           | Tidak ada                          |

### Cara Mengakses Menu

```
Menu: Asset Management → Asset Lending → Peminjaman Aset
Menu: Asset Management → Asset Lending → Pengembalian Aset
```

### Flow Peminjaman & Pengembalian

```
┌──────────────────────────────────────────────────────────────────┐
│                  FLOW PEMINJAMAN & PENGEMBALIAN                   │
└──────────────────────────────────────────────────────────────────┘

┌───────────────────┐
│ 1. Buat Lending   │
│    (Peminjaman)   │
│    Status: Draft  │
└─────────┬─────────┘
          │
          │ Confirm
          ▼
┌───────────────────┐     ┌─────────────────────────────────────┐
│ 2. Status: Open   │     │ Aset ter-flag "sedang dipinjam"     │
│    (Running)      │────►│ Pengguna berubah ke peminjam        │
│                   │     │ Original user disimpan              │
└─────────┬─────────┘     └─────────────────────────────────────┘
          │
          │ Saat dikembalikan
          ▼
┌───────────────────┐
│ 3. Buat Return    │
│    (Pengembalian) │
│    Status: Draft  │
└─────────┬─────────┘
          │
          │ Confirm
          ▼
┌───────────────────┐     ┌─────────────────────────────────────┐
│ 4. Status:        │     │ Aset ter-unflag                     │
│    Confirmed      │────►│ Pengguna kembali ke original        │
│                   │     │ Kondisi pengembalian dicatat        │
└───────────────────┘     └─────────────────────────────────────┘
          │
          ▼
┌───────────────────┐
│ 5. Lending Status │
│    = Done         │
│    (Returned)     │
└───────────────────┘
```

### Cara Membuat Peminjaman (Lending)

1. **Klik "New"**
2. **Pilih Branch** — Cabang pemilik aset
3. **Pilih Pinjam ke** — Cabang/pihak yang meminjam (opsional)
4. **Pilih Penanggung Jawab** — Karyawan yang bertanggung jawab
5. **Isi Tanggal Pinjam:**
   - **Start Date** — Tanggal mulai pinjam
   - **End Date** — Tanggal rencana kembali
6. **Tambah Detail:**
   - Pilih Asset
   - Pilih Pengguna Baru (peminjam)
   - Pilih Reason (alasan pinjam)
   - Isi Note
7. **Klik "Confirm"**

### Penjelasan Field Lending

#### Header

| Field                | Keterangan                       |
| -------------------- | -------------------------------- |
| **Branch**           | Cabang pemilik aset              |
| **Pinjam ke**        | Cabang/pihak peminjam (opsional) |
| **Penanggung Jawab** | Karyawan PJ peminjaman           |
| **Divisi**           | Divisi terkait                   |
| **Tanggal**          | Tanggal pembuatan                |
| **Start Date**       | Tanggal mulai pinjam             |
| **End Date**         | Tanggal rencana kembali          |

#### Tab Detail

| Field              | Keterangan                   |
| ------------------ | ---------------------------- |
| **Asset**          | Aset yang dipinjam           |
| **Asset Code**     | Kode aset (otomatis)         |
| **Pengguna Asset** | Pengguna saat ini (otomatis) |
| **Pengguna Baru**  | Karyawan peminjam            |
| **Reason**         | Alasan peminjaman            |
| **Note**           | Catatan tambahan             |

### Cara Membuat Pengembalian (Return)

1. **Klik "New"**
2. **Pilih Branch**
3. **Tambah Detail:**
   - Pilih Peminjaman (Lending) yang masih aktif
   - Pilih Asset dari peminjaman tersebut
   - Isi Kondisi Pengembalian
   - Isi Note
4. **Klik "Confirm"**

### Penjelasan Field Return

#### Header

| Field        | Keterangan                  |
| ------------ | --------------------------- |
| **Branch**   | Cabang pemilik aset         |
| **Employee** | Karyawan yang mengembalikan |
| **Tanggal**  | Tanggal pengembalian        |

#### Tab Detail

| Field                    | Keterangan                  |
| ------------------------ | --------------------------- |
| **Peminjaman**           | Referensi ke record Lending |
| **Asset**                | Aset yang dikembalikan      |
| **Kondisi Pengembalian** | Baik / Rusak / dll          |
| **Note**                 | Catatan pengembalian        |

### Status Lending

| Status                 | Keterangan                       |
| ---------------------- | -------------------------------- |
| **Draft**              | Belum dikonfirmasi               |
| **Running (Open)**     | Aset sedang dipinjam             |
| **Partially Returned** | Sebagian aset sudah dikembalikan |
| **Returned (Done)**    | Semua aset sudah dikembalikan    |

### Status Return

| Status        | Keterangan            |
| ------------- | --------------------- |
| **Draft**     | Belum dikonfirmasi    |
| **Confirmed** | Pengembalian tercatat |

> [!WARNING] > **Validasi Peminjaman:**
>
> - Aset yang sedang dipinjam **tidak bisa** dipinjam lagi
> - Satu aset hanya bisa ada di satu peminjaman aktif

> [!NOTE] > **Pengembalian Parsial:**  
> Jika satu Lending memiliki banyak aset, Anda bisa mengembalikan sebagian dulu. Status Lending akan menjadi "Partially Returned" hingga semua dikembalikan.

---

## FAQ - Pertanyaan Umum

### Asset Adjustment

**Q: Apakah bisa membatalkan Adjustment yang sudah di-post?**

> Tidak bisa. Jika ada kesalahan, buat Adjustment baru untuk mengoreksi.

**Q: Mengapa depresiasi pertama setelah adjustment nilainya berbeda?**

> Sistem menghitung **Catch-up Depreciation** untuk menyesuaikan depresiasi yang sudah berjalan dengan rate baru.

---

### Asset Barcode

**Q: Kertas apa yang cocok untuk label?**

> Disarankan:
>
> - Label sticker ukuran 5x3 cm
> - Kertas polyester untuk outdoor/mesin
> - Kertas HVS untuk indoor/furniture

**Q: Aset sudah dilabel tapi status masih "Tidak Terlabel"?**

> Setelah print, pastikan untuk mencentang checkbox "Is Labelled" di master aset, atau sistem akan update otomatis setelah print.

---

### Asset Disposal

**Q: Aset sudah di-dispose, tapi ternyata dijual. Bisa diubah?**

> Tidak bisa. Disposal yang sudah confirmed tidak bisa dibatalkan. Untuk kasus ini, hubungi Administrator untuk adjustment manual.

**Q: Kenapa harus isi Alokasi HL untuk type Sold?**

> Alokasi HL (Hutang Lain) adalah untuk mencatat bahwa penerimaan dari penjualan aset akan digunakan untuk membayar hutang tertentu. Ini memastikan cash flow tercatat dengan benar.

---

### Asset Mutation

**Q: Siapa yang harus konfirmasi pertama, pengirim atau penerima?**

> **Penerima duluan** — Buat Mutation Request, lalu Confirm.
> Setelah itu **Pengirim** — Buka Distribution Asset, lalu Confirm.

**Q: Kenapa aset tidak muncul di pilihan mutation?**

> Cek:
>
> 1. Aset milik cabang pengirim yang dipilih
> 2. Status aset "Running" (tidak dalam status CIP/Draft/Disposed)
> 3. Aset tidak sedang dipinjam

---

### Asset Lending & Return

**Q: Bagaimana jika aset rusak saat dipinjam?**

> 1. Buat pengembalian dengan kondisi "Rusak"
> 2. Setelah dikembalikan, buat Disposal type Scrap jika aset tidak bisa diperbaiki

**Q: Bisa tidak meminjamkan ke karyawan dari cabang lain?**

> Bisa. Pilih cabang peminjam di field "Pinjam ke", lalu pilih karyawan dari cabang tersebut di Tab Detail.

**Q: Aset dikembalikan tapi pengguna tidak kembali ke original?**

> Cek apakah Return sudah di-Confirm. Pengguna baru kembali ke original setelah Return dikonfirmasi.

---

## Tips Best Practice

### ✅ Do's

1. **Adjustment** — Selalu cek preview journal sebelum post
2. **Barcode** — Cetak label segera setelah aset di-akuisisi
3. **Disposal** — Dokumentasikan kondisi aset sebelum dispose
4. **Mutation** — Pastikan kedua cabang sudah siap sebelum confirm
5. **Lending** — Isi End Date yang realistis untuk tracking

### ❌ Don'ts

1. **Adjustment** — Jangan ubah nilai tanpa alasan yang jelas
2. **Barcode** — Jangan cetak ulang label yang sudah ditempel (bikin duplikat)
3. **Disposal** — Jangan dispose aset yang masih dipinjam
4. **Mutation** — Jangan confirm distribution sebelum aset siap dikirim
5. **Lending** — Jangan biarkan peminjaman expired tanpa pengembalian

---

_Dokumen ini terakhir diperbarui: Januari 2026_  
_Versi: 1.0_
