/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";
import { rpcBus } from "@web/core/network/rpc";
import { router } from "@web/core/browser/router";
import { _t } from "@web/core/l10n/translation";

class GlobalRpcErrorListener extends Component {
    static props = {};
    setup() {
        super.setup(...arguments);
        this.notificationService = useService("notification");
        this.actionService = useService("action");
        this.orm = useService("orm");
        rpcBus.addEventListener("RPC:RESPONSE", (ev) => {
            this._notify(ev);
        });
  }

  async _notify(ev) {
    const payload = ev.detail;
    // Check if its UserError, if not then skip.
    if (payload.error && payload.error.data != null && payload.error.data.name == 'odoo.exceptions.UserError') {
        let is_show_notification = true;
        const action_data = {
            type: 'ir.actions.act_window',
            name: _t('Transaction'),
            target: 'current',
            res_model: payload.error.model,
        }
        // Some error dont have args, skip it
        if (payload.data.params.args) {
            action_data['views'] = [[false, 'form']];
            const ids = payload.data.params.args[0]
            // if the ID is not there, we assume that its not regular odoo Process that need a warning
            if (ids != null){
                // if the ID length is only 1, then we assume that the Event is triggered from a form
                if (ids.length == 1){
                    const transaction_id = ids[0]
                    const url_array = window.location.pathname.split('/')
                    const path_name = url_array[2]
                    const path_id = url_array[url_array.length -1]
                    // We try to identify, if the user is still in the trigger form, then dont need to show the global warning pop up
                    // Identification based on id on the event payload argument and URL/Path
                    if (transaction_id == path_id){
                        // Identification based action name that contain model and model name from event payload
                        if (path_name == payload.error.model){
                            is_show_notification = false;
                        // Identification based action name that using path name and model name from event payload
                        }else{
                            let model = await this.orm.searchRead("ir.model",[['model','=',payload.error.model]],["id"]);
                            let actions = await this.orm.searchRead("ir.actions.act_window",[['path','=',path_name],['binding_model_id','=',model[0].id]],["id"]);
                            if (actions){
                                is_show_notification = false;
                            }
                        }
                    }
                    action_data['res_id'] = transaction_id;
                // if the ID length is more than 1, then direct it to tree
                } else {
                    action_data['domain'] = [('id','in',ids)];
                }
            }
        } else{
            action_data['views'] = [[false, 'list']];
        }
        if (is_show_notification){
            this.notificationService.add(_t(payload.error.data.message), {
                title: "Failed",
                type: "danger",
                sticky: false,
                buttons: [{
                    name: "Go to Transaction",
                    primary: true,
                    onClick: () => {
                        this.actionService.doAction(action_data);
                        return true; // This will close the notification
                    },
                }]
            });
        }
    }
    }
}
GlobalRpcErrorListener.template = "global_rpc_error_listener_template";
export const systrayItem = { Component: GlobalRpcErrorListener,};
registry.category("systray").add("GlobalRpcErrorListener", systrayItem, { sequence: 1 });
