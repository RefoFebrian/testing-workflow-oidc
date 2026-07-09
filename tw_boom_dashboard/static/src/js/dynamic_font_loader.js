/** @odoo-module **/

import { registry } from "@web/core/registry";

/**
 * Dynamic Font Loader Service
 * Fetches all dashboard fonts with Google Fonts URLs and injects them into the page
 * Also provides a method to reload fonts on-demand
 */
export const dynamicFontLoaderService = {
    dependencies: ["orm"],

    async start(env, { orm }) {
        const service = {
            loadFonts: () => loadGoogleFonts(orm),
        };

        // Load fonts on startup
        await service.loadFonts();

        return service;
    },
};

async function loadGoogleFonts(orm) {
    try {
        // Fetch all fonts that have a Google Fonts URL
        const fonts = await orm.searchRead(
            "tw.dashboard.font",
            [["google_fonts_url", "!=", false]],
            ["google_fonts_url"]
        );

        // Inject each font URL as a <link> tag in the document head
        fonts.forEach(font => {
            if (font.google_fonts_url && !isFontLoaded(font.google_fonts_url)) {
                injectFontLink(font.google_fonts_url);
            }
        });

        console.log(`Loaded ${fonts.length} custom fonts`);
    } catch (error) {
        console.warn("Failed to load dynamic fonts:", error);
    }
}

function isFontLoaded(url) {
    // Check if this URL is already loaded to avoid duplicates
    const links = document.querySelectorAll('link[rel="stylesheet"]');
    return Array.from(links).some(link => link.href === url || link.href.includes(url));
}

function injectFontLink(url) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = url;
    document.head.appendChild(link);
    console.log(`Injected font: ${url}`);
}

// Register as a service that runs on app start
registry.category("services").add("dynamicFontLoader", dynamicFontLoaderService);
