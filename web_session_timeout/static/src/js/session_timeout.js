/** @odoo-module **/

import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { session } from "@web/session";

export const sessionTimeoutService = {
    start(env) {
        // Events that define "activity"
        // const events = ['keydown', 'wheel', 'touchmove', 'touchstart', 'click', 'scroll', 'resize'];
        const events = ['keydown', 'touchmove', 'touchstart', 'click'];
        const debug_mode = false;
        // Default timeout: 2 hours (7200 seconds)
        // We expect 'session_idle_timeout_seconds' to be injected into session info
        const TIMEOUT_MS = (session.session_idle_timeout_seconds || 7200) * 1000;
        let CHECK_INTERVAL_MS = 60 * 1000; // Check every 60 seconds
        if (debug_mode){
            CHECK_INTERVAL_MS = 60; // Check every 0.6 seconds for testing only
        }
        
        // Throttle writing to localStorage to avoid performance issues
        let lastWriteTime = 0;
        const WRITE_THROTTLE_MS = 30 * 1000; // Check every 30 seconds

        const updateActivity = (ev) => {
            const now = Date.now();
            if (now - lastWriteTime > WRITE_THROTTLE_MS) {
                if (debug_mode){
                    console.log(`[SessionTimeout] Writing to storage: ${ev?.type || 'manual'} at ${new Date(now).toLocaleTimeString()}`);
                }
                browser.localStorage.setItem('session_last_active', now.toString());
                lastWriteTime = now;
            }
        };

        let checkIntervalId = null;

        const checkInactivity = () => {
            const rawLastActive = browser.localStorage.getItem('session_last_active');
            const lastActive = parseInt(rawLastActive || Date.now());
            const now = Date.now();
            const diff = now - lastActive;
            
            if (debug_mode){
                console.log(`[SessionTimeout] Check: Now=${new Date(now).toLocaleTimeString()}, Last=${new Date(lastActive).toLocaleTimeString()}, Diff=${(diff/1000).toFixed(1)}s, Limit=${TIMEOUT_MS/1000}s`);
            }

            if (diff > TIMEOUT_MS) {
                // Double check: verify one last time effectively from storage to prevent race conditions
                const freshLastActive = parseInt(browser.localStorage.getItem('session_last_active') || Date.now());
                if (Date.now() - freshLastActive > TIMEOUT_MS) {
                    // Check if another tab is already handling the logout
                    if (!browser.localStorage.getItem('session_logout_pending')) {
                        // We are the first! Set the flag and redirect.
                        browser.localStorage.setItem('session_logout_pending', '1');
                        if (debug_mode){
                            console.log("[SessionTimeout] Timeout reached. Clearing session and redirecting.");
                        }
                        
                        // Stop the interval to prevent repeated checks
                        if (checkIntervalId) {
                            browser.clearInterval(checkIntervalId);
                        }
                        
                        // Clear the session storage to force a clean state
                        browser.localStorage.removeItem('session_last_active');
                        
                        // Force redirect using window.location.replace (more reliable than href)
                        try {
                            session.expiration_date = new Date().toISOString();
                            if (debug_mode){
                                console.log("[SessionTimeout] Executing redirect to /web/session/logout");
                            }
                            window.location.replace('/web/session/logout');
                        } catch (e) {
                            if (debug_mode){
                                console.log("[SessionTimeout] Timeout reached. Initiating logout.");
                            }
                            browser.location.href = '/web/session/logout';
                        }
                    } else {
                        // Another tab is handling logout. Just redirect to web.
                        if (debug_mode){
                            console.log("[SessionTimeout] Timeout reached but logout pending. Redirecting.");
                        }
                        
                        // Stop the interval
                        if (checkIntervalId) {
                            browser.clearInterval(checkIntervalId);
                        }
                        
                        try {
                            window.location.replace('/web');
                        } catch (e) {
                            window.location.href = '/web';
                        }
                    }
                } else {
                     console.log("[SessionTimeout] Timeout averted by fresh usage in another tab.");
                }
            } else {
                 // Clear the pending flag if we are valid (session is active again)
                 if (browser.localStorage.getItem('session_logout_pending')) {
                      browser.localStorage.removeItem('session_logout_pending');
                 }
            }
        };

        // Attach listeners
        for (const event of events) {
            browser.addEventListener(event, updateActivity, { passive: true });
        }
        
        // Also update immediately on focus/visibility change
        browser.addEventListener('focus', updateActivity);
        browser.addEventListener('visibilitychange', () => {
            if (!document.hidden) updateActivity();
        });

        // Initialize timestamp if missing
        if (!browser.localStorage.getItem('session_last_active')) {
            updateActivity();
        }

        // Start periodic check
        checkIntervalId = browser.setInterval(checkInactivity, CHECK_INTERVAL_MS);
    },
};

registry.category("services").add("session_timeout", sessionTimeoutService);
