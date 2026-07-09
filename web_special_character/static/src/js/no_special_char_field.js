/** @odoo-module **/
/**
 * No Special Character Field Widget (no_special_char)
 * 
 * Widget yang mencegah user memasukkan karakter spesial ke dalam input field.
 * Berguna untuk field seperti nama, alamat, dll yang tidak memerlukan karakter spesial.
 * 
 * KARAKTER YANG DIIZINKAN:
 * -------------------------
 * - Huruf      : A-Z, a-z (termasuk huruf Unicode seperti é, ñ, 中, dll)
 * - Angka      : 0-9
 * - Spasi      : whitespace
 * - Hyphen     : -
 * - Underscore : _
 * - Petik Satu : '
 * - Koma       : ,
 * - Titik      : .
 * 
 * KARAKTER YANG DIBLOKIR:
 * -------------------------
 * ` ~ ! @ # $ % ^ & * ( ) = + [ ] { } | \ ; : " < > ? /
 * 
 * PENGGUNAAN:
 * -------------------------
 * <field name="field_name" widget="no_special_char"/>
 * 
 * OPSI CUSTOM PATTERN:
 * -------------------------
 * <field name="field_name" widget="no_special_char" options="{'pattern': '^[A-Za-z0-9]*$'}"/>
 * 
 * @author Tunas Honda
 * @version 1.0
 */
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useDynamicPlaceholder } from "@web/views/fields/dynamic_placeholder_hook";
import { formatChar } from "@web/views/fields/formatters";
import { useInputField } from "@web/views/fields/input_field_hook";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { TranslationButton } from "@web/views/fields/translation_button";
import { useService } from "@web/core/utils/hooks";
import { Component, useEffect, useExternalListener, useRef } from "@odoo/owl";

const fields = registry.category("fields");

function buildPattern(opt) {
    // Allow: letters, numbers, whitespace, hyphen, underscore, single quote, comma, period
    const defaultPattern = "^[\\p{L}\\p{N}\\s\\-_',.]*$";
    const raw = (opt && opt.pattern) || defaultPattern;
    try {
        return new RegExp(raw, "u");
    } catch (e) {
        return /^[A-Za-z0-9 \-_',.]*$/;
    }
}

function sanitize(value, pattern) {
    let v = value || "";
    if (v.normalize) v = v.normalize("NFC");
    if (pattern.test(v)) return v;
    return [...v].filter((ch) => pattern.test(ch)).join("");
}

export class NoSpecialCharField extends Component {
    static template = "web.CharField";
    static components = { TranslationButton };
    static props = {
        ...standardFieldProps,
        autocomplete: { type: String, optional: true },
        isPassword: { type: Boolean, optional: true },
        placeholder: { type: String, optional: true },
        dynamicPlaceholder: { type: Boolean, optional: true },
        dynamicPlaceholderModelReferenceField: { type: String, optional: true },
        placeholderField: { type: String, optional: true },
    };
    static defaultProps = { dynamicPlaceholder: false };

    setup() {
        this.input = useRef("input");
        this.notification = useService("notification");

        // Get options
        const opt = this.props.options || {};
        this.allowSpecial = opt.allow_special_char === true;
        this.pattern = buildPattern(opt);

        // Debounce notification to prevent spam
        this._lastNotifyTime = 0;
        this._notifyDebounce = 1500; // 1.5 seconds

        console.log('[no_special_char] Setup. Field:', this.props.name, 'allowSpecial:', this.allowSpecial);

        if (this.props.dynamicPlaceholder) {
            this.dynamicPlaceholder = useDynamicPlaceholder(this.input);
            useExternalListener(document, "keydown", this.dynamicPlaceholder.onKeydown);
            useEffect(() =>
                this.dynamicPlaceholder.updateModel(
                    this.props.dynamicPlaceholderModelReferenceField
                )
            );
        }

        useInputField({
            getValue: () => this.props.record.data[this.props.name] || "",
            parse: (v) => this.parse(v),
        });

        this.selectionStart = this.props.record.data[this.props.name]?.length || 0;

        // Attach event listeners to input element after mount
        useEffect(
            (inputEl) => {
                if (!inputEl || this.allowSpecial) return;

                console.log('[no_special_char] Attaching event listeners to input');

                const onKeyDown = (ev) => {
                    const controlKeys = ['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight',
                        'ArrowUp', 'ArrowDown', 'Home', 'End', 'Tab', 'Enter', 'Escape'];
                    if (controlKeys.includes(ev.key) || ev.ctrlKey || ev.metaKey || ev.altKey) {
                        return;
                    }
                    if (ev.key && ev.key.length === 1 && !this.pattern.test(ev.key)) {
                        console.log('[no_special_char] Blocked key:', ev.key);
                        ev.preventDefault();
                        ev.stopPropagation();
                        this._showBlockedNotification(ev.key);
                    }
                };

                const onBeforeInput = (ev) => {
                    if (!ev.data) return;
                    for (const ch of ev.data) {
                        if (!this.pattern.test(ch)) {
                            console.log('[no_special_char] Blocked beforeinput:', ch);
                            ev.preventDefault();
                            ev.stopPropagation();
                            this._showBlockedNotification(ch);
                            return;
                        }
                    }
                };

                const onPaste = (ev) => {
                    ev.preventDefault();
                    const pastedText = (ev.clipboardData || window.clipboardData).getData('text');
                    const cleaned = sanitize(pastedText, this.pattern);
                    console.log('[no_special_char] Paste:', pastedText, '->', cleaned);

                    if (cleaned) {
                        const start = inputEl.selectionStart;
                        const end = inputEl.selectionEnd;
                        const currentValue = inputEl.value || "";
                        const newValue = currentValue.substring(0, start) + cleaned + currentValue.substring(end);
                        inputEl.value = newValue;
                        inputEl.setSelectionRange(start + cleaned.length, start + cleaned.length);
                        inputEl.dispatchEvent(new InputEvent("input", { bubbles: true }));
                    }
                };

                inputEl.addEventListener('keydown', onKeyDown, true);
                inputEl.addEventListener('beforeinput', onBeforeInput, true);
                inputEl.addEventListener('paste', onPaste, true);

                // Cleanup
                return () => {
                    inputEl.removeEventListener('keydown', onKeyDown, true);
                    inputEl.removeEventListener('beforeinput', onBeforeInput, true);
                    inputEl.removeEventListener('paste', onPaste, true);
                };
            },
            () => [this.input.el]
        );
    }

    get shouldTrim() {
        return this.props.record.fields[this.props.name].trim && !this.props.isPassword;
    }
    get maxLength() {
        return this.props.record.fields[this.props.name].size;
    }
    get isTranslatable() {
        return this.props.record.fields[this.props.name].translate;
    }
    get formattedValue() {
        return formatChar(this.props.record.data[this.props.name], {
            isPassword: this.props.isPassword,
        });
    }
    get hasDynamicPlaceholder() {
        return this.props.dynamicPlaceholder && !this.props.readonly;
    }
    get placeholder() {
        return this.props.record.data[this.props.placeholderField] || this.props.placeholder;
    }

    /**
     * Show notification when special character is blocked
     * Uses debounce to prevent notification spam
     */
    _showBlockedNotification(blockedChar) {
        const now = Date.now();
        if (now - this._lastNotifyTime < this._notifyDebounce) {
            return; // Skip if within debounce period
        }
        this._lastNotifyTime = now;

        this.notification.add(
            _t("Special character '%s' is not allowed in this field", blockedChar),
            {
                type: "warning",
                sticky: false,
            }
        );
    }

    parse(value) {
        // Sanitize value during parse
        if (!this.allowSpecial) {
            value = sanitize(value, this.pattern);
        }
        if (this.shouldTrim) {
            return value.trim();
        }
        return value;
    }

    onBlur() {
        this.selectionStart = this.input.el.selectionStart;
    }

    async onDynamicPlaceholderOpen() {
        await this.dynamicPlaceholder.open({
            validateCallback: this.onDynamicPlaceholderValidate.bind(this),
        });
    }

    async onDynamicPlaceholderValidate(chain, defaultValue) {
        if (chain) {
            this.input.el.focus();
            const dynamicPlaceholder = ` {{object.${chain}${defaultValue?.length ? ` ||| ${defaultValue}` : ""
                }}}`;
            this.input.el.setRangeText(
                dynamicPlaceholder,
                this.selectionStart,
                this.selectionStart,
                "end"
            );
            this.input.el.dispatchEvent(new InputEvent("input"));
            this.input.el.dispatchEvent(new KeyboardEvent("keydown"));
            this.input.el.focus();
        }
    }
}

export const noSpecialCharField = {
    component: NoSpecialCharField,
    displayName: _t("No Special Char"),
    supportedTypes: ["char"],
    extractProps: ({ attrs, options }) => ({
        isPassword: false,
        dynamicPlaceholder: options.dynamic_placeholder || false,
        dynamicPlaceholderModelReferenceField: options.dynamic_placeholder_model_reference_field || "",
        autocomplete: attrs.autocomplete,
        placeholder: attrs.placeholder,
        placeholderField: options.placeholder_field,
    }),
};

fields.add("no_special_char", noSpecialCharField);
