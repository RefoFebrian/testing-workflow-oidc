# 📖 PANDUAN PENGGUNA SALE ORDER CANCEL

## Daftar Isi

1. [Pendahuluan](#pendahuluan)
2. [Alur Proses Pembatalan](#alur-proses-pembatalan)
3. [Cara Membuat Sale Order Cancel](#cara-membuat-sale-order-cancel)
4. [Validasi Sebelum Pembatalan](#validasi-sebelum-pembatalan)
5. [FAQ - Pertanyaan yang Sering Diajukan](#faq---pertanyaan-yang-sering-diajukan)

---

## Pendahuluan

### Apa itu Sale Order Cancel?

Sale Order Cancel adalah modul untuk **membatalkan Sale Order (tw.sale.order)** yang sudah dikonfirmasi. Modul ini memastikan pembatalan dilakukan dengan benar, termasuk:

- Validasi bahwa invoice belum dibayar
- Validasi bahwa barang sudah dikembalikan (jika sudah dikirim)
- Pembatalan picking yang belum selesai
- Pembuatan jurnal reversal

### Mengapa Perlu Sistem Ini?

| Tanpa Sistem                        | Dengan Sistem                         |
| ----------------------------------- | ------------------------------------- |
| Pembatalan manual, rawan kesalahan  | Pembatalan terkontrol dengan validasi |
| Tidak ada audit trail               | Setiap pembatalan tercatat lengkap    |
| Tidak ada approval                  | Ada approval bertingkat               |
| Jurnal reversal harus dibuat manual | Jurnal reversal otomatis              |

### Siapa yang Menggunakan Sistem Ini?

- **Staff Sales/Admin** — Membuat permintaan pembatalan
- **Supervisor/Manager** — Memberikan persetujuan
- **Accounting** — Memastikan validasi keuangan

---

## Alur Proses Pembatalan

```
┌─────────────────────────────────────────────────────────────────────┐
│                   ALUR PROSES SALE ORDER CANCEL                      │
└─────────────────────────────────────────────────────────────────────┘

     ┌───────────────────┐
     │ 1. CREATE CANCEL  │ ← Staff membuat permintaan pembatalan
     │    (Draft)        │
     └────────┬──────────┘
              │ Klik "RFA" (Request for Approval)
              ▼
     ┌───────────────────┐
     │ 2. WAITING FOR    │ ← Menunggu persetujuan atasan
     │    APPROVAL       │
     └────────┬──────────┘
              │ Approver klik "Approve"
              ▼
     ┌───────────────────┐
     │ 3. APPROVED       │ ← Sudah disetujui
     └────────┬──────────┘
              │ Klik "Confirm"
              ▼
     ┌───────────────────┐
     │ 4. CONFIRMED      │ ← Pembatalan selesai
     └───────────────────┘
              │
              ├── Picking yang belum done → CANCELLED
              ├── Jurnal reversal → CREATED
              └── Sale Order → CANCELLED
```

---

## Cara Membuat Sale Order Cancel

### Akses Menu

**Untuk divisi Unit (dari menu Showroom):**

```
Menu: Showroom → Cancellation → Sale Order Cancel
```

**Untuk divisi Sparepart (dari menu Workshop):**

```
Menu: Workshop → Cancellation → Sale Order Cancel
```

> [!NOTE]
> Division akan otomatis terisi dan tidak bisa diubah sesuai menu yang diakses.

### Langkah-langkah

1. **Klik tombol "New"**
2. **Pilih Branch** — Cabang yang melakukan pembatalan
3. **Pilih Sale Order** — SO yang akan dibatalkan
4. **Isi Reason/Alasan** — Alasan pembatalan (wajib)
5. **Klik "RFA"** — Request for Approval
6. **Tunggu approval** dari atasan
7. **Setelah Approved, klik "Confirm"**

### Penjelasan Field-field

| Field          | Keterangan                          | Wajib? |
| -------------- | ----------------------------------- | ------ |
| **Branch**     | Cabang yang melakukan pembatalan    | ✅ Ya  |
| **Division**   | Unit/Sparepart (otomatis dari menu) | ✅ Ya  |
| **Date**       | Tanggal pembatalan                  | ✅ Ya  |
| **Sale Order** | Sale Order yang akan dibatalkan     | ✅ Ya  |
| **Reason**     | Alasan pembatalan                   | ✅ Ya  |

### Status Dokumen

| Status                   | Arti                          |
| ------------------------ | ----------------------------- |
| **Draft**                | Baru dibuat                   |
| **Waiting for Approval** | Menunggu persetujuan          |
| **Approved**             | Sudah disetujui, siap confirm |
| **Confirmed**            | Pembatalan selesai            |

---

## Validasi Sebelum Pembatalan

Sebelum pembatalan dikonfirmasi, sistem akan melakukan validasi:

### 1. Validasi Invoice

> [!IMPORTANT]
> **Invoice harus belum dibayar!**
>
> Jika ada invoice yang sudah dibayar atau direconcile, Anda harus:
>
> 1. Batalkan pembayaran customer terlebih dahulu
> 2. Unreoncile invoice
> 3. Baru bisa melanjutkan pembatalan SO

### 2. Validasi Shipment/Picking

> [!IMPORTANT]
> **Barang harus sudah dikembalikan!**
>
> Jika ada picking yang sudah done, semua barang harus di-return (reverse transfer) dahulu. Sistem akan mengecek:
>
> - Qty yang sudah dikirim
> - Qty yang sudah di-return
> - Selisih harus = 0

### 3. Validasi Unit (Khusus Division Unit)

> [!IMPORTANT]
> **Lot/Serial Number harus kembali ke internal location!**
>
> Untuk divisi Unit, sistem akan cek apakah unit (lot) sudah kembali ke lokasi internal.

---

## Apa yang Terjadi Saat Confirm?

1. **Picking yang belum done** → Otomatis di-cancel
2. **Jurnal reversal** → Dibuat otomatis untuk membalik jurnal invoice
3. **Sale Order** → Status berubah menjadi "Cancel"

---

## FAQ - Pertanyaan yang Sering Diajukan

**Q: Kenapa Sale Order tidak muncul di list pilihan?**

> Hanya Sale Order dengan status **'Sale' (Confirmed)** atau **'Done'** yang bisa dibatalkan.
>
> Pastikan:
>
> 1. Sale Order dari branch yang sama
> 2. Sale Order dari division yang sama
> 3. Sale Order sudah berstatus 'Sale' atau 'Done' (bukan Draft, Sent, Cancel, atau Unused)

**Q: Muncul error "Invoice sudah dibayar"?**

> Anda harus membatalkan pembayaran customer terlebih dahulu di menu Customer Payment/Payment Voucher.

**Q: Muncul error "Barang belum dikembalikan"?**

> Lakukan Reverse Transfer/Return di menu Stock untuk mengembalikan barang yang sudah dikirim.

**Q: Bisakah membatalkan SO yang belum ada invoice?**

> Bisa. Sistem tetap akan cancel picking yang pending dan mengubah status SO.

**Q: Siapa yang bisa approve pembatalan?**

> User yang memiliki akses approval sesuai limit yang ditentukan di master approval.

---

## Tips dan Best Practice

### Do's ✅

1. **Isi alasan yang jelas** — Untuk keperluan audit
2. **Pastikan semua validasi terpenuhi** sebelum request approval
3. **Komunikasikan dengan tim terkait** sebelum melakukan pembatalan

### Don'ts ❌

1. **Jangan** memaksakan pembatalan tanpa menyelesaikan validasi
2. **Jangan** asal isi alasan pembatalan
3. **Jangan** skip proses approval

---

_Dokumen ini terakhir diperbarui: Januari 2026_  
_Versi: 1.0_
