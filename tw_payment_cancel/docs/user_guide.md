# Panduan Pembatalan Payment (Payment Cancel)

## Apa itu Payment Cancel?

Payment Cancel adalah fitur untuk **membatalkan Payment Voucher** yang sudah diproses. Fitur ini akan:

- ✅ Reverse jurnal payment
- ✅ Mengubah status payment menjadi Canceled
- ✅ Membuka kembali invoice yang terkait

---

## Kapan Bisa Membatalkan Payment?

| Kondisi                    | Bisa Cancel? | Keterangan                         |
| -------------------------- | ------------ | ---------------------------------- |
| Payment sudah di-reconcile | ❌           | Harus un-reconcile dulu            |
| Unit sudah di-transfer     | ❌           | Harus reverse transfer dulu        |
| Periode sudah ditutup      | ❌           | Hubungi Finance untuk buka periode |

---

## Langkah-langkah Cancel Payment

### 1️⃣ Buat Dokumen Payment Cancel

1. Buka menu **Cancellation** → **Payment Cancel**
2. Klik tombol **New**
3. Pilih **Branch** dan **Division** (Unit/Sparepart)
4. Pilih **Account Payment** yang ingin dibatalkan
5. Isi **Alasan Pembatalan**
6. Klik **Save**

### 2️⃣ Request For Approval (RFA)

1. Setelah dokumen tersimpan, klik tombol **RFA**
2. Status berubah menjadi **Waiting For Approval**
3. Dokumen akan dikirim ke approver

### 3️⃣ Approval

1. Approver membuka dokumen Payment Cancel
2. Review informasi dan alasan pembatalan
3. Klik **Approve** untuk menyetujui
4. Status berubah menjadi **Approved**

### 4️⃣ Confirm (Eksekusi Pembatalan)

1. User dengan akses confirm membuka dokumen yang sudah Approved
2. Klik tombol **Confirm**
3. Sistem akan otomatis:
   - Membuat jurnal reversal
   - Mengubah status payment menjadi **Canceled**
   - Membuka kembali invoice terkait

---

## Status Dokumen

| Status               | Warna   | Keterangan                          |
| -------------------- | ------- | ----------------------------------- |
| Draft                | Abu-abu | Baru dibuat, belum diajukan         |
| Waiting For Approval | Kuning  | Menunggu approval dari atasan       |
| Approved             | Biru    | Sudah disetujui, siap di-confirm    |
| Confirmed            | Hijau   | Pembatalan sudah selesai dieksekusi |

---

## Hubungan dengan PO Cancel

Jika Anda ingin **Cancel Purchase Order** tetapi PO tersebut sudah dibayar:

```
1. Cancel Payment terlebih dahulu ← Wajib!
2. Setelah Payment Canceled, baru bisa Cancel PO
```

> ⚠️ **Penting:** Urutan cancel harus benar. PO Cancel tidak bisa dilakukan jika masih ada payment yang aktif.

---

## FAQ

### ❓ Kenapa Payment tidak muncul di dropdown?

**Kemungkinan penyebab:**

- Payment sudah pernah di-cancel sebelumnya
- Branch/Division tidak sesuai
- Payment masih dalam status Draft

### ❓ Kenapa muncul error "Invoice sudah dibayar"?

Jika ada invoice yang masih ter-reconcile dengan payment lain, Anda harus un-reconcile terlebih dahulu.

### ❓ Apa yang terjadi setelah Payment di-cancel?

1. **Payment status** → Canceled
2. **Jurnal reversal** → Dibuat otomatis
3. **Invoice** → Kembali terbuka (dapat dibayar ulang)

### ❓ Bagaimana melihat jurnal reversal?

Setelah Payment Cancel di-confirm, klik tombol **Journal Entry** pada dokumen cancel untuk melihat jurnal reversal yang dibuat.

---

## Checklist Sebelum Cancel Payment

- [ ] Pastikan payment sudah tidak ter-link ke transaksi lain
- [ ] Pastikan periode akuntansi masih terbuka
- [ ] Siapkan alasan pembatalan yang jelas
- [ ] Koordinasi dengan Finance jika diperlukan
