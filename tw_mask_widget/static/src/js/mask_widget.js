/** @odoo-module **/
/**
 * Sensitive Information Masking Widget for Odoo 18
 *
 * Usage:
 *   <field name="mobile" widget="mask_sensitive" options="{'mask_type': 'phone'}"/>
 *   <field name="work_email" widget="mask_sensitive" options="{'mask_type': 'email'}"/>
 *   <field name="identification_id" widget="mask_sensitive" options="{'mask_type': 'id'}"/>

 * mask_type options:
 *   - 'phone': 08*********2 (show first 2, last 1)
 *   - 'email': j******e@e******.com
 *   - 'id': 3171**********90 (show first 4, last 2)
 */
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { charField } from "@web/views/fields/char/char_field";
import { useInputField } from "@web/views/fields/input_field_hook";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";
import { Component, useRef, onWillStart, useEffect } from "@odoo/owl";

// Cache admin check
let _isAdminCache = null;
let _adminCheckPromise = null;

export class MaskSensitiveField extends Component {
  static template = "web.CharField";
  static props = {
    ...standardFieldProps,
    placeholder: { type: String, optional: true },
    options: { type: Object, optional: true },
  };

  setup() {
    this.input = useRef("input");
    this.orm = useService("orm");
    this.isAdminUser = _isAdminCache === true;
    this.userModified = false;
    this.isFocused = false;

    onWillStart(async () => {
      await this._checkAdminStatus();
    });

    // Custom useInputField that returns MASKED value for display
    useInputField({
      getValue: () => {
        // When focused or user modified, return actual input value for editing
        if (this.isFocused) {
          return this.input.el?.value || "";
        }
        if (this.userModified && this.input.el) {
          return this.input.el.value;
        }
        // Otherwise return masked value for display
        return this._maskValue(this._getOriginalValue());
      },
      parse: (v) => this._parseValue(v),
    });

    // Handle mousedown and focus via useEffect
    useEffect(
      (inputEl) => {
        if (!inputEl || this.props.readonly) return;

        const onMouseDown = () => {
          if (!this.isFocused) {
            inputEl.value = "";
          }
        };

        const onFocus = () => {
          this.isFocused = true;
          inputEl.value = "";
        };

        inputEl.addEventListener("mousedown", onMouseDown);
        inputEl.addEventListener("focus", onFocus);

        return () => {
          inputEl.removeEventListener("mousedown", onMouseDown);
          inputEl.removeEventListener("focus", onFocus);
        };
      },
      () => [this.input.el]
    );
  }

  async _checkAdminStatus() {
    if (_isAdminCache !== null) {
      this.isAdminUser = _isAdminCache;
      return;
    }
    if (_adminCheckPromise) {
      try { this.isAdminUser = await _adminCheckPromise; } catch { this.isAdminUser = false; }
      return;
    }
    try {
      _adminCheckPromise = this.orm.call("res.users", "check_mask_admin", []);
      this.isAdminUser = _isAdminCache = await _adminCheckPromise;
    } catch {
      this.isAdminUser = _isAdminCache = false;
    }
  }

  _getOriginalValue() {
    return this.props.record.data[this.props.name] || "";
  }

  _parseValue(value) {
    const original = this._getOriginalValue();
    const masked = this._maskValue(original);
    // If user entered the masked value or empty, keep original
    if (!this.userModified || value === masked || value === "") {
      return original;
    }
    return value;
  }

  // Method called by web.CharField template via t-on-blur
  onBlur() {
    this.isFocused = false;
    if (this.input.el) {
      if (!this.input.el.value) {
        this.input.el.value = this._maskValue(this._getOriginalValue());
        this.userModified = false;
      } else {
        this.userModified = true;
      }
    }
  }

  // Required getters for web.CharField template
  get isTranslatable() {
    return false;
  }

  get maxLength() {
    return this.props.record.fields[this.props.name]?.size || 0;
  }

  get maskType() {
    return this.props.options?.mask_type || "phone";
  }

  get formattedValue() {
    return this._maskValue(this._getOriginalValue());
  }

  get hasDynamicPlaceholder() {
    return false;
  }

  get placeholder() {
    return this.props.placeholder || "";
  }

  _maskValue(value) {
    if (!value) return "";
    const str = String(value);
    if (this.isAdminUser) return str;

    switch (this.maskType) {
      case "email": return this._maskEmail(str);
      case "id": return this._maskId(str);
      default: return this._maskPhone(str);
    }
  }

  _maskPhone(v) {
    if (v.length <= 3) return v;
    return v.slice(0, 2) + "*".repeat(v.length - 3) + v.slice(-1);
  }

  _maskEmail(v) {
    const [local, domain] = v.split("@");
    if (!domain) return v;
    const ml = local.length <= 2 ? local[0] + "*" : local[0] + "*".repeat(local.length - 2) + local.slice(-1);
    const dp = domain.split(".");
    const md = dp.length >= 2
      ? (dp[0].length <= 1 ? dp[0] + "*****" : dp[0][0] + "*".repeat(dp[0].length - 1)) + "." + dp.slice(1).join(".")
      : domain[0] + "*".repeat(domain.length - 1);
    return ml + "@" + md;
  }

  _maskId(v) {
    if (v.length <= 6) return v;
    return v.slice(0, 4) + "*".repeat(v.length - 6) + v.slice(-2);
  }
}

export const maskSensitiveField = {
  ...charField,
  component: MaskSensitiveField,
  displayName: _t("Mask Sensitive"),
  supportedTypes: ["char", "text"],
  extractProps: ({ attrs, options }) => ({
    placeholder: attrs.placeholder,
    options: options,
  }),
};

registry.category("fields").add("mask_sensitive", maskSensitiveField);
