/** @odoo-module **/

import { registry } from "@web/core/registry";
import { CharField } from "@web/views/fields/char/char_field";
import { onMounted, onWillUpdateProps } from "@odoo/owl";

export class PdfUrlViewer extends CharField {
    static template = "tw_attachment.PdfUrlViewer";

    setup() {
        super.setup();
        
        onMounted(() => {
            this.updateIframe();
        });
        onWillUpdateProps((nextProps) => {
            this.updateIframe(nextProps);
        });
    }

    updateIframe(props) {
        const url = props ? props.record.data[this.props.name] : this.props.record.data[this.props.name];
        const iframe = document.getElementById(`pdf_iframe_${this.props.id}`);

        if (iframe && url && this.isValidPdfUrl(url)) {
            iframe.src = url;
            iframe.style.display = "block";
        } else if (iframe) {
            iframe.style.display = "none";
        }
    }

    isValidPdfUrl(url) {
        if (typeof url === 'string') {
            return url.toLowerCase().endsWith('.pdf');
        }
        return false;
    }
}

registry.category("fields").add("pdf_url_viewer", {
    component: PdfUrlViewer,
    supportedTypes: ["char"],
});