/** @odoo-module **/

import { ReCaptcha } from "@google_recaptcha/js/recaptcha";
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.LoginCaptcha = publicWidget.Widget.extend({
    selector: 'form[data-recaptcha-enabled]',
    events: {
        'submit': '_onSubmit',
    },

    /**
     * @override
     */
    start() {
        this.recaptchaEnabled = this.$el.data('recaptcha-enabled');
        this.recaptchaVersion = this.$el.data('recaptcha-version') || 'v3_invisible';
        this.siteKey = this.$el.data('site-key');
        
        console.log("[LoginCaptcha] Start. Enabled:", this.recaptchaEnabled, "Version:", this.recaptchaVersion, "SiteKey:", this.siteKey);
        
        if (this.recaptchaEnabled) {
             if (this.recaptchaVersion === 'v3_invisible') {
                console.log("[LoginCaptcha] Loading v3");
                this._recaptcha = new ReCaptcha();
                this._recaptcha.loadLibs();
            } else if (this.recaptchaVersion === 'v2_checkbox') {
                console.log("[LoginCaptcha] Loading v2");
                this._loadV2Lib();
            }
        }
        return this._super(...arguments);
    },

    _loadV2Lib() {
        console.log("[LoginCaptcha] _loadV2Lib called");
        if (window.grecaptcha && window.grecaptcha.render) {
             console.log("[LoginCaptcha] grecaptcha already ready");
             this._renderV2Widget();
             return;
        }

        if (!document.getElementById('recaptcha-v2-lib')) {
            console.log("[LoginCaptcha] Injecting script");
            // Define global callback
            window.odoo_recaptcha_v2_onload = () => {
                console.log("[LoginCaptcha] Global callback fired");
                this._renderV2Widget();
                delete window.odoo_recaptcha_v2_onload;
            };

            const script = document.createElement('script');
            script.id = 'recaptcha-v2-lib';
            script.src = 'https://www.google.com/recaptcha/api.js?onload=odoo_recaptcha_v2_onload&render=explicit';
            script.async = true;
            script.defer = true;
            document.head.appendChild(script);
            
            script.onerror = () => {
                console.error("[LoginCaptcha] Script load error");
                this._displayError("Failed to load Google reCAPTCHA library. Please check your internet connection.");
            }
        }
    },
    
    _renderV2Widget() {
         console.log("[LoginCaptcha] _renderV2Widget called");
         const container = document.getElementById('recaptcha_v2_container');
         if (!container) {
             console.error("[LoginCaptcha] Container not found!");
             return;
         }

         if (window.grecaptcha && window.grecaptcha.render) {
             console.log("[LoginCaptcha] grecaptcha.render exists, attempting render");
             try {
                 // Clear previous if any (though widget usually manages this)
                 container.innerHTML = ''; 
                 
                 this._v2WidgetId = window.grecaptcha.render('recaptcha_v2_container', {
                     'sitekey': this.siteKey,
                     'theme': 'light', // explicitly set theme
                     'callback': (token) => {
                         console.log("[LoginCaptcha] Token received via callback");
                         this.$('.o_recaptcha_token_response').val(token);
                         this._removeError();
                     },
                     'error-callback': () => {
                        console.error("[LoginCaptcha] Google Error Callback fired");
                        this._displayError("Google reCAPTCHA Error. Please check your Site Key configuration.");
                     }
                 });
                 console.log("[LoginCaptcha] Render called, ID:", this._v2WidgetId);
             } catch (e) {
                 console.error("[LoginCaptcha] Render exception:", e);
                 this._displayError("Failed to render reCAPTCHA: " + e.message);
             }
         } else {
             console.error("[LoginCaptcha] grecaptcha.render NOT found even after load");
         }
    },

    _removeError() {
        this.$('.o_login_captcha_error').remove();
    },

    _displayError(message) {
        // Remove existing JS errors
        this.$('.o_login_captcha_error').remove();
        
        const $error = $('<p class="alert alert-danger o_login_captcha_error" role="alert"/>').text(message);
        // Prepend to form or insert before specific element
        if (this.$('.mb-3.field-login').length) {
             $error.insertBefore(this.$('.mb-3.field-login'));
        } else {
             this.$el.prepend($error);
        }
    },

    /**
     * @private
     * @param {Event} ev
     */
    async _onSubmit(ev) {
        if (!this.recaptchaEnabled) {
            return;
        }

        if (this.$('.o_recaptcha_token_response').val()) {
            return;
        }

        ev.preventDefault();
        const button = this.$('button[type="submit"]');
        button.prop('disabled', true);
        
        try {
            let token = null;
            
            if (this.recaptchaVersion === 'v3_invisible') {
                const tokenObj = await this._recaptcha.getToken('login');
                if (tokenObj.token) {
                    token = tokenObj.token;
                } else if (tokenObj.error) {
                    this._displayError("reCAPTCHA Error: " + tokenObj.error);
                }
            } else if (this.recaptchaVersion === 'v2_checkbox') {
                token = window.grecaptcha.getResponse(this._v2WidgetId);
                if (!token) {
                     this._displayError("Please check the box to verify you are not a robot.");
                     button.prop('disabled', false);
                     return;
                }
            }
            
            if (token) {
                this.$('.o_recaptcha_token_response').val(token);
                this.$el.submit();
            } else {
                 // Even if token missing (v3 fallthrough), submit to let backend show error
                 this.$el.submit();
            }
            
        } catch (e) {
            console.error("Captcha Error", e);
            this._displayError("An error occurred with reCAPTCHA: " + e.message);
            button.prop('disabled', false);
        }
    },
});
