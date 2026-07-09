/** @odoo-module **/

/*
Fitur : Mengatasi bug dialog error yang muncul jika terkena validasi di saat create record.
BUG : Saat dialog muncul dan user tidak meng-klik "Stay Here" dan malah menekan "ESC" di keyboard, maka
method resolve tidak terpanggil, sehingga tombol-tombol seperti "Save" dan "Discard" tetap terdisable dan 
field-field tetap terdisable secara JS walaupun secara UI bisa di ganti.

FIX : Memanggil method resolve dan discard otomatis saat form dialog di discard menggunakan tombol "ESC" di keyboard.
*/

import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";
import { FormErrorDialog } from "@web/views/form/form_error_dialog/form_error_dialog";

patch(FormController.prototype, {
    async onSaveError(error, { discard }) {
        const proceed = await new Promise((resolve) => {
            this.model.dialog.add(
                FormErrorDialog,
                {
                    message: error.data.message,
                    data: error.data,
                    onDiscard: () => {
                        discard();
                        resolve(true);
                    },
                    onRedirect: async ({ action, additionalContext }) => {
                        this.allowLeavingWithoutSaving = true;
                        try {
                            await this.actionService.doAction(action, {
                                additionalContext,
                            });
                        } finally {
                            this.allowLeavingWithoutSaving = false;
                            resolve(false);
                        }
                    },
                    onStayHere: () => resolve(false),
                },
                {
                    onClose: () => resolve(false),
                }
            );
        });
        return proceed;
    }
});
