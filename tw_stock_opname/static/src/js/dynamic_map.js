odoo.define('your_module_name.dynamic_map', function (require) {
    "use strict";

    $(document).ready(function () {
        // Get latitude and longitude values from input fields
        var latitude = parseFloat($('input[name="latitude"]').val());
        var longitude = parseFloat($('input[name="longtitude"]').val());

        console.log("Latitude:", latitude);
        console.log("Longitude:", longitude);

        // Check if latitude and longitude are valid numbers
        if (!isNaN(latitude) && !isNaN(longitude)) {
            // Construct the URL with dynamic latitude and longitude
            var url = 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d21245.940512027442!2d' + longitude + '!3d' + latitude + '!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMTLCsDM2JzU1LjMiTiA3N8KwMDMnMDAuMyJF!5e0!3m2!1sen!2suk!4v1648990175206!5m2!1sen!2suk';

            // Set the src attribute of the iframe
            $('#dynamic_map').attr('src', url);
        } else {
            console.error("Invalid latitude or longitude values.");
        }
    });
});
