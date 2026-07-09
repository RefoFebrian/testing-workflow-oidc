/** @odoo-module **/
import { Component, onMounted, onWillUnmount, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";

function rupiah(n) {
  try {
    return n.toLocaleString("id-ID");
  } catch {
    return n;
  }
}

class QrisClient extends Component {
  static template = "tw_qris_display.BackendPage";

  setup() {
    this.bus = useService("bus_service");

    this.state = useState({
      displayCode: this.props?.action?.context?.display_code || "KASIR-01",
      amountText: "Rp 0",
      qrisSrc: "",
      statusText: "",
      imageError: false,  // ✅ track broken image
    });

    this._unsub = null;

    onMounted(() => {
      console.log("[QRIS] Mounted. displayCode:", this.state.displayCode);

      this._unsub = this.bus.subscribe("qris_notif", (payload) => {
        console.log("[QRIS] recv payload:", payload);
        if (!payload || payload.display_code !== this.state.displayCode) return;

        this.state.amountText = "Rp " + rupiah(payload.amount ?? 0);
        this.state.statusText = payload.expires_at
          ? `Berlaku hingga ${payload.expires_at}`
          : "";

        // Reset error state
        this.state.imageError = false;

        // Assign QR    
        if (payload.qris_base64) {
            this.state.qrisSrc = `data:image/png;base64,${payload.qris_base64}`;
            this.state.imageError = false;
        } else {
          this.state.qrisSrc = "";
          this.state.imageError = true;
        }
      });

      this.bus.start();
      console.log("[QRIS] bus_service started (subscribe qris_notif)");
    });

    onWillUnmount(() => {
      try {
        if (this._unsub) this._unsub();
      } catch {}
    });
  }

  // ✅ When the image fails to load
  handleImageError() {
    console.warn("[QRIS] image failed to render — showing fallback text");
    this.state.imageError = true;
  }
}

registry.category("actions").add("qris_display.client", QrisClient);
export default QrisClient;
