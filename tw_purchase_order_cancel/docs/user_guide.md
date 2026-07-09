# Panduan Pembatalan Purchase Order (PO Cancel)

## Apa itu PO Cancel?

PO Cancel adalah fitur untuk **membatalkan Purchase Order** yang sudah diproses. Fitur ini memastikan:

- ✅ Stock yang sudah masuk akan dikembalikan (return ke supplier)
- ✅ Invoice yang sudah dibuat akan di-reverse
- ✅ Lot/Serial Number akan ditandai dengan prefix "X"

---

## Kapan Bisa Membatalkan PO?

| Kondisi                   | Bisa Cancel? | Keterangan                        |
| ------------------------- | ------------ | --------------------------------- |
| PO sudah bayar            | ❌           | Harus cancel **Payment** dulu     |
| Unit sudah dijual         | ❌           | Harus cancel **Sales Order** dulu |
| Sparepart sudah terpakai  | ❌           | Stock harus mencukupi             |
| PO dari Main Dealer (AHM) | ❌           | Tidak bisa dibatalkan             |

---

## Langkah-langkah Cancel PO

### 1️⃣ Buat Dokumen PO Cancel

1. Buka menu **Cancellation** → **PO Unit Cancel** atau **PO Sparepart Cancel**
2. Klik tombol **New**
3. Pilih **Branch** dan **Division** (Unit/Sparepart)
4. Pilih **Purchase Order** yang ingin dibatalkan
5. Isi **Alasan Pembatalan**
6. Klik **Save**

### 2️⃣ Request For Approval (RFA)

1. Setelah dokumen tersimpan, klik tombol **RFA**
2. Status berubah menjadi **Waiting For Approval**
3. Dokumen akan dikirim ke approver

### 3️⃣ Approval

1. Approver membuka dokumen PO Cancel
2. Review informasi dan alasan pembatalan
3. Klik **Approve** untuk menyetujui
4. Status berubah menjadi **Approved**

### 4️⃣ Confirm (Eksekusi Pembatalan)

1. User dengan akses confirm membuka dokumen yang sudah Approved
2. Klik tombol **Confirm**
3. Sistem akan otomatis:
   - Cancel/Return stock picking
   - Rename lot dengan prefix "X" (contoh: JDK1E130001 → XJDK1E130001)
   - Reverse invoice
   - Cancel Purchase Order

---

## Status Dokumen

| Status               | Warna   | Keterangan                          |
| -------------------- | ------- | ----------------------------------- |
| Draft                | Abu-abu | Baru dibuat, belum diajukan         |
| Waiting For Approval | Kuning  | Menunggu approval dari atasan       |
| Approved             | Biru    | Sudah disetujui, siap di-confirm    |
| Confirmed            | Hijau   | Pembatalan sudah selesai dieksekusi |

---

## FAQ

### ❓ Kenapa PO tidak muncul di dropdown?

**Kemungkinan penyebab:**

- PO sudah pernah di-cancel sebelumnya
- PO dari supplier Main Dealer (AHM)
- PO masih dalam status Draft atau belum dikonfirmasi
- Branch/Division tidak sesuai

### ❓ Kenapa muncul error "sudah dibayar"?

Jika PO sudah dibayar (ada Payment Voucher), Anda **harus cancel Payment dulu** sebelum bisa cancel PO.

### ❓ Apa arti prefix "X" pada Lot Number?

Prefix "X" menandakan bahwa unit tersebut **sudah di-cancel/return**. Contoh:

- Lot asli: `JDK1E1300001`
- Setelah cancel: `XJDK1E1300001`

### ❓ Bagaimana jika ada error saat Confirm?

Hubungi tim IT dengan menyertakan:

1. Screenshot error
2. Nomor PO yang ingin di-cancel
3. Nomor dokumen PO Cancel

---
