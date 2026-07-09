/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useDropzone } from "@web/core/dropzone/dropzone_hook";
import { useFileUploader } from "@web/core/utils/files";
import { BinaryField } from "@web/views/fields/binary/binary_field";
import {
    many2ManyBinaryField,
    Many2ManyBinaryField,
} from "@web/views/fields/many2many_binary/many2many_binary_field";
import { FileUploader } from "@web/views/fields/file_handler";
import { FileInput } from "@web/core/file_input/file_input";

import { useRef } from "@odoo/owl";

export class BinaryDropzoneField extends BinaryField {
    static template = "tw_file_dropzone_widget.BinaryDropzoneField";
    static components = {
        ...BinaryField.components,
        FileUploader,
    };

    setup() {
        super.setup();
        this.rootRef = useRef("root");

        useDropzone(
            this.rootRef,
            this.onDrop.bind(this),
            "o_web_dropzone",
            () => !this.props.readonly
        );
    }

    isAcceptedFile(file) {
        if (!this.props.acceptedFileExtensions || this.props.acceptedFileExtensions === "*") {
            return true;
        }
        const acceptedTypes = this.props.acceptedFileExtensions
            .split(",")
            .map((type) => type.trim().toLowerCase());
        const fileExtension = `.${file.name.split(".").pop().toLowerCase()}`;
        const fileType = (file.type || "").toLowerCase();

        return acceptedTypes.some((type) => {
            if (type.startsWith(".")) {
                return type === fileExtension;
            }
            if (type.endsWith("/*")) {
                return fileType.startsWith(type.replace("/*", ""));
            }
            return type === fileType;
        });
    }

    async onDrop(ev) {
        if (!ev.dataTransfer?.files?.length) {
            return;
        }

        const file = ev.dataTransfer.files[0];
        if (!this.isAcceptedFile(file)) {
            this.notification.add(_t("Unsupported file type."), { type: "danger" });
            return;
        }

        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = async () => {
            const result = reader.result;
            const dataBase64 = result.split(",")[1];
            await this.update({
                name: file.name,
                data: dataBase64,
                type: file.type,
                size: file.size,
            });
        };
        reader.onerror = (error) => {
            console.error("Error reading file:", error);
            this.notification.add(_t("Error reading file."), { type: "danger" });
        };
    }
}

export class Many2ManyBinaryDropzoneField extends Many2ManyBinaryField {
    static template = "tw_file_dropzone_widget.Many2ManyBinaryDropzoneField";
    static components = {
        FileInput,
    };

    setup() {
        super.setup();
        this.rootRef = useRef("root");
        this.uploadFiles = useFileUploader();

        useDropzone(
            this.rootRef,
            this.onDrop.bind(this),
            "o_web_dropzone",
            () => !this.props.readonly
        );
    }

    isAcceptedFile(file) {
        if (!this.props.acceptedFileExtensions || this.props.acceptedFileExtensions === "*") {
            return true;
        }
        const acceptedTypes = this.props.acceptedFileExtensions
            .split(",")
            .map((type) => type.trim().toLowerCase());
        const fileExtension = `.${file.name.split(".").pop().toLowerCase()}`;
        const fileType = (file.type || "").toLowerCase();

        return acceptedTypes.some((type) => {
            if (type.startsWith(".")) {
                return type === fileExtension;
            }
            if (type.endsWith("/*")) {
                return fileType.startsWith(type.replace("/*", ""));
            }
            return type === fileType;
        });
    }

    async onDrop(ev) {
        if (!ev.dataTransfer?.files?.length) {
            return;
        }

        const files = Array.from(ev.dataTransfer.files);
        const invalidFile = files.find((file) => !this.isAcceptedFile(file));
        if (invalidFile) {
            this.notification.add(_t("Unsupported file type."), { type: "danger" });
            return;
        }
        const remainingSlots = this.props.numberOfFiles
            ? Math.max(this.props.numberOfFiles - this.files.length, 0)
            : files.length;
        const filesToUpload = files.slice(0, remainingSlots);

        if (!filesToUpload.length) {
            return;
        }

        try {
            const parsedFileData = await this.uploadFiles("/web/binary/upload_attachment", {
                csrf_token: odoo.csrf_token,
                ufile: filesToUpload,
                model: this.props.record.resModel,
                id: this.props.record.resId || 0,
            });
            if (parsedFileData) {
                await this.onFileUploaded(parsedFileData);
            }
        } catch (error) {
            this.notification.add(error.message || _t("Uploading error"), {
                title: _t("Uploading error"),
                type: "danger",
            });
        }
    }
}

registry.category("fields").add("binary_dropzone", {
    ...registry.category("fields").get("binary"),
    component: BinaryDropzoneField,
    displayName: _t("Dropzone File"),
});

registry.category("fields").add("many2many_binary_dropzone", {
    ...many2ManyBinaryField,
    component: Many2ManyBinaryDropzoneField,
    displayName: _t("Dropzone Files"),
});
