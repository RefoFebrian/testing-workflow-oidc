/** @odoo-module */
import { ListController } from '@web/views/list/list_controller';
import { patch } from "@web/core/utils/patch";
import { useSetupAction } from "@web/search/action_hook";
import { _t } from "@web/core/l10n/translation";
import { SettingsConfirmationDialog } from "@web/webclient/settings_form_view/settings_confirmation_dialog";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { ListConfirmationDialog } from "@web/views/list/list_confirmation_dialog";
import { user } from "@web/core/user";
import { rpc } from "@web/core/network/rpc";

patch(ListController.prototype, {
   /* Patch ListController to restrict auto save in tree views */
   setup() {
      super.setup(...arguments);
      useSetupAction({
         beforeLeave: () => this.beforeLeave(),
         //          beforeUnload: (ev) => this.beforeUnload(ev),
      });
      this.user = user;

      this.is_auto_save = true;

      this.env.services.orm.read("res.users", [this.user.userId], ["is_auto_save"])
         .then((result) => {
            this.is_auto_save = result[0]?.is_auto_save;
         });
   },
   async beforeLeave() {
      if (this.env.services.dialog.hasOpenDialogs?.()) {
         return false;
      }
      if (this.model.root?.isTransient) {
         return;
      }

      /* function will work before leave the list */
      // const result = await rpc("/web/dataset/call_kw", {
      //    model: "res.users",
      //    method: "read",
      //    args: [[this.user.userId], ["is_auto_save"]],
      //    kwargs: {},
      // });

      // const is_auto_save = result?.[0]?.is_auto_save;

      // const [userData] = await this.env.services.orm.read(
      //    "res.users",
      //    [this.user.userId],
      //    ["is_auto_save"]
      // );

      const is_auto_save = this.is_auto_save;
      console.log("is_auto_save", is_auto_save);
      if (this.model.root.editedRecord && is_auto_save === false) {
         if (confirm("Do you want to save changes before leaving?")) {
            return true
         } else {
            return false;
         }
      }
   },
});
