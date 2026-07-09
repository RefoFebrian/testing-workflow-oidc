# 📖 PANDUAN PENGGUNA SISTEM P2P (PURCHASE TO PURCHASE)

## Daftar Isi

1. [Pendahuluan](#pendahuluan)
2. [Alur Proses P2P End-to-End](#alur-proses-p2p-end-to-end)
3. [Master Data P2P](#master-data-p2p)
4. [Membuat Transaksi P2P Purchase Order](#membuat-transaksi-p2p-purchase-order)
5. [Proses Approval P2P](#proses-approval-p2p)
6. [Integrasi MFT UPO (File Transfer ke AHM)](#integrasi-mft-upo-file-transfer-ke-ahm)
7. [Ekspor dan Impor Data](#ekspor-dan-impor-data)
8. [Pertanyaan yang Sering Diajukan (FAQ)](#pertanyaan-yang-sering-diajukan-faq)
9. [Tips dan Praktik Terbaik](#tips-dan-praktik-terbaik)

---

## Pendahuluan

### Apa Itu Sistem P2P?

Sistem P2P (Purchase to Purchase) adalah modul untuk **mengelola proses pemesanan dari ATPM (AHM - Astra Honda Motor) ke Main Dealer**. Modul ini mencakup:

1. **tw_p2p** — Modul utama untuk membuat P2P Purchase Order
2. **tw_p2p_approval** — Modul persetujuan bertingkat
3. **tw_mft_upo** — Modul integrasi file transfer ke AHM

### Mengapa Perlu Sistem Ini?

| Tanpa Sistem                    | Dengan Sistem                           |
| ------------------------------- | --------------------------------------- |
| Pemesanan manual via surel/faks | Pemesanan terintegrasi dalam sistem     |
| Tidak ada pelacakan periode     | Periode pemesanan terkelola dengan baik |
| Data tidak terstruktur          | Data terstruktur dan dapat dilacak      |
| Sulit validasi kuantitas        | Validasi otomatis berdasarkan master    |
| Tidak ada jejak audit           | Jejak audit lengkap                     |
| Buat file manual untuk AHM      | File UPO/PPO dibuat otomatis            |

### Siapa yang Menggunakan Sistem Ini?

| Pengguna                     | Fungsi                                    |
| ---------------------------- | ----------------------------------------- |
| **Staf Purchasing Showroom** | Membuat P2P Purchase Order Unit           |
| **Staf Purchasing Workshop** | Membuat P2P Purchase Order Sparepart      |
| **Admin Master Data**        | Mengelola master Periode, Product, Config |
| **Supervisor/Manager**       | Memberikan persetujuan (approval)         |
| **Tim B2B/MFT**              | Memantau pengiriman file ke AHM           |

---

## Alur Proses P2P End-to-End

Berikut adalah alur lengkap proses P2P dari awal hingga selesai:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ALUR PROSES P2P END-TO-END                        │
└─────────────────────────────────────────────────────────────────────┘

     ┌───────────────────┐
     │ PERSIAPAN         │ ← Admin mengatur master (Config, Periode, Product)
     │ Master Data       │
     └─────────┬─────────┘
               │
               ▼
     ┌───────────────────┐
     │ 1. BUAT P2P ORDER │ ← Staf Purchasing membuat P2P Purchase Order
     │ (Draft)           │
     └─────────┬─────────┘
               │
               │ Generate line / Isi data
               ▼
     ┌───────────────────┐
     │ 2. REQUEST FOR    │ ← Kirim untuk persetujuan (RFA)
     │ APPROVAL (RFA)    │
     └─────────┬─────────┘
               │
               ├─────────────────────────────┐
               │                             │
     ┌─────────▼─────────┐         ┌─────────▼─────────┐
     │ 3a. APPROVED      │         │ 3b. REJECTED      │
     │ (Disetujui)       │         │ (Ditolak)         │
     └─────────┬─────────┘         └───────────────────┘
               │
               ▼
     ┌───────────────────────┐
     │ 4. VERIFICATION       │ ← Verifikasi dan buat file UPO/PPO
     │ + File UPO Otomatis   │
     └─────────┬─────────────┘
               │
               ├─────────────────────────────┐
               │                             │
     ┌─────────▼─────────┐         ┌─────────▼─────────┐
     │ 5a. CONFIRM       │         │ 5b. REVISI        │
     │ (Dikonfirmasi)    │         │ (Perbaikan)       │
     └─────────┬─────────┘         └───────────────────┘
               │
               ▼
     ┌───────────────────┐
     │ 6. PURCHASE ORDER │ ← PO standar terbentuk
     │ TERBENTUK         │
     └─────────┬─────────┘
               │
               ▼
     ┌───────────────────┐
     │ 7. FILE UPO/PPO   │ ← File dikirim ke AHM via MFT
     │ TERKIRIM KE AHM   │
     └─────────┬─────────┘
               │
               ▼
         ✅ SELESAI
```

### Status P2P Purchase Order

| Status                       | Keterangan                   | Aksi Selanjutnya           |
| ---------------------------- | ---------------------------- | -------------------------- |
| **Draft**                    | Pesanan baru dibuat          | RFA (Request for Approval) |
| **Waiting for Approval**     | Menunggu persetujuan         | Approve atau Reject        |
| **Approved**                 | Disetujui oleh atasan        | Lanjut ke Verification     |
| **Waiting for Verification** | Menunggu verifikasi akhir    | Confirm atau Revisi        |
| **Revisi**                   | Dikembalikan untuk perbaikan | Perbaiki data, RFA ulang   |
| **Confirmed**                | Pesanan dikonfirmasi         | PO dan file UPO terbentuk  |
| **Cancel**                   | Dibatalkan                   | -                          |
| **Reject**                   | Ditolak oleh AHM             | -                          |

---

## Master Data P2P

Sebelum membuat transaksi P2P, pastikan master data sudah disiapkan dengan benar.

### 1. P2P Config

**Menu:** Showroom/Workshop → Configuration → P2P → P2P Config

Master Config digunakan untuk mengatur konfigurasi pemasok (Principle/ATPM).

| Kolom           | Keterangan                 | Wajib Diisi? | Contoh |
| --------------- | -------------------------- | ------------ | ------ |
| **Supplier**    | Pemasok principle (ATPM)   | ✅ Ya        | PT AHM |
| **Tentative 1** | Persentase tentative 1 (%) | Tidak        | 20     |
| **Tentative 2** | Persentase tentative 2 (%) | Tidak        | 30     |
| **Active**      | Status aktif               | ✅ Ya        | ☑️     |

> [!NOTE]
> **Satu pemasok hanya dapat memiliki satu konfigurasi.** Sistem akan mencegah duplikasi data pemasok.

---

### 2. P2P Periode

**Menu:** Showroom/Workshop → Configuration → P2P → P2P Periode

Master Periode mengatur rentang waktu kapan P2P Purchase Order dapat dibuat.

| Kolom                    | Keterangan                                  | Wajib Diisi? | Contoh     |
| ------------------------ | ------------------------------------------- | ------------ | ---------- |
| **Name**                 | Nama periode (format YYYYMM, maks. 6 digit) | ✅ Ya        | 202601     |
| **Effective Start Date** | Tanggal mulai efektif (input)               | ✅ Ya        | 01/01/2026 |
| **Effective End Date**   | Tanggal akhir efektif (input)               | ✅ Ya        | 15/01/2026 |
| **Periode Start Date**   | Tanggal mulai periode pengiriman            | Tidak        | 01/02/2026 |
| **Periode End Date**     | Tanggal akhir periode pengiriman            | Tidak        | 28/02/2026 |
| **Active**               | Status aktif                                | ✅ Ya        | ☑️         |

> [!IMPORTANT]
> **Tentang Effective Date:**
>
> - **Effective Start Date** dan **Effective End Date** menentukan kapan pengguna boleh membuat P2P Order
> - Tanggal pembuatan P2P harus berada dalam rentang Effective Date
> - Sistem mencegah tumpang tindih tanggal antarperiode

> [!CAUTION]
> **Periode tidak boleh tumpang tindih!**
> Jika membuat periode baru dengan tanggal yang bersinggungan dengan periode yang sudah ada, sistem akan menolak dengan pesan kesalahan.

---

### 3. P2P Product

**Menu:** Showroom/Workshop → Configuration → P2P → P2P Product

Master Product mengatur produk apa saja yang dapat dipesan dalam P2P.

| Kolom                  | Keterangan                             | Wajib Diisi? | Contoh           |
| ---------------------- | -------------------------------------- | ------------ | ---------------- |
| **Product**            | Produk yang akan dipesan               | ✅ Ya        | Beat Street CBS  |
| **Start Date**         | Tanggal mulai produk aktif             | ✅ Ya        | 01/01/2026       |
| **End Date**           | Tanggal akhir produk aktif             | ✅ Ya        | 31/12/2026       |
| **Companies**          | Perusahaan/Cabang yang dapat memesan   | Tidak        | Tunas Group      |
| **Category Fix Order** | Kategori untuk Fix Order (Sparepart)   | Kondisional  | Oli, Ban, dll.   |
| **Division**           | Divisi (otomatis dari kategori produk) | Otomatis     | Unit / Sparepart |

> [!NOTE]
> **Category Fix Order wajib diisi untuk divisi Sparepart!**
> Untuk divisi Unit, kolom ini tidak perlu diisi.

---

### 4. Category Fix Order

**Menu:** Showroom/Workshop → Configuration → P2P → Category Fix Order

Master kategori untuk mengelompokkan produk sparepart berdasarkan tipe Fix Order.

| Kolom      | Keterangan    | Wajib Diisi? | Contoh |
| ---------- | ------------- | ------------ | ------ |
| **Name**   | Nama kategori | ✅ Ya        | OLI    |
| **Active** | Status aktif  | ✅ Ya        | ☑️     |

---

## Membuat Transaksi P2P Purchase Order

### Cara Mengakses Menu

**Untuk Unit:**

```
Menu: Showroom → Purchase → P2P Unit
```

**Untuk Sparepart:**

```
Menu: Workshop → Purchase → P2P Sparepart
```

### Langkah-langkah Membuat P2P Purchase Order

#### Langkah 1: Buat Pesanan Baru

1. Klik tombol **"New"** untuk membuat pesanan baru
2. Pilih **Dealer** (Cabang yang melakukan pemesanan)
3. **Supplier** akan terisi otomatis berdasarkan Default Supplier di Branch
4. Pilih **Periode** yang sesuai
5. Pilih **Type** (Fix atau Additional)
6. **Untuk Sparepart dengan Type Fix:** Pilih Category Fix Order

#### Langkah 2: Isi Detail Pesanan

**Untuk Type Fix:**

1. Klik **"Generate"** untuk membuat baris produk dari master P2P Product
2. Sistem akan mengambil data dari periode sebelumnya jika ada
3. Edit **Fix Qty**, **Tent 1 Qty**, **Tent 2 Qty** sesuai kebutuhan

**Untuk Type Additional:**

1. Tambahkan produk secara manual di tab Order Line
2. Pilih produk dari daftar yang tersedia
3. Isi **Fix Qty** untuk setiap produk

### Penjelasan Kolom di P2P Purchase Order

#### Bagian Header

| Kolom                  | Keterangan                          | Wajib Diisi? | Contoh             |
| ---------------------- | ----------------------------------- | ------------ | ------------------ |
| **Dealer**             | Cabang yang membuat pesanan         | ✅ Ya        | Honda Pondok Indah |
| **Supplier**           | Pemasok ATPM (otomatis dari Branch) | ✅ Ya        | PT AHM             |
| **Periode**            | Periode pemesanan                   | ✅ Ya        | 202601             |
| **Division**           | Divisi (Unit/Sparepart)             | ✅ Ya        | Unit               |
| **Type**               | Tipe pesanan (Fix/Additional)       | ✅ Ya        | Fix                |
| **Category Fix Order** | Kategori untuk Fix Order Sparepart  | Kondisional  | OLI                |
| **Description**        | Deskripsi tambahan                  | Tidak        | Pesanan Januari    |
| **Revisi Ke**          | Nomor revisi (jika ada)             | Otomatis     | 0                  |

#### Bagian Order Line (Type Fix)

| Kolom               | Keterangan                         | Wajib Diisi? |
| ------------------- | ---------------------------------- | ------------ |
| **Product**         | Produk yang dipesan                | ✅ Ya        |
| **Tent 1 Prev Qty** | Kuantitas Tentative 1 periode lalu | Otomatis     |
| **Fix Qty**         | Kuantitas fix yang dipesan         | ✅ Ya        |
| **Tent 1 Qty**      | Kuantitas tentative 1              | ✅ Ya        |
| **Tent 2 Qty**      | Kuantitas tentative 2              | ✅ Ya        |
| **Qty Available**   | Stok yang tersedia di pemasok      | Otomatis     |

> [!TIP]
> **Tentang Data Periode Sebelumnya:**
> Jika ada P2P Order pada periode sebelumnya, sistem akan mengambil data Tent 1 dan Tent 2 dari periode tersebut sebagai referensi.

#### Bagian Order Line (Type Additional)

| Kolom             | Keterangan                    | Wajib Diisi? |
| ----------------- | ----------------------------- | ------------ |
| **Product**       | Produk yang dipesan           | ✅ Ya        |
| **Fix Qty**       | Kuantitas yang dipesan        | ✅ Ya        |
| **Qty Available** | Stok yang tersedia di pemasok | Otomatis     |

---

## Proses Approval P2P

Modul P2P Approval menambahkan alur persetujuan bertingkat sebelum P2P Order dapat diverifikasi dan dikonfirmasi.

### Alur Approval

```
┌───────────────────┐     ┌────────────────────────┐     ┌───────────────────────┐
│ DRAFT             │────▶│ WAITING FOR APPROVAL   │────▶│ APPROVED              │
│ (Staf membuat)    │ RFA │ (Menunggu persetujuan) │     │ (Lanjut verifikasi)   │
└───────────────────┘     └──────────┬─────────────┘     └───────────────────────┘
                                     │
                                     ▼ Jika ditolak
                          ┌──────────────────────┐
                          │ REJECTED / DRAFT     │
                          │ (Perlu perbaikan)    │
                          └──────────────────────┘
```

### Panduan untuk Staf (Pembuat Pesanan)

#### Langkah 1: Lengkapi P2P Order

1. Pastikan semua data terisi dengan benar
2. Fix Qty harus lebih besar dari 0
3. Tidak boleh ada produk duplikat (untuk Type Additional)

#### Langkah 2: Kirim RFA (Request for Approval)

1. Klik tombol **"RFA"** (Request for Approval)
2. Sistem akan melakukan validasi data
3. Jika validasi berhasil, status berubah menjadi _Waiting for Approval_

> [!IMPORTANT]
> **Sebelum RFA pastikan:**
>
> - Total Fix Qty harus lebih besar dari 0
> - Untuk Type Additional, tidak boleh ada produk duplikat
> - Semua produk harus masih aktif

### Panduan untuk Approver

#### Menyetujui P2P Order

1. Buka P2P Order yang berstatus _Waiting for Approval_
2. Tinjau data pesanan (produk, kuantitas, dll.)
3. Jika setuju, klik tombol **"Approve"**
4. Status berubah menjadi _Waiting for Verification_

#### Menolak P2P Order

1. Buka P2P Order yang berstatus _Waiting for Approval_
2. Jika tidak setuju, klik tombol **"Reject"**
3. Isi alasan penolakan
4. Status kembali ke Draft atau status Reject

#### Membatalkan Approval

1. Buka P2P Order yang berstatus _Approved_
2. Klik tombol **"Cancel Approval"**
3. Isi alasan pembatalan
4. Status kembali ke Draft

### Tombol-tombol pada Header Form

| Tombol              | Fungsi                      | Kapan Muncul?            | Pengguna      |
| ------------------- | --------------------------- | ------------------------ | ------------- |
| **Generate**        | Buat baris dari P2P Product | Draft, Type Fix          | Staf          |
| **RFA**             | Request for Approval        | Draft, Revisi            | Staf          |
| **Approve**         | Menyetujui pesanan          | Waiting for Approval     | Approver      |
| **Reject**          | Menolak pesanan             | Waiting for Approval     | Approver      |
| **Cancel Approval** | Membatalkan persetujuan     | Approved                 | Approver      |
| **Confirm**         | Konfirmasi akhir            | Waiting for Verification | Staf/Approver |
| **Revisi**          | Kembalikan untuk perbaikan  | Waiting for Verification | Staf/Approver |
| **Cancel**          | Batalkan pesanan            | Draft                    | Staf          |
| **Export / Import** | Ekspor/Impor data via Excel | Draft, Revisi            | Staf          |

### Tab Approval

Tab **"Approval"** pada formulir P2P Order menampilkan riwayat persetujuan:

| Kolom        | Keterangan                           |
| ------------ | ------------------------------------ |
| **Approver** | Pengguna yang melakukan persetujuan  |
| **Date**     | Tanggal persetujuan                  |
| **Action**   | Aksi yang dilakukan (Approve/Reject) |
| **Note**     | Catatan/alasan                       |

---

## Integrasi MFT UPO (File Transfer ke AHM)

Modul MFT UPO secara otomatis membuat file UPO (Unit Purchase Order) atau PPO (Part Purchase Order) saat P2P Order diverifikasi. File ini digunakan untuk komunikasi B2B dengan AHM.

### Proses Pembuatan File

```
┌───────────────────────┐     ┌─────────────────────┐     ┌───────────────────┐
│ P2P ORDER             │────▶│ VERIFICATION        │────▶│ FILE UPO/PPO      │
│ (Sudah di-approve)    │     │ (Klik Verification) │     │ DIBUAT OTOMATIS   │
└───────────────────────┘     └─────────────────────┘     └─────────┬─────────┘
                                                                    │
                                                                    ▼
                                                          ┌───────────────────┐
                                                          │ DISIMPAN KE       │
                                                          │ FOLDER MFT-OUT    │
                                                          └───────────────────┘
```

### Format Nama File

#### Untuk Unit (UPO)

| Kondisi       | Format Nama File                     | Contoh                      |
| ------------- | ------------------------------------ | --------------------------- |
| Pesanan biasa | `{MD_CODE}-{PO_NUMBER}.UPO`          | `THK-P2PHK00001.UPO`        |
| Revisi ke-N   | `AHM-{MD_CODE}-{PO_NUMBER}_{N}_.UPO` | `AHM-THK-P2PHK00001_1_.UPO` |

#### Untuk Sparepart (PPO)

| Kondisi     | Format Nama File                         | Contoh                       |
| ----------- | ---------------------------------------- | ---------------------------- |
| Fix Order   | `AHM-{MD_CODE}-{DDMMYYYY}{CATEGORY}.PPO` | `AHM-THK-27012026OLI.PPO`    |
| Additional  | `AHM-{MD_CODE}-{DDMMYYYY}ADD.PPO`        | `AHM-THK-27012026ADD.PPO`    |
| Revisi ke-N | `AHM-{MD_CODE}-{DDMMYYYY}{CAT}_{N}_.PPO` | `AHM-THK-27012026OLI_1_.PPO` |

### Isi File UPO (Unit)

```
{MD_CODE};{BULAN};{TAHUN};{PRODUCT_NAME};{COLOR};{FIX_QTY};{TENT1_QTY};{TENT2_QTY};{PO_NUMBER};{TYPE};{EFF_START};{EFF_END};
```

**Contoh:**

```
THK;01;2026;BEAT STREET CBS;Vigor Black;10;15;20;P2P/HK/00001;F;01012026;31012026;
```

### Isi File PPO (Sparepart)

```
{MD_CODE};{BULAN};{TAHUN};{PRODUCT_NAME};{FIX_QTY};{PO_NUMBER};{TYPE};{CATEGORY};{EFF_START};{EFF_END};
```

**Contoh:**

```
THK;01;2026;OLI FEDERAL 0.8L;50;P2P/HK/00001;F;OLI;01012026;31012026;
```

### Tab History File UPO

Tab **"History File UPO"** pada formulir P2P Order menampilkan riwayat file yang telah dibuat:

| Kolom        | Keterangan                  |
| ------------ | --------------------------- |
| **Filename** | Nama file yang dibuat       |
| **Date**     | Tanggal pembuatan file      |
| **State**    | Status file (Open/Done/Rev) |
| **Content**  | Isi file (dapat dilihat)    |

### Status File UPO

| Status       | Keterangan                             | Kondisi                  |
| ------------ | -------------------------------------- | ------------------------ |
| **Open**     | File baru dibuat, menunggu konfirmasi  | Setelah Verification     |
| **Done**     | File selesai, P2P Order dikonfirmasi   | Setelah Confirm          |
| **Revision** | File direvisi, ada file baru pengganti | Setelah Revisi P2P Order |
| **Closed**   | File ditutup (tidak digunakan)         | Manual oleh admin        |

### Tab MFT Error Log

Tab **"MFT Error Log"** menampilkan kesalahan yang terjadi saat proses transfer file ke AHM:

| Kolom        | Keterangan              |
| ------------ | ----------------------- |
| **Name**     | Nama kesalahan/pesan    |
| **State**    | Status (Open/Done)      |
| **Datetime** | Waktu kesalahan terjadi |

> [!NOTE]
> Error log dengan status **Open** adalah kesalahan yang belum ditangani. Setelah P2P Order diverifikasi ulang, status error akan berubah menjadi **Done**.

---

## Ekspor dan Impor Data

### Ekspor Data

1. Buka P2P Purchase Order yang ingin diekspor
2. Klik tombol **"Export / Import"**
3. Pilih **"Download"** untuk mengunduh file Excel
4. File akan berisi daftar produk dengan kuantitas yang dapat diedit

### Impor Data

1. Buka P2P Purchase Order yang akan diimpor
2. Klik tombol **"Export / Import"**
3. Unggah file Excel yang sudah diedit
4. Klik **"Import"**
5. Sistem akan memperbarui kuantitas sesuai data di Excel

> [!WARNING]
> **Format Excel harus sesuai!**
> Pastikan format file Excel sama dengan templat ekspor. Jangan mengubah struktur kolom atau menambah/menghapus baris produk.

---

## Pertanyaan yang Sering Diajukan (FAQ)

### Umum

**T: Saya tidak dapat melihat menu P2P, mengapa?**

> Anda mungkin tidak memiliki akses. Hubungi Administrator untuk diberikan akses ke grup P2P yang sesuai.

**T: Tombol RFA tidak muncul?**

> Pastikan:
>
> 1. Status dokumen masih "Draft" atau "Revisi"
> 2. Semua kolom wajib sudah diisi
> 3. Anda memiliki hak akses yang sesuai

---

### Periode

**T: Muncul kesalahan "Periode P2P tidak ditemukan"?**

> Tidak ada periode aktif untuk tanggal saat ini. Hubungi Admin Master Data untuk mengaktifkan atau membuat periode baru.

**T: Muncul kesalahan "Tanggal tidak termasuk dalam periode"?**

> Tanggal pembuatan P2P Order tidak berada dalam rentang Effective Date periode. Pastikan membuat pesanan dalam periode yang masih berlaku.

**T: Muncul kesalahan "Periode tanggal bersinggungan"?**

> Anda mencoba membuat periode baru dengan tanggal yang tumpang tindih dengan periode yang sudah ada. Pilih tanggal yang tidak bersinggungan.

---

### Produk

**T: Produk yang saya cari tidak muncul di daftar?**

> Periksa:
>
> 1. Produk sudah terdaftar di P2P Product
> 2. Tanggal saat ini berada dalam rentang Start Date - End Date produk
> 3. Perusahaan/Cabang Anda tercakup dalam kolom Companies di master P2P Product
> 4. Divisi produk sesuai (Unit/Sparepart)

**T: Muncul kesalahan "Category Fix Order wajib diisi"?**

> Untuk divisi Sparepart dengan Type Fix, Anda harus memilih Category Fix Order.

---

### Approval

**T: Muncul kesalahan saat RFA, mengapa?**

> Beberapa kemungkinan:
>
> 1. Total Fix Qty = 0 (harus lebih besar dari 0)
> 2. Produk sudah tidak aktif
> 3. Pemasok tidak ada di P2P Config
> 4. Periode tidak sesuai

**T: Pesanan saya sudah di-approve tetapi masih Waiting for Verification?**

> Status _Waiting for Verification_ adalah tahap setelah approval. Selanjutnya perlu diklik **"Confirm"** untuk menyelesaikan proses.

**T: Pesanan saya di-reject, apa yang harus dilakukan?**

> 1. Baca alasan penolakan di tab Approval
> 2. Perbaiki data sesuai umpan balik
> 3. Kirim RFA ulang

---

### File UPO/MFT

**T: Kapan file UPO/PPO dibuat?**

> File dibuat secara otomatis saat P2P Order di-**Verification** (setelah approval).

**T: Di mana file UPO/PPO disimpan?**

> File disimpan di folder yang dikonfigurasi sebagai "MFT-OUT" di menu Configuration → Config Files. Biasanya terkoneksi dengan sistem MFT untuk transfer ke AHM.

**T: Muncul kesalahan "Belum ada konfigurasi folder penyimpanan file UPO (MFT-OUT)!"?**

> Hubungi Admin IT untuk membuat konfigurasi MFT-OUT. Konfigurasi ini menentukan di mana file UPO/PPO akan disimpan.

**T: File terbuat tetapi tidak terkirim ke AHM?**

> File hanya dibuat oleh sistem Odoo. Pengiriman ke AHM dilakukan oleh sistem MFT terpisah. Hubungi Tim B2B/MFT untuk status pengiriman.

---

### Transaksi

**T: Saya sudah confirm tetapi PO tidak terbentuk?**

> Periksa apakah:
>
> 1. Cabang memiliki konfigurasi Default Supplier
> 2. Pemasok terdaftar di P2P Config
> 3. Tidak ada kesalahan lain saat proses confirm

**T: Bagaimana cara membatalkan P2P yang sudah Confirmed?**

> P2P yang sudah Confirmed tidak dapat dibatalkan secara langsung. Hubungi Administrator untuk penanganan lebih lanjut.

**T: Data P2P tidak dapat diduplikasi?**

> Ya, P2P Purchase Order tidak mendukung fitur duplikasi untuk menjaga integritas data periode.

---

## Tips dan Praktik Terbaik

### Yang Harus Dilakukan ✅

1. **Pastikan periode sudah dibuat** sebelum membuat P2P Order
2. **Periksa master P2P Product** sudah terisi dengan produk yang dibutuhkan
3. **Gunakan fitur Generate** untuk Type Fix agar data konsisten
4. **Tinjau kuantitas** sebelum RFA
5. **Periksa History File UPO** setelah verifikasi untuk memastikan file terbuat
6. **Berikan catatan yang jelas** saat menolak agar pembuat pesanan paham
7. **Segera proses approval** yang tertunda untuk kelancaran operasional
8. **Pantau Error Log** secara berkala
9. **Koordinasi dengan Tim MFT** untuk memastikan file terkirim ke AHM

### Yang Tidak Boleh Dilakukan ❌

1. **Jangan** membuat P2P Order di luar periode yang berlaku
2. **Jangan** mengubah struktur file Excel saat impor
3. **Jangan** memasukkan produk duplikat dalam satu pesanan
4. **Jangan** mengabaikan pesan kesalahan dari sistem
5. **Jangan** confirm jika total Fix Qty = 0
6. **Jangan** approve tanpa meninjau data
7. **Jangan** reject tanpa memberikan alasan
8. **Jangan** hapus file di folder MFT-OUT secara manual
9. **Jangan** edit file UPO/PPO secara manual
10. **Jangan** revisi P2P berulang kali tanpa keperluan (akan membuat banyak file)

---

## Kontak Dukungan

Jika Anda mengalami kendala yang tidak tercakup dalam panduan ini, silakan hubungi:

| Tim             | Untuk Masalah                       | Kontak                 |
| --------------- | ----------------------------------- | ---------------------- |
| **IT Support**  | Kesalahan sistem, tidak dapat akses | helpdesk@company.com   |
| **Master Data** | Produk/Periode tidak ada            | masterdata@company.com |
| **Tim B2B/MFT** | Status pengiriman file ke AHM       | mft@company.com        |
| **Admin**       | Pertanyaan proses bisnis            | admin@company.com      |

---

_Dokumen ini terakhir diperbarui: Januari 2026_  
_Versi: 1.0_
