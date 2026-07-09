/** @odoo-module **/

import { Component, onWillStart, onMounted, useRef, useEffect } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { loadJS } from "@web/core/assets";
import { session } from "@web/session";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

export class TwMapWidget extends Component {
    static template = "tw_map_widget.MapWidget";
    static props = {
        ...standardFieldProps,
        lat_field: { type: String, optional: true },
        long_field: { type: String, optional: true },
        address_field: { type: String, optional: true },
    };

    setup() {
        this.mapContainer = useRef("mapContainer");
        this.searchInput = useRef("searchInput");
        this.notification = useService("notification");

        this.jsonField = this.props.name;
        this.latField = this.props.lat_field;
        this.longField = this.props.long_field;
        this.addressField = this.props.address_field;

        // Default settings if base_geolocalize is not configured properly in session
        this.twMapSettings = session.tw_map_widget || { provider: 'openstreetmap', google_map_api_key: '' };
        this.provider = this.twMapSettings.provider;
        this.apiKey = this.twMapSettings.google_map_api_key;

        this.map = null;
        this.marker = null;
        this.isUpdatingFromMap = false;

        onWillStart(async () => {
            if (this.provider === 'googlemap' && this.apiKey) {
                if (!window.google || !window.google.maps) {
                    await loadJS(`https://maps.googleapis.com/maps/api/js?key=${this.apiKey}&libraries=places`);
                }
            }
        });

        onMounted(() => {
            this.initMap();
        });

        useEffect(() => {
            if (!this.isUpdatingFromMap) {
                this.updateMarkerFromRecord();
            }
            this.isUpdatingFromMap = false;
        }, () => {
            const deps = [];
            if (this.latField) deps.push(this.props.record.data[this.latField]);
            if (this.longField) deps.push(this.props.record.data[this.longField]);
            return deps;
        });
    }

    getInitialCoords() {
        let lat = NaN;
        let lng = NaN;
        if (this.latField && this.longField) {
            lat = parseFloat(this.props.record.data[this.latField]);
            lng = parseFloat(this.props.record.data[this.longField]);
        }
        if (!isNaN(lat) && !isNaN(lng)) {
            return { lat, lng };
        }
        
        if (this.props.record.data[this.jsonField]) {
            try {
                let data = this.props.record.data[this.jsonField];
                if (typeof data === 'string') data = JSON.parse(data);
                if (data && data.lat && data.long) {
                    return { lat: parseFloat(data.lat), lng: parseFloat(data.long) };
                }
            } catch (e) {
                console.error("Invalid json data in map field", e);
            }
        }
        // Default to Jakarta, Indonesia
        return { lat: -6.200000, lng: 106.816666 };
    }

    initMap() {
        const coords = this.getInitialCoords();

        if (this.provider === 'googlemap' && this.apiKey && window.google) {
            this.map = new google.maps.Map(this.mapContainer.el, {
                center: coords,
                zoom: 13,
            });

            this.marker = new google.maps.Marker({
                position: coords,
                map: this.map,
                draggable: !this.props.readonly,
            });

            this.map.addListener("click", (e) => {
                if (this.props.readonly) return;
                const newPos = e.latLng;
                this.marker.setPosition(newPos);
                this.updateRecord(newPos.lat(), newPos.lng());
            });

            this.marker.addListener("dragend", (e) => {
                const newPos = e.latLng;
                this.updateRecord(newPos.lat(), newPos.lng());
            });

        } else {
            // Leaflet
            this.map = L.map(this.mapContainer.el).setView([coords.lat, coords.lng], 13);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; OpenStreetMap contributors'
            }).addTo(this.map);

            this.marker = L.marker([coords.lat, coords.lng], { draggable: !this.props.readonly }).addTo(this.map);

            this.map.on('click', (e) => {
                if (this.props.readonly) return;
                const newPos = e.latlng;
                this.marker.setLatLng(newPos);
                this.updateRecord(newPos.lat, newPos.lng);
            });

            this.marker.on('dragend', (e) => {
                const newPos = this.marker.getLatLng();
                this.updateRecord(newPos.lat, newPos.lng);
            });
        }
    }

    updateMarkerFromRecord() {
        let lat = NaN;
        let lng = NaN;
        if (this.latField && this.longField) {
            lat = parseFloat(this.props.record.data[this.latField]);
            lng = parseFloat(this.props.record.data[this.longField]);
        }

        if (isNaN(lat) || isNaN(lng) || !this.map || !this.marker) return;

        if (this.provider === 'googlemap' && this.apiKey && window.google) {
            const pos = new google.maps.LatLng(lat, lng);
            this.marker.setPosition(pos);
            this.map.panTo(pos);
        } else {
            this.marker.setLatLng([lat, lng]);
            this.map.panTo([lat, lng]);
        }
    }

    async updateRecord(lat, lng) {
        if (this.props.readonly) {
            return;
        }
        this.isUpdatingFromMap = true;
        
        const updates = {};
        const strLat = lat.toFixed(6).toString();
        const strLng = lng.toFixed(6).toString();
        
        let addressStr = "";
        
        // Reverse geocoding
        try {
            const result = await rpc("/tw_map_widget/reverse_geocode", { lat, lng });
            if (result && result.address) {
                addressStr = result.address;
                if (this.addressField) {
                    updates[this.addressField] = addressStr;
                }
            }
        } catch (e) {
            console.error("Reverse geocoding failed", e);
        }

        if (this.latField) updates[this.latField] = strLat;
        if (this.longField) updates[this.longField] = strLng;
        
        updates[this.jsonField] = JSON.stringify({
            lat: strLat,
            long: strLng,
            address: addressStr
        });

        this.props.record.update(updates);
    }

    async onSearchClick() {
        if (this.props.readonly) {
            return;
        }
        const query = this.searchInput.el.value;
        if (!query) return;

        try {
            const result = await rpc("/tw_map_widget/geocode", {
                address: query
            });

            if (result && result.lat && result.lng) {
                const { lat, lng } = result;
                if (this.provider === 'googlemap' && this.apiKey && window.google) {
                    const pos = new google.maps.LatLng(lat, lng);
                    this.marker.setPosition(pos);
                    this.map.setCenter(pos);
                    this.map.setZoom(15);
                } else {
                    this.marker.setLatLng([lat, lng]);
                    this.map.setView([lat, lng], 15);
                }
                this.updateRecord(lat, lng);
            } else {
                this.notification.add("Location not found", { type: "warning" });
            }
        } catch (error) {
            console.error("Geocoding failed", error);
            this.notification.add("Failed to search location", { type: "danger" });
        }
    }

    onSearchKeyDown(ev) {
        if (ev.key === "Enter") {
            this.onSearchClick();
            ev.preventDefault();
        }
    }
}

export const twMapWidget = {
    component: TwMapWidget,
    extractProps: ({ attrs, options }) => {
        return {
            lat_field: options.lat_field,
            long_field: options.long_field,
            address_field: options.address_field,
        };
    },
};

registry.category("fields").add("tw_map", twMapWidget);
