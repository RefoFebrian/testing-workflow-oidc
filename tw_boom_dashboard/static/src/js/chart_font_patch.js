/** @odoo-module **/

/**
 * Generic patch for amCharts 5 to support dynamic font family from Odoo dashboard.
 * This monkey-patches am5.Root.new to inherit font-family from the container div.
 */

(function () {
    function applyPatch() {
        if (window.am5 && !window.am5._root_font_patched) {
            const originalRootNew = am5.Root.new;
            am5.Root.new = function (container, settings) {
                const root = originalRootNew.call(this, container, settings);

                // Use a short delay to ensure Odoo has applied the style attribute to the container
                setTimeout(() => {
                    if (root._container) {
                        const containerElement = typeof root._container === "string" ? document.getElementById(root._container) : root._container;
                        if (containerElement) {
                            const computedStyle = window.getComputedStyle(containerElement);
                            const fontFamily = computedStyle.fontFamily;
                            const fontWeight = computedStyle.fontWeight;
                            const fontStyle = computedStyle.fontStyle;
                            // Check if it's not the default browser font to avoid overriding intended amCharts defaults unnecessarily
                            if (fontFamily && fontFamily !== 'serif' && fontFamily !== 'sans-serif') {
                                root.set("fontFamily", fontFamily);
                            }
                            // Apply font weight and style from dashboard configuration
                            if (fontWeight && fontWeight !== 'normal' && fontWeight !== '400') {
                                root.set("fontWeight", fontWeight);
                            }
                            if (fontStyle && fontStyle !== 'normal') {
                                root.set("fontStyle", fontStyle);
                            }
                        }
                    }
                }, 0);

                return root;
            };
            window.am5._root_font_patched = true;
        }
    }

    applyPatch();

    if (!window.am5) {
        const interval = setInterval(() => {
            if (window.am5) {
                applyPatch();
                clearInterval(interval);
            }
        }, 500);
        setTimeout(() => clearInterval(interval), 10000);
    }
})();
