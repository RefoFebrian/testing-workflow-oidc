# 📖 PANDUAN PENGGUNA MUTATION ORDER CANCEL

## Daftar Isi

1. [Pendahuluan](#pendahuluan)
2. [Alur Proses Pembatalan](#alur-proses-pembatalan)
3. [Cara Membuat Mutation Order Cancel](#cara-membuat-mutation-order-cancel)
4. [Validasi Sebelum Pembatalan](#validasi-sebelum-pembatalan)
5. [FAQ - Pertanyaan yang Sering Diajukan](#faq---pertanyaan-yang-sering-diajukan)

---

## Pendahuluan

### Apa itu Mutation Order Cancel?

Mutation Order Cancel adalah modul untuk **membatalkan Mutation Order (tw.mutation.order)** yang sudah dikonfirmasi. Modul ini memastikan pembatalan dilakukan dengan benar, termasuk:

- Validasi bahwa picking belum di-transfer
- Pembatalan picking yang belum selesai
- Perubahan status Mutation Order menjadi cancel

### Mengapa Perlu Sistem Ini?

| Tanpa Sistem                       | Dengan Sistem                         |
| ---------------------------------- | ------------------------------------- |
| Pembatalan manual, rawan kesalahan | Pembatalan terkontrol dengan validasi |
| Tidak ada audit trail              | Setiap pembatalan tercatat lengkap    |
| Tidak ada approval                 | Ada approval bertingkat               |
| Stock move tidak terhandle         | Picking otomatis di-cancel            |

### Siapa yang Menggunakan Sistem Ini?

- **Staff Gudang/Warehouse** — Membuat permintaan pembatalan
- **Supervisor/Manager** — Memberikan persetujuan

---

## Alur Proses Pembatalan

```
┌─────────────────────────────────────────────────────────────────────┐
│                 ALUR PROSES MUTATION ORDER CANCEL                    │
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
              └── Mutation Order → CANCELLED
```

---

## Cara Membuat Mutation Order Cancel

### Akses Menu

```
Menu: Warehouse/Showroom/Workshop → Cancellation → Mutation Order Cancel
```

### Langkah-langkah

1. **Klik tombol "New"**
2. **Pilih Branch** — Cabang yang melakukan pembatalan
3. **Pilih Division** — Unit/Sparepart
4. **Pilih Mutation Order** — MO yang akan dibatalkan
5. **Isi Reason/Alasan** — Alasan pembatalan (wajib)
6. **Klik "RFA"** — Request for Approval
7. **Tunggu approval** dari atasan
8. **Setelah Approved, klik "Confirm"**

### Penjelasan Field-field

| Field              | Keterangan                          | Wajib? |
| ------------------ | ----------------------------------- | ------ |
| **Branch**         | Cabang yang melakukan pembatalan    | ✅ Ya  |
| **Division**       | Unit/Sparepart                      | ✅ Ya  |
| **Date**           | Tanggal pembatalan                  | ✅ Ya  |
| **Mutation Order** | Mutation Order yang akan dibatalkan | ✅ Ya  |
| **Reason**         | Alasan pembatalan                   | ✅ Ya  |

### Status Dokumen

| Status                   | Arti                          |
| ------------------------ | ----------------------------- |
| **Draft**                | Baru dibuat                   |
| **Waiting for Approval** | Menunggu persetujuan          |
| **Approved**             | Sudah disetujui, siap confirm |
| **Confirmed**            | Pembatalan selesai            |

---

## Validasi Sebelum Pembatalan

> [!CAUTION]
> **Picking TIDAK BOLEH sudah di-transfer (done)!**
>
> Jika ada picking yang sudah berstatus "Done", pembatalan **TIDAK BISA** dilakukan. Anda harus:
>
> 1. Selesaikan proses mutasi yang sudah berjalan
> 2. Lakukan **mutasi balik** untuk mengembalikan stock ke lokasi asal
> 3. Pembatalan Mutation Order hanya bisa dilakukan jika **belum ada transfer sama sekali**

### Mengapa Tidak Bisa Cancel Jika Sudah Transfer?

```
Mutation Order: Branch A → Branch B

Jika sudah transfer:
- Stock sudah berpindah ke Branch B
- Cancel akan menyebabkan "stock hilang" di sistem
- Solusi: Buat Mutation Order baru dari Branch B → Branch A (mutasi balik)
```

---

## Apa yang Terjadi Saat Confirm?

1. **Validasi shipment** — Cek apakah ada picking yang sudah done
2. **Picking cancel** — Semua picking yang pending di-cancel
3. **Mutation Order cancel** — Status MO berubah menjadi cancelled

---

## FAQ - Pertanyaan yang Sering Diajukan

**Q: Muncul error "Picking sudah ditransfer"?**

> Mutation Order tidak bisa dibatalkan karena barang sudah di-transfer. Anda harus membuat Mutation Order baru untuk mengembalikan barang (mutasi balik).

**Q: Mutation Order tidak muncul di list pilihan?**

> Hanya Mutation Order dengan status **'Confirmed'** yang bisa dibatalkan.
>
> Pastikan:
>
> 1. Mutation Order dari branch yang sesuai
> 2. Mutation Order dari division yang sesuai
> 3. Mutation Order sudah berstatus 'Confirmed' (bukan Draft, Done, atau Cancelled)

**Q: Bisakah membatalkan sebagian qty saja?**

> Tidak. Pembatalan Mutation Order bersifat keseluruhan. Jika ingin mengurangi qty, buat Mutation Order baru dengan qty yang benar.

**Q: Siapa yang bisa approve pembatalan?**

> User yang memiliki akses approval sesuai limit yang ditentukan di master approval.

**Q: Bagaimana jika picking sudah partial (sebagian sudah transfer)?**

> Pembatalan tidak bisa dilakukan. Selesaikan transfer yang tersisa, lalu buat mutasi balik jika diperlukan.

---

## Tips dan Best Practice

### Do's ✅

1. **Batalkan secepatnya** — Sebelum picking di-transfer
2. **Isi alasan yang jelas** — Untuk keperluan audit dan tracking
3. **Koordinasi dengan branch tujuan** — Agar tidak terjadi konflik

### Don'ts ❌

1. **Jangan** menunggu terlalu lama untuk membatalkan jika memang harus batal
2. **Jangan** memaksakan cancel jika picking sudah done
3. **Jangan** skip proses approval

---

## Perbedaan dengan Mutasi Balik

| Mutation Order Cancel      | Mutasi Balik                    |
| -------------------------- | ------------------------------- |
| Untuk picking yang PENDING | Untuk picking yang sudah DONE   |
| Cancel MO langsung         | Buat MO baru arah sebaliknya    |
| Tidak ada transfer terjadi | Ada 2x transfer (pergi + balik) |
| Status MO = Cancelled      | MO lama tetap Done, ada MO baru |

---

_Dokumen ini terakhir diperbarui: Januari 2026_  
_Versi: 1.0_
