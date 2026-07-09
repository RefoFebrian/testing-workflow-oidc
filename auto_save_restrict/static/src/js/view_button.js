import { patch } from "@web/core/utils/patch";
import { ViewButton } from "@web/views/view_button/view_button";
import { SettingsConfirmationDialog } from "@web/webclient/settings_form_view/settings_confirmation_dialog";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { pick } from "@web/core/utils/objects";
import { user } from "@web/core/user";
import { rpc } from "@web/core/network/rpc";

patch(ViewButton.prototype, {
    setup() {
        super.setup(...arguments);
        this.dialogService = useService("dialog");
        this.user = user;
    },

    async _isTransientModel(modelName) {
        if (!modelName) {
            return false;
        }
        const result = await rpc("/web/dataset/call_kw", {
            model: "ir.model",
            method: "search_read",
            args: [[["model", "=", modelName]], ["transient"]],
            kwargs: { limit: 1 },
        });
        return !!result?.[0]?.transient;
    },

    async onClick(ev) {
        const model = this.env.model;
        const currentTarget = ev.currentTarget;
        const result = await rpc("/web/dataset/call_kw", {
            model: "res.users",
            method: "read",
            args: [[this.user.userId], ["is_auto_save"]],
            kwargs: {},
        });
        const is_auto_save = result?.[0]?.is_auto_save;

        const resModel = model?.root?.resModel;
        const isTransient = await this._isTransientModel(resModel);
        console.log("model", resModel);

        if (model && model.root && typeof model.root.isDirty === 'function') {
            const isDirty = await model.root.isDirty();

            if (isDirty) {
                if (is_auto_save === false && !isTransient) {
                    const proceed = await this._confirmSave();
                    if (!proceed) {
                        return;
                    }
                }
            }
        }
        if (!currentTarget || !document.body.contains(currentTarget)) {
            console.warn("Elemen tombol sudah tidak ada di DOM, membatalkan super.onClick untuk mencegah error.");
            return;
        }
        return super.onClick(ev);
    },

    discard() {
        const model = this.props.record || this.props.model;

        if (!model) {
            console.warn("No model available to discard or save.");
            return;
        }

        this.env.onClickViewButton({
            clickParams: {
                name: "cancel",
                type: "object",
                special: "cancel",
            },
            getResParams: () =>
                pick(model, "context", "evalContext", "resModel", "resId", "resIds"),
        });
    },

    async _confirmSave() {
        let _continue = true;

        await new Promise((resolve) => {
            this.dialogService.add(SettingsConfirmationDialog, {
                body: _t("Would you like to save your changes?"),
                confirm: async () => {
                    _continue = true;
                    resolve();
                },
                cancel: async () => {
                    const model = this.props.record || this.props.model;
                    if (model) {
                        await model?.discard?.();
                        await model?.save?.();
                    } else {
                        console.warn("No model available to discard or save.");
                    }
                    _continue = true;
                    resolve();
                },
                stayHere: () => {
                    _continue = false;
                    resolve();
                },
            });
        });

        return _continue;
    },
});
