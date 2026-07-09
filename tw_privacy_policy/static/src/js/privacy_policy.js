/** @odoo-module **/

import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

/**
 * Privacy Policy Service for TETO system
 * Checks if user has accepted current privacy policy from HOKI API
 * and displays modal if not accepted.
 */

let policyCheckInProgress = false;
let policyModalShown = false;

async function checkPrivacyPolicy() {
    // Skip if already checking or modal shown
    if (policyCheckInProgress || policyModalShown) {
        return;
    }
    
    policyCheckInProgress = true;
    
    try {
        // Call controller to check policy
        const response = await rpc('/tw/check_privacy_policy', {});
        
        if (response.status === 'error') {
            console.error("[TW Privacy Policy] Error:", response.message);
            policyCheckInProgress = false;
            return;
        }
        
        if (!response.is_accepted && response.privacy_policy_id && response.privacy_policy_content) {
            // User hasn't accepted - show modal
            showPolicyModal(response);
        } else {
            policyCheckInProgress = false;
        }
        
    } catch (error) {
        console.error("[TW Privacy Policy] Failed to check policy:", error);
        policyCheckInProgress = false;
    }
}

function showPolicyModal(data) {
    if (policyModalShown) {
        return; // Prevent duplicate modal
    }
    
    policyModalShown = true;
    
    // Create modal HTML
    const modalHtml = `
        <div class="modal fade" id="twPolicyModal" tabindex="-1" role="dialog" aria-labelledby="twPolicyModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-lg" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <h4 class="modal-title" id="twPolicyModalLabel">Kebijakan Privasi</h4>
                    </div>
                    <div class="modal-body" style="max-height: 400px; overflow-y: auto;">
                        ${data.privacy_policy_content}
                    </div>
                    <div class="modal-footer">
                        <div class="form-check" style="flex: 1; text-align: left;">
                            <input type="checkbox" class="form-check-input" id="twPolicyCheckbox">
                            <label class="form-check-label" for="twPolicyCheckbox">
                                Saya telah membaca dan menyetujui kebijakan privasi.
                            </label>
                        </div>
                        <button type="button" class="btn btn-primary" id="twPolicyAcceptBtn" disabled>
                            Setuju &amp; Lanjutkan
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Append modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    const modalElement = document.getElementById('twPolicyModal');
    const checkbox = document.getElementById('twPolicyCheckbox');
    const acceptBtn = document.getElementById('twPolicyAcceptBtn');
    
    // Enable/disable accept button based on checkbox
    checkbox.addEventListener('change', function() {
        acceptBtn.disabled = !this.checked;
    });
    
    // Handle accept button click
    acceptBtn.addEventListener('click', async function() {
        acceptBtn.disabled = true;
        acceptBtn.textContent = 'Memproses...';
        
        try {
            const response = await rpc('/tw/accept_privacy_policy', {
                privacy_policy_id: data.privacy_policy_id
            });
            
            if (response.status === 'success' && response.is_accepted) {
                
                // Hide modal using vanilla JS
                modalElement.classList.remove('show');
                modalElement.style.display = 'none';
                modalElement.removeAttribute('aria-modal');
                modalElement.setAttribute('aria-hidden', 'true');
                
                // Remove backdrop
                const backdrop = document.querySelector('.modal-backdrop');
                if (backdrop) {
                    backdrop.remove();
                }
                document.body.classList.remove('modal-open');
                
                // Remove modal from DOM
                setTimeout(() => {
                    modalElement.remove();
                    policyCheckInProgress = false;
                    // Reload page to refresh session
                    window.location.reload();
                }, 300);
            } else {
                console.error("[TW Privacy Policy] Failed to accept policy:", response.message);
                alert('Gagal menyimpan persetujuan. Silakan coba lagi.');
                acceptBtn.disabled = false;
                acceptBtn.textContent = 'Setuju & Lanjutkan';
            }
        } catch (error) {
            console.error("[TW Privacy Policy] Error accepting policy:", error);
            alert('Terjadi kesalahan. Silakan coba lagi.');
            acceptBtn.disabled = false;
            acceptBtn.textContent = 'Setuju & Lanjutkan';
        }
    });
    
    // Show modal with static backdrop (cannot close without accepting)
    // Use vanilla JS since bootstrap object is not globally available in Odoo 18
    modalElement.classList.add('show');
    modalElement.style.display = 'block';
    modalElement.setAttribute('aria-modal', 'true');
    modalElement.removeAttribute('aria-hidden');
    
    // Add backdrop
    const backdrop = document.createElement('div');
    backdrop.className = 'modal-backdrop fade show';
    document.body.appendChild(backdrop);
    document.body.classList.add('modal-open');
}

// Service definition for privacy policy checker
export const privacyPolicyService = {
    dependencies: [],
    async start(env) {
        
        // Wait a bit for the web client to fully load
        setTimeout(() => {
            checkPrivacyPolicy();
        }, 1500);
        
        return {};
    },
};

// Register service
registry.category("services").add("tw_privacy_policy", privacyPolicyService);

