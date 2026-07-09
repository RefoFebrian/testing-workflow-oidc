# 📖 PANDUAN PENGGUNA SISTEM ASSET MANAGEMENT

## Daftar Isi

1. [Pendahuluan](#pendahuluan)
2. [Alur Proses Asset Management](#alur-proses-asset-management)
3. [Langkah 1: PO Asset (Purchase Order Asset)](#langkah-1-po-asset-purchase-order-asset)
4. [Langkah 2: GR Asset (Good Receive Asset)](#langkah-2-gr-asset-good-receive-asset)
5. [Langkah 3: Akuisisi Asset](#langkah-3-akuisisi-asset)
6. [Langkah 4: GR Collecting Asset](#langkah-4-gr-collecting-asset)
7. [Penanganan CIP (Construction in Progress)](#penanganan-cip-construction-in-progress)
8. [FAQ - Pertanyaan yang Sering Diajukan](#faq---pertanyaan-yang-sering-diajukan)

---

## Pendahuluan

### Apa itu Sistem Asset Management?

Sistem Asset Management adalah modul untuk **mengelola seluruh siklus hidup aset perusahaan** mulai dari pembelian, penerimaan barang, pencatatan sebagai aset, hingga pembayaran ke vendor.

### Mengapa Perlu Sistem Ini?

| Tanpa Sistem                   | Dengan Sistem                           |
| ------------------------------ | --------------------------------------- |
| Pencatatan manual, rawan salah | Pencatatan otomatis dan terintegrasi    |
| Sulit melacak aset             | Semua aset tercatat dengan lengkap      |
| Tidak ada kontrol persetujuan  | Ada approval bertingkat                 |
| Depresiasi dihitung manual     | Depresiasi otomatis sesuai kebijakan    |
| Pembayaran sulit di-track      | Pembayaran terkoneksi dengan penerimaan |

### Siapa yang Menggunakan Sistem Ini?

- **Staff Purchasing** — Membuat Purchase Order Asset
- **Staff Gudang/GA** — Menerima barang (Good Receive)
- **Staff Accounting** — Membuat Akuisisi Asset & GR Collecting
- **Supervisor/Manager** — Memberikan persetujuan

---

## Alur Proses Asset Management

Berikut adalah alur lengkap proses asset management dari awal hingga selesai:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ALUR PROSES ASSET MANAGEMENT                      │
└─────────────────────────────────────────────────────────────────────┘

     ┌───────────────┐
     │  1. PO ASSET  │ ← Staff Purchasing membuat pesanan pembelian
     │ (Pemesanan)   │
     └───────┬───────┘
             │
             │ Setelah disetujui & barang dikirim vendor
             ▼
     ┌───────────────┐
     │ 2. GR ASSET   │ ← Staff Gudang/GA menerima barang
     │ (Penerimaan)  │
     └───────┬───────┘
             │
             │ Barang sudah diterima, siap dicatat sebagai aset
             ▼
     ┌───────────────┐
     │ 3. AKUISISI   │ ← Staff Accounting mencatat sebagai aset
     │ (Pencatatan)  │
     └───────┬───────┘
             │
             │ Aset tercatat, siap untuk pembayaran
             ▼
     ┌─────────────────┐
     │ 4. GR COLLECTING│ ← Staff Accounting membuat invoice & payment
     │ (Pembayaran)    │
     └───────┬─────────┘
             │
             ▼
        ✅ SELESAI
```

### Mengapa Harus Berurutan?

> [!IMPORTANT]
> Setiap langkah **HARUS** dilakukan secara berurutan. Anda tidak bisa:
>
> - Membuat GR sebelum ada PO yang disetujui
> - Membuat Akuisisi sebelum GR dikonfirmasi
> - Membuat GR Collecting sebelum ada GR yang sudah open

Hal ini untuk memastikan **pencatatan yang akurat** dan **audit trail** yang jelas.

---

## Langkah 1: PO Asset (Purchase Order Asset)

### Apa itu PO Asset?

PO Asset adalah **dokumen pemesanan pembelian aset** kepada vendor. Dokumen ini berisi informasi apa yang akan dibeli, dari siapa, berapa harganya, dan kapan akan dikirim.

### Cara Mengakses Menu

```
Menu: Asset Management → PO Asset → Purchase Order Asset
```

### Cara Membuat PO Asset Baru

1. **Klik tombol "New"** untuk membuat PO baru
2. **Isi data header** seperti dijelaskan di bawah
3. **Tambahkan item** yang akan dibeli di tab "Order Lines"
4. **Klik "Request Approval"** untuk mengajukan persetujuan

### Penjelasan Field-field di PO Asset

#### Bagian Header (Informasi Utama)

| Field            | Keterangan                              | Wajib Diisi? | Contoh                 |
| ---------------- | --------------------------------------- | ------------ | ---------------------- |
| **Vendor**       | Perusahaan/toko tempat membeli aset     | ✅ Ya        | PT Astra International |
| **Branch**       | Cabang yang melakukan pembelian         | ✅ Ya        | Honda Pondok Indah     |
| **Division**     | Divisi terkait (otomatis terisi "Umum") | ✅ Ya        | Umum                   |
| **Date Order**   | Tanggal pembuatan PO                    | ✅ Ya        | 12/01/2026             |
| **Date Planned** | Tanggal rencana barang diterima         | Tidak        | 20/01/2026             |
| **PO Type**      | Tipe pembelian aset                     | Tidak        | Pembelian Baru         |

> [!NOTE] > **Mengapa Date Order tidak boleh di masa lalu?**  
> Sistem mencegah tanggal mundur untuk menjaga integritas data dan audit trail. Jika Anda perlu membuat PO untuk pembelian yang sudah terjadi, hubungi Administrator.

#### Bagian Order Lines (Daftar Barang)

Klik **"Add a line"** untuk menambahkan item yang akan dibeli:

| Field           | Keterangan                    | Wajib Diisi? | Contoh                    |
| --------------- | ----------------------------- | ------------ | ------------------------- |
| **Product**     | Nama barang/aset yang dibeli  | ✅ Ya        | Laptop Dell Latitude 5520 |
| **Description** | Deskripsi tambahan jika perlu | Tidak        | RAM 16GB, SSD 512GB       |
| **Quantity**    | Jumlah yang dibeli            | ✅ Ya        | 5                         |
| **Unit Price**  | Harga per unit                | ✅ Ya        | 15,000,000                |
| **Taxes**       | Pajak yang berlaku (PPN)      | Tidak        | PPN 11%                   |

> [!TIP] > **Tips:** Pastikan product yang dipilih sudah memiliki **Asset Category** di master Product. Jika belum, sistem akan menampilkan peringatan saat GR.

### Status PO Asset

| Status                   | Arti                           | Apa yang Harus Dilakukan?                   |
| ------------------------ | ------------------------------ | ------------------------------------------- |
| **Draft**                | PO baru dibuat, belum diajukan | Lengkapi data, lalu klik "Request Approval" |
| **Waiting for Approval** | Menunggu persetujuan atasan    | Tunggu supervisor/manager approve           |
| **Approved**             | Sudah disetujui                | Klik "Confirm" untuk membuka PO             |
| **Open**                 | PO aktif, siap untuk GR        | Buat GR Asset saat barang diterima          |
| **Partial Received**     | Sebagian barang sudah diterima | Lanjutkan GR untuk sisa barang              |
| **Received**             | Semua barang sudah diterima    | Tunggu proses collecting                    |
| **Partial Payment**      | Sebagian sudah dibayar         | Lanjutkan GR Collecting                     |
| **Payment**              | Sudah lunas                    | Proses selesai ✅                           |

### Tombol-tombol Aksi

| Tombol                | Fungsi                          | Kapan Muncul?          |
| --------------------- | ------------------------------- | ---------------------- |
| **Request Approval**  | Mengajukan PO untuk persetujuan | Saat status Draft      |
| **Approve**           | Menyetujui PO (untuk approver)  | Saat status Waiting    |
| **Confirm**           | Mengkonfirmasi PO menjadi Open  | Saat status Approved   |
| **View Good Receive** | Melihat daftar GR terkait       | Setelah ada GR         |
| **View Collecting**   | Melihat daftar GR Collecting    | Setelah ada Collecting |

---

## Langkah 2: GR Asset (Good Receive Asset)

### Apa itu GR Asset?

GR Asset adalah **dokumen penerimaan barang** yang dibuat saat aset yang dipesan sudah tiba dan diterima di lokasi. Dokumen ini menjadi bukti bahwa barang sudah fisik diterima.

### Cara Mengakses Menu

```
Menu: Asset Management → GR Asset → Good Receive Asset
```

### Kapan Membuat GR Asset?

Buat GR Asset **HANYA** ketika:

- Barang sudah tiba secara fisik
- Kondisi barang sudah dicek dan sesuai pesanan
- PO sudah berstatus "Open"

> [!CAUTION] > **Jangan membuat GR jika barang belum diterima!**  
> GR adalah bukti bahwa barang sudah di tangan Anda. Membuat GR palsu bisa menyebabkan masalah akuntansi dan audit.

### Cara Membuat GR Asset Baru

1. **Klik tombol "New"**
2. **Pilih Branch** terlebih dahulu
3. **Pilih Vendor** yang mengirim barang
4. **Centang "Is Asset"** untuk menandakan ini GR untuk aset
5. **Tambahkan item** di tab "Asset Items"
6. **Isi tanggal dokumen** dan informasi lainnya
7. **Klik "Request Approval"** atau langsung "Confirm"

### Penjelasan Field-field di GR Asset

#### Bagian Header

| Field                     | Keterangan                     | Wajib Diisi? | Contoh                 |
| ------------------------- | ------------------------------ | ------------ | ---------------------- |
| **Branch**                | Cabang yang menerima barang    | ✅ Ya        | Honda Pondok Indah     |
| **Vendor**                | Vendor pengirim barang         | ✅ Ya        | PT Astra International |
| **Is Asset**              | Centang jika ini GR untuk aset | ✅ Ya        | ☑️ (dicentang)         |
| **Date**                  | Tanggal penerimaan barang      | ✅ Ya        | 20/01/2026             |
| **Document Date**         | Tanggal di surat jalan vendor  | Tidak        | 19/01/2026             |
| **Vendor Picking Number** | Nomor surat jalan vendor       | Tidak        | SJ-2026-001            |

> [!NOTE] > **Mengapa perlu "Vendor Picking Number"?**  
> Untuk memudahkan cross-check jika ada dispute dengan vendor. Nomor ini akan menjadi referensi jika ada masalah di kemudian hari.

#### Bagian Asset Items (Daftar Barang yang Diterima)

| Field              | Keterangan                   | Wajib Diisi? | Contoh                    |
| ------------------ | ---------------------------- | ------------ | ------------------------- |
| **Purchase Order** | Pilih PO yang terkait        | ✅ Ya        | POA/HKA/00001             |
| **PO Line**        | Pilih baris PO (item apa)    | ✅ Ya        | Laptop Dell Latitude      |
| **Product**        | Otomatis terisi dari PO Line | Otomatis     | Laptop Dell Latitude 5520 |
| **Description**    | Deskripsi item               | Tidak        | SN: ABC123                |
| **Qty**            | Jumlah yang diterima         | ✅ Ya        | 5                         |
| **Price**          | Harga per unit               | ✅ Ya        | 15,000,000                |
| **Asset Category** | Kategori aset (dari Product) | ✅ Ya        | Computer Equipment        |
| **Taxes**          | Pajak yang berlaku           | Tidak        | PPN 11%                   |
| **No DO**          | Nomor Delivery Order         | Tidak        | DO-001                    |
| **DO Date**        | Tanggal Delivery Order       | Tidak        | 20/01/2026                |

> [!IMPORTANT] > **Tentang Quantity:**
>
> - **Qty** harus sama atau kurang dari **Qty Available** di PO
> - Jika barang diterima bertahap, buat beberapa GR dengan qty sesuai penerimaan
> - Contoh: PO 10 unit, terima 3 dulu → Buat GR qty 3, sisanya nanti

#### Field untuk CIP (Construction in Progress)

| Field            | Keterangan                                            | Wajib Diisi? |
| ---------------- | ----------------------------------------------------- | ------------ |
| **Is CIP**       | Otomatis dari Asset Category                          | Otomatis     |
| **Is Final CIP** | Centang jika ini penerimaan terakhir untuk proyek CIP | Tidak        |
| **Asset (CIP)**  | Pilih aset CIP existing jika kapitalisasi             | Tidak        |

> [!NOTE] > **Apa itu CIP?**  
> CIP adalah aset yang masih dalam proses pembangunan/perakitan. Contoh: membangun gedung baru. Selama pembangunan, semua biaya dikumpulkan dulu, baru setelah selesai dicatat sebagai aset utuh.

### Status GR Asset

| Status                   | Arti                                | Apa yang Harus Dilakukan?   |
| ------------------------ | ----------------------------------- | --------------------------- |
| **Draft**                | GR baru dibuat                      | Lengkapi data, lalu confirm |
| **Waiting for Approval** | Menunggu persetujuan                | Tunggu approver             |
| **Approved**             | Sudah disetujui                     | Klik "Confirm"              |
| **Open**                 | GR dikonfirmasi, journal JGR dibuat | Buat Akuisisi Asset         |
| **Partial Invoiced**     | Sebagian sudah di-collecting        | Lanjutkan GR Collecting     |
| **Invoiced**             | Semua sudah di-collecting           | Proses selesai              |
| **Done**                 | Selesai                             | -                           |

### Apa yang Terjadi Saat GR Dikonfirmasi?

1. **Stock Move** dibuat untuk setiap item (pencatatan inventory)
2. **Journal JGR** (Jurnal Good Receive) dibuat otomatis
3. **Qty Received di PO** diupdate
4. Status PO berubah sesuai total penerimaan

> [!WARNING] > **Perhatian!**  
> Saat GR dikonfirmasi, **ASET BELUM TERCATAT**. Aset baru tercatat setelah proses **Akuisisi Asset** di langkah berikutnya.

---

## Langkah 3: Akuisisi Asset

### Apa itu Akuisisi Asset?

Akuisisi Asset adalah proses **mencatat barang yang sudah diterima menjadi aset resmi perusahaan**. Di sinilah aset benar-benar "lahir" dalam sistem dengan kode, kategori, dan jadwal depresiasi.

### Mengapa Perlu Langkah Terpisah?

> [!IMPORTANT] > **Mengapa tidak langsung tercatat saat GR?**
>
> 1. **Fleksibilitas jumlah aset** — Dari 1 GR line bisa dibuat beberapa unit aset dengan serial number berbeda
> 2. **Penentuan pengguna** — Setiap unit aset bisa ditentukan siapa penggunanya
> 3. **CIP/Kapitalisasi** — Bisa menggabungkan beberapa penerimaan menjadi 1 aset (untuk proyek CIP)
> 4. **Kontrol accounting** — Tim accounting bisa review sebelum aset tercatat

### Cara Mengakses Menu

```
Menu: Asset Management → Akuisisi Asset → Asset Acquisition
```

### Cara Membuat Akuisisi Asset

1. **Klik tombol "New"**
2. **Pilih Branch** yang sesuai
3. **Pilih Good Receive** yang sudah Open
4. **Pilih GR Line** yang akan diakuisisi
5. **Isi Asset Category** (biasanya otomatis dari product)
6. **Tentukan Quantity** unit aset yang dibuat
7. **Isi Tab Pengguna Asset** — Siapa yang akan menggunakan tiap unit
8. **Klik "Confirm"** untuk membuat aset

### Penjelasan Field-field di Akuisisi Asset

#### Bagian Header

| Field               | Keterangan                   | Wajib Diisi? | Contoh                    |
| ------------------- | ---------------------------- | ------------ | ------------------------- |
| **Branch**          | Cabang pemilik aset          | ✅ Ya        | Honda Pondok Indah        |
| **Date**            | Tanggal akuisisi             | ✅ Ya        | 22/01/2026                |
| **Good Receive**    | Pilih GR yang sudah Open     | ✅ Ya        | GR/HKA/00001              |
| **GR Line (Asset)** | Pilih line dari GR tersebut  | ✅ Ya        | Laptop Dell Latitude 5520 |
| **Quantity**        | Berapa unit aset yang dibuat | ✅ Ya        | 5                         |
| **Asset Category**  | Kategori aset                | ✅ Ya        | Computer Equipment        |
| **PIC Asset**       | Penanggung jawab aset        | Tidak        | Budi Santoso              |

> [!NOTE] > **Field "Quantity" sangat penting!**  
> Angka ini menentukan berapa record aset yang akan dibuat. Jika Anda menerima 5 laptop, dan ingin setiap laptop tercatat terpisah dengan serial number masing-masing, isi Quantity = 5.

#### Bagian Amounts (Nilai-nilai)

| Field                     | Keterangan                        | Otomatis?   |
| ------------------------- | --------------------------------- | ----------- |
| **Base Amount**           | Nilai dari GR Line utama × Qty    | ✅ Otomatis |
| **Capitalization Amount** | Total nilai kapitalisasi tambahan | ✅ Otomatis |
| **Total Amount**          | Base + Kapitalisasi               | ✅ Otomatis |
| **Amount per Unit**       | Total ÷ Quantity                  | ✅ Otomatis |

**Contoh Perhitungan:**

```
GR Line: Laptop @ Rp 15.000.000
Quantity Akuisisi: 5 unit
Kapitalisasi (Mouse + Tas): Rp 1.000.000

Perhitungan:
- Base Amount = 15.000.000 × 5 = 75.000.000
- Capitalization Amount = 1.000.000
- Total Amount = 75.000.000 + 1.000.000 = 76.000.000
- Amount per Unit = 76.000.000 ÷ 5 = 15.200.000

Setiap aset laptop akan tercatat dengan nilai Rp 15.200.000
```

#### Tab Kapitalisasi (Opsional)

Tab ini digunakan jika ada biaya tambahan yang ingin digabungkan ke nilai aset utama.

| Field            | Keterangan                               |
| ---------------- | ---------------------------------------- |
| **Good Receive** | Pilih GR lain yang berisi biaya tambahan |
| **GR Line**      | Pilih item yang akan dikapitalisasi      |
| **Qty**          | Jumlah yang dikapitalisasi               |
| **Price**        | Harga per unit                           |

**Kapan Menggunakan Kapitalisasi?**

- Membeli aksesoris yang menjadi bagian dari aset utama
- Biaya instalasi/setup yang harus masuk nilai aset
- Komponen tambahan untuk CIP

#### Tab Pengguna Asset (WAJIB)

> [!CAUTION] > **Tab ini WAJIB diisi!**  
> Jumlah baris di tab ini harus sama dengan Quantity di atas. Jika Quantity = 5, harus ada 5 baris pengguna.

| Field             | Keterangan                     | Wajib Diisi?            |
| ----------------- | ------------------------------ | ----------------------- |
| **Employee**      | Karyawan yang akan menggunakan | ✅ Ya                   |
| **Serial Number** | Nomor serial unit ini          | Tidak (tapi disarankan) |

**Cara Cepat Mengisi:**

- Jika semua unit untuk 1 orang yang sama, **centang "Pengguna Sama Semua?"** lalu pilih employee. Sistem akan otomatis mengisi semua baris.

### Penanganan CIP di Akuisisi

#### Jika ini CIP Pertama (Belum ada aset CIP)

1. Pilih Asset Category yang bertipe CIP
2. Biarkan field "Asset (CIP)" kosong
3. Sistem akan membuat aset baru dengan status "CIP"

#### Jika ini Kapitalisasi ke CIP Existing

1. Pilih Asset Category bertipe CIP
2. Pilih aset CIP yang sudah ada di field "Asset (CIP)"
3. Nilai akan ditambahkan ke aset CIP tersebut (TIDAK membuat aset baru)

#### Jika ini CIP Final

1. Centang "Is Final CIP?"
2. Sistem akan mengubah status aset dari "CIP" menjadi "Open/Running"
3. Depresiasi akan mulai berjalan

### Status Akuisisi Asset

| Status        | Arti               |
| ------------- | ------------------ |
| **Draft**     | Belum dikonfirmasi |
| **Done**      | Aset sudah dibuat  |
| **Cancelled** | Dibatalkan         |

### Apa yang Terjadi Saat Akuisisi Dikonfirmasi?

1. **Asset record** dibuat sesuai jumlah di tab Pengguna
2. Setiap aset memiliki:
   - Nama (dari Product)
   - Kode unik (generate otomatis)
   - Kategori aset
   - Nilai (Amount per Unit)
   - Jadwal depresiasi
   - Pengguna yang ditentukan
   - Serial number (jika diisi)
3. **Qty Acquired** di GR Line diupdate
4. Jika CIP Final: Aset langsung "Running" dan depresiasi dimulai

---

## Langkah 4: GR Collecting Asset

### Apa itu GR Collecting?

GR Collecting adalah proses **membuat invoice dan pembayaran** untuk aset yang sudah diterima. Ini adalah langkah terakhir yang menyelesaikan siklus pembelian aset.

### Mengapa Namanya "Collecting"?

> [!NOTE]
> Istilah "Collecting" berarti **mengumpulkan** beberapa penerimaan (GR) untuk dibuat menjadi satu invoice/pembayaran. Anda bisa menggabungkan beberapa GR dari vendor yang sama menjadi satu pembayaran.

### Cara Mengakses Menu

```
Menu: Asset Management → GR Collecting → Good Receive Collecting Asset
```

### Cara Membuat GR Collecting

1. **Klik tombol "New"**
2. **Pilih Branch**
3. **Pilih Vendor**
4. **Pilih Good Receive** yang akan di-collect (bisa lebih dari 1)
5. **Sistem otomatis mengisi lines** dari GR yang dipilih
6. **Isi informasi dokumen vendor** (Nomor Faktur, dll)
7. **Klik "Request Approval"** atau "Confirm"

### Penjelasan Field-field di GR Collecting

#### Bagian Header

| Field                | Keterangan                          | Wajib Diisi? | Contoh                 |
| -------------------- | ----------------------------------- | ------------ | ---------------------- |
| **Branch**           | Cabang yang melakukan pembayaran    | ✅ Ya        | Honda Pondok Indah     |
| **Vendor**           | Vendor yang akan dibayar            | ✅ Ya        | PT Astra International |
| **Date**             | Tanggal collecting                  | ✅ Ya        | 25/01/2026             |
| **Document No**      | Nomor invoice vendor                | Tidak        | INV-2026-001           |
| **Document Date**    | Tanggal invoice vendor              | Tidak        | 23/01/2026             |
| **No Faktur Pajak**  | Nomor faktur pajak vendor           | Tidak        | 010.000-26.00000001    |
| **Tgl Faktur Pajak** | Tanggal faktur pajak                | Tidak        | 23/01/2026             |
| **Payment Term**     | Termin pembayaran                   | Tidak        | 30 Days                |
| **Good Receive**     | Pilih GR yang akan di-collect       | ✅ Ya        | GR/HKA/00001           |
| **Collect All?**     | Centang untuk collect semua item GR | Tidak        | ☑️                     |

> [!NOTE] > **Tentang Field Faktur Pajak:**  
> Nomor faktur pajak penting untuk keperluan pelaporan pajak. Pastikan format sesuai dengan faktur fisik dari vendor.

#### Bagian Collecting Lines (Otomatis Terisi)

| Field           | Keterangan      |
| --------------- | --------------- |
| **Origin**      | Nomor GR asal   |
| **Product**     | Nama produk     |
| **Description** | Deskripsi       |
| **Qty**         | Jumlah          |
| **Price**       | Harga per unit  |
| **Taxes**       | Pajak           |
| **Subtotal**    | Total per baris |

> [!WARNING] > **Hati-hati dengan duplikasi!**  
> Sistem akan mencegah jika ada item yang sama muncul lebih dari sekali. Jika muncul error duplikasi, hapus salah satu baris yang sama.

### Status GR Collecting

| Status                   | Arti                 | Apa yang Harus Dilakukan?   |
| ------------------------ | -------------------- | --------------------------- |
| **Draft**                | Baru dibuat          | Lengkapi data, lalu confirm |
| **Waiting for Approval** | Menunggu persetujuan | Tunggu approver             |
| **Approved**             | Sudah disetujui      | Klik "Confirm"              |
| **Open**                 | Invoice sudah dibuat | Proses pembayaran           |
| **Done**                 | Sudah lunas          | Selesai ✅                  |
| **Cancel**               | Dibatalkan           | -                           |

### Apa yang Terjadi Saat GR Collecting Dikonfirmasi?

1. **Supplier Invoice** dibuat otomatis
2. **Journal Collecting** (JCA) dibuat
3. **Supplier Payment** (pembayaran ke vendor) dibuat
4. Status GR Line menjadi "Done"
5. Invoice langsung di-posting

---

## Penanganan CIP (Construction in Progress)

### Apa itu CIP?

CIP (Construction in Progress) atau **Aset Dalam Penyelesaian** adalah aset yang masih dalam proses pembangunan atau perakitan. Contoh:

- Pembangunan gedung baru
- Perakitan mesin produksi
- Pembuatan software (jika dikapitalisasi)

### Mengapa Perlu Perlakuan Khusus?

| Aset Normal                     | Aset CIP                                            |
| ------------------------------- | --------------------------------------------------- |
| Langsung dicatat & didepresiasi | Dikumpulkan dulu, baru didepresiasi setelah selesai |
| 1 penerimaan = 1 aset           | Banyak penerimaan bisa = 1 aset                     |
| Nilai tetap                     | Nilai bertambah seiring kapitalisasi                |

### Flow CIP Step-by-Step

```
                    FLOW CIP (CONSTRUCTION IN PROGRESS)

┌─────────────────┐
│ PO 1: Material  │──┐
└─────────────────┘  │    ┌─────────────────┐
                     ├───►│ GR 1: Material  │──┐
┌─────────────────┐  │    └─────────────────┘  │     ┌────────────────────┐
│ PO 2: Jasa      │──┤                         ├────►│ AKUISISI 1         │
└─────────────────┘  │    ┌─────────────────┐  │     │ (CIP Pertama)      │
                     └───►│ GR 2: Jasa      │──┘     │ Buat Aset Status=CIP│
                          └─────────────────┘        └─────────┬──────────┘
                                                               │
                                                               ▼
┌─────────────────┐       ┌─────────────────┐        ┌────────────────────┐
│ PO 3: Finishing │──────►│ GR 3: Finishing │───────►│ AKUISISI 2         │
└─────────────────┘       └─────────────────┘        │ (Kapitalisasi)     │
                                                     │ Tambah nilai ke CIP│
                                                     └─────────┬──────────┘
                                                               │
                                                               ▼
┌─────────────────┐       ┌─────────────────┐        ┌────────────────────┐
│ PO 4: Final     │──────►│ GR 4: Final     │───────►│ AKUISISI 3         │
└─────────────────┘       └─────────────────┘        │ (CIP Final)        │
                                                     │ ☑️ Is Final CIP    │
                                                     └─────────┬──────────┘
                                                               │
                                                               ▼
                                                     ┌────────────────────┐
                                                     │ ASET RUNNING       │
                                                     │ Depresiasi dimulai │
                                                     └────────────────────┘
```

### Langkah CIP Pertama:

1. Buat GR seperti biasa
2. Buat Akuisisi, pilih Asset Category bertipe CIP
3. **JANGAN** isi field "Asset (CIP)"
4. Confirm → Sistem membuat aset baru dengan status "CIP"

### Langkah Kapitalisasi:

1. Buat GR untuk penerimaan berikutnya
2. Buat Akuisisi baru
3. Pilih aset CIP yang sudah ada di field "Asset (CIP)"
4. Confirm → Nilai ditambahkan ke aset CIP (tidak buat aset baru)

### Langkah CIP Final:

1. Buat GR untuk penerimaan terakhir
2. Buat Akuisisi
3. Pilih aset CIP yang sudah ada
4. **Centang "Is Final CIP?"**
5. Confirm → Aset berubah menjadi running, depresiasi dimulai

---

## FAQ - Pertanyaan yang Sering Diajukan

### Umum

**Q: Saya tidak bisa melihat menu Asset Management, kenapa?**

> Anda mungkin tidak memiliki akses. Hubungi Administrator untuk diberikan akses ke group "Asset Management User" atau "Asset Management Manager".

**Q: Tombol Request Approval tidak muncul?**

> Pastikan:
>
> 1. Status dokumen masih "Draft"
> 2. Semua field wajib sudah diisi
> 3. Anda memiliki hak akses yang sesuai

---

### PO Asset

**Q: Saya salah input PO, bagaimana cara membatalkan?**

> - Jika status masih **Draft** atau **Waiting**: Klik "Cancel" atau hubungi approver
> - Jika sudah **Open**: Tidak bisa cancel langsung, hubungi Administrator
> - Jika sudah ada **GR**: Harus cancel GR dulu sebelum cancel PO

**Q: Vendor yang saya cari tidak ada di list?**

> Vendor harus didaftarkan terlebih dahulu di menu **Contacts** dengan tipe "Vendor". Hubungi tim Master Data untuk menambahkan vendor baru.

---

### GR Asset

**Q: Barang datang tidak sesuai pesanan, apa yang harus dilakukan?**

> 1. **Jika jumlah kurang**: Buat GR dengan qty sesuai yang diterima saja
> 2. **Jika barang rusak**: Jangan masukkan ke GR, koordinasi dengan vendor untuk retur
> 3. **Jika barang berbeda**: Jangan buat GR, koordinasi dengan Purchasing

**Q: Saya sudah confirm GR, tapi ternyata salah. Bisa dicancel?**

> Bisa, selama:
>
> - Belum ada Akuisisi yang dibuat dari GR tersebut
> - Jika sudah ada Akuisisi, cancel Akuisisi dulu

**Q: Kenapa muncul peringatan tentang "Is Asset?"?**

> Product yang dipilih memiliki Asset Category CIP tapi belum dicentang sebagai aset. Minta tim Master Data untuk mencentang field "Is Asset?" di Product.

---

### Akuisisi Asset

**Q: Berapa banyak aset yang akan dibuat?**

> Sama dengan angka di field **Quantity**. Misalnya Quantity = 5, maka akan terbuat 5 record aset terpisah.

**Q: Boleh tidak mengisi Serial Number?**

> Boleh, tapi sangat disarankan untuk mengisi. Serial Number membantu identifikasi unit spesifik saat audit atau maintenance.

**Q: Kenapa Tab Pengguna harus diisi?**

> Untuk tracking siapa yang bertanggung jawab atas setiap unit aset. Ini penting untuk:
>
> - Audit aset
> - Maintenance tracking
> - Mutasi aset antar karyawan

**Q: Bagaimana jika 1 unit dipakai bergantian oleh beberapa orang?**

> Isi dengan nama pengguna utama atau penanggung jawab unit tersebut. Sistem memiliki history pengguna jika nanti terjadi perubahan.

---

### GR Collecting

**Q: Saya collecting beberapa GR, tapi ada yang tidak muncul di list?**

> Cek:
>
> 1. GR sudah berstatus "Open" (bukan Draft)
> 2. GR dari vendor yang sama dengan yang dipilih
> 3. GR dari branch yang sama

**Q: Invoice sudah dibuat tapi ada kesalahan, bagaimana?**

> 1. Cancel GR Collecting (isi alasan cancel)
> 2. Sistem akan otomatis cancel invoice terkait
> 3. Buat GR Collecting baru yang benar

---

### CIP

**Q: Kapan harus centang "Is Final CIP?"**

> Centang ketika:
>
> - Ini adalah penerimaan **TERAKHIR** untuk proyek tersebut
> - Proyek sudah siap digunakan
> - Anda ingin **memulai depresiasi**

> [!CAUTION]
> Setelah dicentang dan dikonfirmasi, aset akan mulai didepresiasi sesuai kategori. Pastikan proyek memang sudah selesai.

**Q: Bagaimana jika CIP sudah di-finalize tapi ternyata ada biaya tambahan?**

> Hubungi Administrator atau Accounting. Mungkin perlu adjustment manual pada nilai aset.

---

## Tips dan Best Practice

### Do's ✅

1. **Selalu verifikasi fisik** sebelum membuat GR
2. **Isi Serial Number** untuk tracking yang lebih baik
3. **Simpan dokumen vendor** (faktur, surat jalan) dengan baik
4. **Cross-check jumlah** antara PO, GR, dan fisik barang
5. **Gunakan Description** untuk catatan tambahan yang berguna

### Don'ts ❌

1. **Jangan** membuat GR sebelum barang fisik diterima
2. **Jangan** mengabaikan peringatan sistem
3. **Jangan** mengubah tanggal dokumen sembarangan
4. **Jangan** skip langkah approval
5. **Jangan** centang "Is Final CIP" jika proyek belum selesai

---

## Kontak Support

Jika Anda mengalami kendala yang tidak tercakup dalam panduan ini, silakan hubungi:

| Tim             | Untuk Masalah                   | Kontak                 |
| --------------- | ------------------------------- | ---------------------- |
| **IT Support**  | Error sistem, tidak bisa akses  | helpdesk@company.com   |
| **Master Data** | Product/Vendor tidak ada        | masterdata@company.com |
| **Accounting**  | Pertanyaan terkait nilai/jurnal | accounting@company.com |

---

_Dokumen ini terakhir diperbarui: Januari 2026_  
_Versi: 1.0_
