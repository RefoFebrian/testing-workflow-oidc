/** @odoo-module **/

/*
Fitur : Mengubah text dialog error menjadi bahasa Indonesia
*/

import { WarningDialog, standardErrorDialogProps } from "@web/core/errors/error_dialogs";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";


export class CustomWarningDialog extends WarningDialog {
    setup() {
        this.title = _t("Oops! Ada kesalahan, periksa lagi datamu.");
        const { data, message } = this.props;
        if (data && data.arguments && data.arguments.length > 0) {
            this.message = data.arguments[0];
        } else {
            this.message = message;
        }
     }

}
CustomWarningDialog.template = "web.WarningDialog";
CustomWarningDialog.components = { Dialog };
CustomWarningDialog.props = {
    ...standardErrorDialogProps,
    title: { type: String, optional: true },
};
registry
    .category("error_dialogs")
    .add("odoo.exceptions.UserError", CustomWarningDialog, { force: true });

    