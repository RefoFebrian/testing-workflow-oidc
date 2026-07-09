document.addEventListener('DOMContentLoaded', function() {
    var card_self_register = document.getElementById('card_self_register');
    card_self_register.style.display = 'none';
});

function searchPlatNo(event) {
    event.preventDefault(); // Cegah refresh halaman

    const plat_kendaraan = document.getElementsByName("plat_kendaraan")[0].value;
    const data = { plat_kendaraan: plat_kendaraan };
    const url = location.origin;

    console.log('>>>>>>>>>>>  Running');

    fetch(`${url}/post-search-by-no-plat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then((response) => response.json())
    .then((data) => {
        console.log('Fetched data:', data);
        // Handle multiple response formats:
        // JSON-RPC: {result: [200, data]} or {result: data}
        // Raw: [200, data] or data object
        if (data && data.result) {
            data = Array.isArray(data.result) ? data.result[1] : data.result;
        } else if (Array.isArray(data)) {
            data = data[1];
        }
       
        var message_error =  data['error'];
        var status = data['status'];
        var branch_name = data['branch_name'];
        var branch_code = data['branch_code'];
        var no_booking_service = data['no_booking_service'];
        var chassis_no = data['chassis_no'];
        var engine_no = data['engine_no'];
        var product = data['product'];
        var keluhan = data['keluhan'];
        var km = data['km'];
        var name_customer = data['name_customer'];
        var paket_service = data['paket_service'];
        var no_self_register = data['no_self_register'];
        var self_register_status = data['self_register_status'];
        
        // Privacy Policy data from search response
        var pp_content = data['privacy_policy_content'] || false;
        var pp_id = data['privacy_policy_id'] || false;
        
        document.getElementsByName("bg_illustrasi")[0].style.padding = '20%'

        if (message_error != 'False') {
            document.getElementsByName("bg_illustrasi")[0].style.padding = '5%'
            document.getElementById("card_self_register").style.display = 'none';
            document.getElementById("image_modal_footer").src = '/website_self_register/static/img/illustrasi_gagal.png';
            document.getElementById("title_modal").innerHTML = 'Mohon Maaf';
            document.getElementById("content_modal").innerHTML = message_error;
            document.getElementById("registration_number").style.display = 'none';            
            document.getElementById("successModal").style.display = 'block';
            modalForm()
        }
        else if (self_register_status === 'registered' && no_self_register && no_self_register !== 'False') {
            document.getElementsByName("bg_illustrasi")[0].style.paddingTop = '5%'
            document.getElementById("card_self_register").style.display = 'none';
            document.getElementById("image_modal_footer").src = '/website_self_register/static/img/illustrasi_berhasil.png';
            document.getElementById("title_modal").innerHTML = 'Pendaftaran Ditemukan!';
            document.getElementById("content_modal").innerHTML = 'Kendaraan anda sudah terdaftar hari ini. 🚨 Simpan nomor registrasi ini, ya';
            document.getElementById("registration_number").style.display = 'block';
            document.getElementById("registrationNumber").value = no_self_register;
            document.getElementById("successModal").style.display = 'block';
            modalForm();
        }
        else {
            document.getElementsByName("bg_illustrasi")[0].style.padding = '5%'
            document.getElementById("card_self_register").style.display = 'block';

            // Set value dan readonly untuk elemen-elemen
            document.getElementById("nomor_rangka").value = chassis_no;
            document.getElementById("nomor_rangka").setAttribute('readonly', true);
            document.getElementById("nomor_mesin").value = engine_no;
            document.getElementById("nomor_mesin").setAttribute('readonly', true);
            document.getElementById("no_booking_service").value = no_booking_service;
            document.getElementById("no_booking_service").setAttribute('readonly', true);
            document.getElementById("product").value = product;
            document.getElementById("product").setAttribute('readonly', true);
            document.getElementById("km").value = km;
            document.getElementById("km").setAttribute('readonly', true);
            document.getElementById("keluhan").value = keluhan;
            document.getElementById("name_customer").value = name_customer;
            

            // Insert Paket Service Cards
            const cardsContainer = document.getElementById("paket_service_cards_container");
            const hiddenInput = document.getElementById("paket_service");
            
            if (cardsContainer) {
                cardsContainer.innerHTML = ''; // Clear existing cards
            }
            if (hiddenInput) {
                hiddenInput.value = ''; // Reset selection
            }

            // Insert Paket Service Descriptions (hidden select for compatibility)
            const selectElementDescription = document.getElementById("paket_service_description");
            if (selectElementDescription) {
                selectElementDescription.innerHTML = ''; // Clear existing options
                const option_description = document.createElement("option");
                option_description.value = '#';
                option_description.text = '-SILAHKAN PILIH-';
                selectElementDescription.appendChild(option_description);
            }
            
            if (paket_service && paket_service.length > 0) {
                paket_service.forEach(service => {
                    // Populate description select for compatibility
                    if (selectElementDescription) {
                        const option_description = document.createElement("option");
                        option_description.value = service.id;
                        option_description.text = service.description || '';
                        selectElementDescription.appendChild(option_description);
                    }

                    // Render Card UI inside Modal Container
                    if (cardsContainer) {
                        const card = document.createElement('div');
                        card.className = 'paket-card';
                        card.dataset.id = service.id;
                        card.dataset.name = service.name;
                        
                        let imageHtml = `
                            <!-- Placeholder icon -->
                            <img src="https://cdn-icons-png.flaticon.com/512/3208/3208726.png" class="placeholder" style="opacity: 0.3; filter: grayscale(100%);" alt="Service Icon" />
                        `;
                        let imageStyle = '';
                        if (service.image) {
                            // Use base64 image from API as background
                            // Clean any newlines from the base64 string which break the CSS inline style parser
                            const cleanBase64 = service.image.replace(/[\r\n\s]+/g, "");
                            imageHtml = '';
                            imageStyle = `background-image: url('data:image/jpeg;base64,${cleanBase64}'); background-size: cover; background-position: center; background-repeat: no-repeat;`;
                        }

                        const descLength = service.description ? service.description.length : 0;
                        const showReadMore = true; // Always show red arrow button

                        // Format description for better readability (add line breaks before numbers and bold labels)
                        let formattedDesc = service.description ? service.description : 'Layanan regular untuk kendaraan anda.';
                        if (service.description) {
                            formattedDesc = formattedDesc
                                .replace(/(Paket Service\s*:)/ig, '<br><strong>$1</strong><br>')
                                .replace(/(Paket Sparepart)/ig, '<br><br><strong>$1</strong><br>')
                                .replace(/\s(\d+\.\s)/g, '<br>$1'); // Add linebreak before numbers like " 1. "
                            
                            // Clean up leading breaks if any
                            formattedDesc = formattedDesc.replace(/^(<br>)+/, '');
                        }

                        card.innerHTML = `
                            <div class="paket-check">
                                <i class="fa fa-check" style="font-weight: bold; font-family: sans-serif; font-style: normal;">✓</i>
                            </div>
                            <div class="paket-card-image" style="${imageStyle}">
                                ${imageHtml}
                            </div>
                            <div class="paket-card-content">
                                <h4 class="paket-title">${service.name}</h4>
                                <div class="paket-desc-container">
                                    <p class="paket-desc" title="${service.name}">${formattedDesc}</p>
                                </div>
                                <span class="read-more" title="Lihat Detail" style="position:absolute; bottom:6px; right:6px; width:28px; height:28px; background:#e62020; color:#fff; border-radius:50%; display:flex; align-items:center; justify-content:center; cursor:pointer; font-size:14px; box-shadow:0 2px 6px rgba(230,32,32,0.3); transition:background 0.2s;"><i class="fa fa-chevron-right" style="font-family:FontAwesome; font-style:normal;"></i></span>
                            </div>
                        `;

                        // Handle Read More → open detail modal
                        const readMoreBtn = card.querySelector('.read-more');
                        if (readMoreBtn) {
                            readMoreBtn.addEventListener('click', function(e) {
                                e.stopPropagation(); // Prevent selecting the card
                                _openDetailPaketModal(service, card);
                            });
                        }

                        // Add Click Event for selection
                        card.addEventListener('click', function() {
                            // Remove active from all
                            document.querySelectorAll('.paket-card').forEach(c => c.classList.remove('active'));
                            // Add active to clicked
                            this.classList.add('active');
                            
                            // Set hidden input value
                            if (hiddenInput) {
                                hiddenInput.value = this.dataset.id;

                                // Trigger change event to run the togglePaket listener
                                hiddenInput.dispatchEvent(new Event('change'));
                            }

                            // Scroll selected card into view
                            this.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
                        });

                        cardsContainer.appendChild(card);
                    }
                });
                // Show required asterisk if any
                var labelMark = document.querySelector('#paket_service_div .s_website_form_mark');
                if (labelMark) labelMark.style.display = 'inline';
            } else {
                if (cardsContainer) {
                    cardsContainer.innerHTML = `
                        <div class="alert alert-warning w-100 mb-0 mt-2" style="font-size: 0.9rem; text-align: center; border-radius: 8px; color: #856404; background-color: #fff3cd; border-color: #ffeeba;">
                            <i class="fa fa-info-circle mr-1"></i> paket service tidak tersedia, silahkan infokan ke SA pada Ahaas yang dikunjungi 
                        </div>
                    `;
                }
                // Hide required asterisk
                var labelMark = document.querySelector('#paket_service_div .s_website_form_mark');
                if (labelMark) labelMark.style.display = 'none';
            }

            // * Dynamic Privacy Policy injection after search
            var ppSection = document.querySelector('.privacy-policy-section');
            var ppModalEl = document.getElementById('privacyPolicyModal');
            var ppIdInput = document.getElementById('privacy_policy_id');
            var submitBtn = document.querySelector('#card_self_register .btn-primary[type="submit"]');

            if (pp_content && pp_id) {
                // Show privacy policy section - create if not exists (initial load has t-if=False)
                if (!ppSection) {
                    // Create privacy policy section dynamically
                    var formRows = document.querySelector('#card_self_register .s_website_form_rows');
                    var submitDiv = document.querySelector('#card_self_register .s_website_form_submit');

                    // Hidden input for policy ID
                    var ppHiddenInput = document.createElement('input');
                    ppHiddenInput.type = 'hidden';
                    ppHiddenInput.id = 'privacy_policy_id';
                    ppHiddenInput.value = pp_id;
                    formRows.insertBefore(ppHiddenInput, submitDiv);

                    // Checkbox section
                    var ppDiv = document.createElement('div');
                    ppDiv.className = 'mb-3 col-12 privacy-policy-section';
                    ppDiv.innerHTML = '<div class="form-check">' +
                        '<input class="form-check-input" type="checkbox" id="privacy_policy_checkbox"/>' +
                        '<label class="form-check-label" for="privacy_policy_checkbox">' +
                        'Saya telah membaca dan menyetujui ' +
                        '<a href="#" id="privacy_policy_link" class="privacy-policy-link">Kebijakan Privasi</a>' +
                        '</label></div>';
                    formRows.insertBefore(ppDiv, submitDiv);

                    // Modal
                    var modalDiv = document.createElement('div');
                    modalDiv.id = 'privacyPolicyModal';
                    modalDiv.className = 'modal-privacy';
                    modalDiv.style.display = 'none';
                    modalDiv.innerHTML = '<div class="modal-privacy-content">' +
                        '<div class="modal-privacy-header"><h3>Kebijakan Privasi</h3>' +
                        '<span class="close-privacy-modal">&#215;</span></div>' +
                        '<div class="modal-privacy-body">' + pp_content + '</div>' +
                        '<div class="modal-privacy-footer">' +
                        '<button id="btn_accept_privacy" class="btn btn-primary">Saya Mengerti</button>' +
                        '</div></div>';
                    document.querySelector('#card_self_register .container').appendChild(modalDiv);

                    // Re-init privacy policy event listeners
                    _initPrivacyPolicyListeners();
                } else {
                    // Section exists, update content
                    ppSection.style.display = 'block';
                    if (ppIdInput) ppIdInput.value = pp_id;
                    if (ppModalEl) {
                        var ppBody = ppModalEl.querySelector('.modal-privacy-body');
                        if (ppBody) ppBody.innerHTML = pp_content;
                    }
                }
                // Disable submit until accepted
                if (submitBtn) {
                    var ppCb = document.getElementById('privacy_policy_checkbox');
                    if (ppCb) {
                        ppCb.checked = false;
                        ppCb.dispatchEvent(new Event('change'));
                    }
                }
            } else {
                // No privacy policy — hide section if exists, enable submit
                if (ppSection) ppSection.style.display = 'none';
                if (ppModalEl) ppModalEl.style.display = 'none';
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.style.opacity = '1';
                    submitBtn.style.cursor = 'pointer';
                }
            }
            
    }
})
    .catch((error) => {
        console.error('Error:', error);
    });

    return false;
}

function modalForm(){
    // Fungsi untuk menutup modal
    document.querySelector(".close-button").addEventListener("click", function() {
        document.getElementById("successModal").style.display = 'none';
        document.getElementsByName("bg_illustrasi")[0].style.padding = '20%'
    });
    
    // Tutup modal jika klik di luar area modal
    window.addEventListener("click", function(event) {
        const modal = document.getElementById("successModal");
        if (event.target === modal) {
            modal.style.display = 'none';
        }
        document.getElementsByName("bg_illustrasi")[0].style.padding = '20%'
    });
    
    
}

function copyToClipboard() {
    const copyText = document.getElementById("registrationNumber");
    copyText.select();
    copyText.setSelectionRange(0, 99999); // Untuk perangkat mobile
    navigator.clipboard.writeText(copyText.value).then(() => {
        alert("Nomor registrasi berhasil disalin!");
    });
}


function postSelfRegister(event) {
    event.preventDefault(); // Cegah refresh halaman

    // * Validate Privacy Policy checkbox
    var ppCheckbox = document.getElementById('privacy_policy_checkbox');
    if (ppCheckbox && !ppCheckbox.checked) {
        alert('Anda harus menyetujui Kebijakan Privasi terlebih dahulu.');
        ppCheckbox.focus();
        return false;
    }

    // * Validate Paket Service Selection (since it's a custom UI now)
    var paketServiceDiv = document.getElementById("paket_service_div");
    var paket_service_val = document.getElementById("paket_service").value;
    var hasPaketServiceCards = document.querySelectorAll('.paket-card').length > 0;
    if (paketServiceDiv && paketServiceDiv.style.display === 'block' && hasPaketServiceCards && (!paket_service_val || paket_service_val === '#')) {
        alert('Silakan pilih Paket Service terlebih dahulu.');
        paketServiceDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
        return false;
    }

    const plat_kendaraan = document.getElementsByName("plat_kendaraan")[0].value;
    var nomor_rangka = document.getElementById("nomor_rangka").value;
    var nomor_mesin = document.getElementById("nomor_mesin").value;
    var no_booking_service = document.getElementById("no_booking_service").value;
    var product = document.getElementById("product").value;
    var km = document.getElementById("km").value;
    var keluhan = document.getElementById("keluhan").value;
    var name_customer = document.getElementById("name_customer").value;
    var paket_service = document.getElementById("paket_service").value;
    var service_type = document.getElementById("service_type").value;
    var no_telp = document.getElementById("no_telp").value;
    // * Include Privacy Policy ID if exists
    var ppIdEl = document.getElementById('privacy_policy_id');
    var privacy_policy_id = ppIdEl ? ppIdEl.value : false;
    const data = { 
        nomor_rangka: nomor_rangka,
        nomor_mesin: nomor_mesin,
        no_booking_service: no_booking_service,
        product: product,
        km: km,
        keluhan: keluhan,
        paket_service: paket_service,
        name_customer: name_customer,
        service_type: service_type,
        no_telp: no_telp,
        privacy_policy_id: privacy_policy_id
    };
    const url = location.origin;

    console.log('>>>>>>>>>>>  Running');

    fetch(`${url}/post-self-register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then((response) => response.json())
    .then((data) => {
        console.log('Fetched data:', data);
        // Handle multiple response formats
        if (data && data.result) {
            data = Array.isArray(data.result) ? data.result[1] : data.result;
        } else if (Array.isArray(data)) {
            data = data[1];
        }

        var no_self_register = data['no_self_register'];
        var message_error =  data['error'];
        var message =  data['message'];

        if (message_error != 'False') {
            document.getElementsByName("bg_illustrasi")[0].style.paddingTop = '5%'
            document.getElementById("card_self_register").style.display = 'none';
            document.getElementById("image_modal_footer").src = '/website_self_register/static/img/illustrasi_gagal.png';
            document.getElementById("title_modal").innerHTML = 'Mohon Maaf';
            document.getElementById("content_modal").innerHTML = message_error;
            document.getElementById("registration_number").style.display = 'none';            
            document.getElementById("successModal").style.display = 'block';
            modalForm()
        } else {
            document.getElementById("title_modal").innerHTML = 'Yeay, pendaftaran berhasil!';
            document.getElementById("registration_number").style.display = 'block';
            document.getElementById("card_self_register").style.display = 'none';
            document.getElementById("successModal").style.display = 'block';
            document.getElementById("content_modal").innerHTML = '🚨 Simpan nomor registrasi ini, ya';
            document.getElementById("registrationNumber").value = no_self_register;
            document.getElementById("image_modal_footer").src = '/website_self_register/static/img/illustrasi_berhasil.png';
            modalForm()
        }
    })
    .catch((error) => {
        console.error('Error:', error);
    });
    return false;
}



document.addEventListener('DOMContentLoaded', function () {
    var choiceKeluhan = document.getElementById('choice_keluhan');
    var choicePaketService = document.getElementById('paket_service');
    var keluhanField = document.getElementById('keluhan_div');
    var noBookingService = document.getElementById('no_booking_service');
    var paketServiceField = document.getElementById('paket_service_div');
    var serviceType = document.getElementById('service_type_div');
    var paketServiceDescriptionField = document.getElementById('paket_service_description_div');
    var DescriptionService = document.getElementById('description_div');

    function toggleFields() {
        var serviceTypeSelect = document.getElementById('service_type');

        if (noBookingService.value !== '-') {
            serviceType.style.display = 'none';
            if (serviceTypeSelect) serviceTypeSelect.removeAttribute('required');
        }
        else {
            serviceType.style.display = 'block';
            if (serviceTypeSelect) serviceTypeSelect.setAttribute('required', '');
        }

        // Logika jika pilihan keluhan adalah YES
        if (choiceKeluhan.value === 'yes_keluhan') {
            keluhanField.value = 'Silahkan isi Keluhan'
            keluhanField.style.display = 'block'; // Tampilkan field keluhan
            paketServiceField.style.display = 'none'; // Sembunyikan field paket service
            paketServiceDescriptionField.style.display = 'none'; // Sembunyikan field paket service
            DescriptionService.style.display = 'none';
        } 
        // Logika jika pilihan keluhan adalah NO dan no_booking_service berisi "-"
        else if (choiceKeluhan.value === 'no_keluhan') {
            keluhanField.style.display = 'none'; // Sembunyikan field keluhan
            paketServiceField.style.display = 'block'; // Tampilkan field paket service
            paketServiceDescriptionField.style.display = 'none'; // Tampilkan field paket service
            DescriptionService.style.display = 'block';
            document.getElementById("km").removeAttribute('readonly');
        } 
        // Jika tidak ada kondisi yang terpenuhi, sembunyikan field keluhan dan paket service
        else {
            keluhanField.style.display = 'none';
            paketServiceField.style.display = 'none';
            paketServiceDescriptionField.style.display = 'none';
            DescriptionService.style.display = 'none';
            serviceType.style.display = 'none';
            if (serviceTypeSelect) serviceTypeSelect.removeAttribute('required');
        }
        
        
    }
    
    function togglePaket(){
        var selectElement = document.getElementById("paket_service_description");
        var PaketServiceDescription = Array.from(selectElement.options).map(option => ({
            id: option.value,
            description: option.text
        }));
        var descriptionInput = document.getElementById("description_packet_service");

        var selectedService = PaketServiceDescription.find(service => service.id == this.value);    
        if (selectedService) {
            descriptionInput.value = selectedService.description;
        } else {
            descriptionInput.value = ''; // Clear description if no valid selection
        }
        document.getElementById("description_packet_service").setAttribute('readonly', true);
    }
    // Event listener untuk dropdown keluhan
    choiceKeluhan.addEventListener('change', toggleFields);
    
    // Event listener untuk hidden input paket service (menggantikan dropdown)
    const hiddenPaketServiceInput = document.getElementById("paket_service");
    if (hiddenPaketServiceInput) {
        hiddenPaketServiceInput.addEventListener('change', togglePaket);
    }
    
    // Event listener untuk input no_booking_service
    noBookingService.addEventListener('input', toggleFields);

    // Panggil fungsi pertama kali untuk inisialisasi
    toggleFields();

    // ===== Privacy Policy Modal =====
    _initPrivacyPolicyListeners();
});


/**
 * Open the Detail Paket Service modal with full description.
 * Called when user clicks "Selengkapnya..." on a paket card.
 *
 * @param {Object} service - The service data object (id, name, description, image).
 * @param {HTMLElement} cardElement - The card DOM element to select if user clicks "Pilih Paket Ini".
 */
function _openDetailPaketModal(service, cardElement) {
    var modal = document.getElementById('detailPaketModal');
    var titleEl = document.getElementById('detail_paket_title');
    var descEl = document.getElementById('detail_paket_desc');
    var imageWrapper = document.getElementById('detail_paket_image_wrapper');
    var imageEl = document.getElementById('detail_paket_image');
    var btnPilih = document.getElementById('btn_pilih_detail_paket');

    if (!modal) return;

    // Set title
    if (titleEl) titleEl.textContent = service.name || 'Detail Paket';

    // Set image
    if (imageWrapper && imageEl) {
        if (service.image) {
            var cleanBase64 = service.image.replace(/[\r\n\s]+/g, "");
            imageEl.src = 'data:image/jpeg;base64,' + cleanBase64;
            imageWrapper.style.display = 'flex';
        } else {
            imageWrapper.style.display = 'none';
        }
    }

    // Set full description (formatted)
    if (descEl) {
        var fullDesc = service.description || 'Layanan regular untuk kendaraan anda.';
        fullDesc = fullDesc
            .replace(/(Paket Service\s*:)/ig, '<br><strong>$1</strong><br>')
            .replace(/(Paket Sparepart)/ig, '<br><br><strong>$1</strong><br>')
            .replace(/\s(\d+\.\s)/g, '<br>$1')
            .replace(/^(<br>)+/, '');
        descEl.innerHTML = fullDesc;
    }

    // Show modal
    modal.style.display = 'block';

    // "Pilih Paket Ini" button — select the card and close modal
    if (btnPilih) {
        // Clone and replace to remove old listeners
        var newBtn = btnPilih.cloneNode(true);
        btnPilih.parentNode.replaceChild(newBtn, btnPilih);

        newBtn.addEventListener('click', function() {
            cardElement.click(); // Trigger card selection
            modal.style.display = 'none';
        });
    }

    // Close button
    var closeBtn = modal.querySelector('.close-detail-modal');
    if (closeBtn) {
        closeBtn.onclick = function() { modal.style.display = 'none'; };
    }

    // Close on outside click
    modal.onclick = function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    };
}


/**
 * Initialize / re-initialize Privacy Policy event listeners.
 * Extracted as a standalone function so it can be called both on
 * DOMContentLoaded (server-rendered section) and dynamically after
 * the plate-search injects the section via JS.
 */
function _initPrivacyPolicyListeners() {
    var ppLink = document.getElementById('privacy_policy_link');
    var ppModal = document.getElementById('privacyPolicyModal');
    var ppCloseBtn = document.querySelector('.close-privacy-modal');
    var ppAcceptBtn = document.getElementById('btn_accept_privacy');
    var ppCheckbox = document.getElementById('privacy_policy_checkbox');

    if (ppLink && ppModal) {
        // Disable submit button until privacy policy is accepted
        var submitBtn = document.querySelector('#card_self_register .btn-primary[type="submit"]');
        if (submitBtn && ppCheckbox) {
            submitBtn.disabled = true;
            submitBtn.style.opacity = '0.5';
            submitBtn.style.cursor = 'not-allowed';

            ppCheckbox.addEventListener('change', function() {
                submitBtn.disabled = !ppCheckbox.checked;
                submitBtn.style.opacity = ppCheckbox.checked ? '1' : '0.5';
                submitBtn.style.cursor = ppCheckbox.checked ? 'pointer' : 'not-allowed';
            });
        }

        ppLink.addEventListener('click', function(e) {
            e.preventDefault();
            ppModal.style.display = 'block';
        });

        if (ppCloseBtn) {
            ppCloseBtn.addEventListener('click', function() {
                ppModal.style.display = 'none';
            });
        }

        if (ppAcceptBtn) {
            ppAcceptBtn.addEventListener('click', function() {
                ppModal.style.display = 'none';
                if (ppCheckbox) {
                    ppCheckbox.checked = true;
                    ppCheckbox.dispatchEvent(new Event('change'));
                }
            });
        }

        // Close modal when clicking outside
        window.addEventListener('click', function(event) {
            if (event.target === ppModal) {
                ppModal.style.display = 'none';
            }
        });
    }
}
