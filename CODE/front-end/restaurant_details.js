$(document).ready(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const businessId = urlParams.get('id');

    d3.json(`http://localhost:8080/businesses/${businessId}`).then((restaurantData) => {

        // Restaurant Information
        const restaurantInfoContainer = d3.select("#restaurant-info");

        restaurantInfoContainer.select(".restaurant-name").text(restaurantData["name"]);

        const fullAddress = `${restaurantData.address}, ${restaurantData.city}, ${restaurantData.state} ${restaurantData.postal_code}`;

        const addressLink = `<a href="https://www.google.com/maps?q=${encodeURIComponent(fullAddress)}" target="_blank"><i class="fas fa-map-marker-alt"></i> Get Directions</a>`;

        restaurantInfoContainer.select(".restaurant-address").html(`${fullAddress} <div> ${addressLink}</div> <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css" integrity="sha512-v2/mOX4uN7V4WdPVuLZbJ9m6eC8s2sTpwGmTJU97a6U1f6UW1gHHZq9cqkKmfBLclS35fVPhrqwRQuQ7VvCjKg==" crossorigin="anonymous" referrerpolicy="no-referrer" />`);

        // Restaurant Categories
        const categoriesContainer = d3.select("#restaurant-categories");

        categoriesContainer.select(".restaurant-categories")
            .text(restaurantData["categories"].join(", "));

        // Restaurant Attributes
        //const attributesContainer = d3.select("#restaurant-attributes");

        // Move RestaurantsPriceRange2 to its own section
        const priceRangeContainer = d3.select("#restaurant-price-range");
        const priceRange = parseInt(restaurantData["attributes"]["RestaurantsPriceRange2"]);
        const dollarSigns = "<span class='price-range-dollar'>" + "$".repeat(priceRange) + "</span>";
        priceRangeContainer.select(".restaurant-price-range").html("Price Range: " + dollarSigns);

        // Display other attributes
        const attributesContainer = d3.select("#restaurant-attributes");

        const attributesBox = attributesContainer.append("div").attr("class", "restaurant-box");

        const attributes = Object.entries(restaurantData["attributes"]);
        console.log(attributes)

        const attributesList = attributesBox.append("ul").attr("class", "list-group");

        // Initialize arrays for each attribute type
        let greenAttributes = [];
        let redAttributes = [];
        let nonBooleanAttributes = [];

        attributes.forEach(([key, value]) => {
            // Exclude Price Range, Business Parking, and Good For attributes

            if (!attributeMapping[key]) {
                return;
            }

            console.log(attributeMapping[key])
            const iconClass = attributeIcons[attributeMapping[key]] || "";

            if (typeof value === "object") {
                Object.entries(value).forEach(([nestedKey, nestedValue]) => {
                    // Add "Yes" for true value and "No" for false value
                    if (nestedValue === "True") {
                        greenAttributes.push({
                            name: `${attributeMapping[key]}: ${attributeMapping[nestedKey]}`,
                            value: "Yes",
                            iconClass
                        });
                    } else if (nestedValue === "False") {
                        redAttributes.push({
                            name: `${attributeMapping[key]}: ${attributeMapping[nestedKey]}`,
                            value: "No",
                            iconClass
                        });
                    }
                });
            } else {
                if (key === "RestaurantsAttire" || key === "WiFi" || key === "NoiseLevel") {
                    value = value.replace(/u'/g, "");
                    value = value.replace(/'/g, "");
                    value = value.charAt(0).toUpperCase() + value.slice(1);
                }

                // Add "Yes" for true value and "No" for false value
                if (value === "True") {
                    greenAttributes.push({name: attributeMapping[key], value: "Yes", iconClass});
                } else if (value === "False") {
                    redAttributes.push({name: attributeMapping[key], value: "No", iconClass});
                } else {
                    nonBooleanAttributes.push({name: `${attributeMapping[key]}: ${value}`, iconClass});
                }
            }
        });

        // Sort each attribute type alphabetically
        greenAttributes.sort();
        redAttributes.sort();
        nonBooleanAttributes.sort();

        // Display attributes in the HTML element
        greenAttributes.forEach(attr => {
            const listItem = attributesList.append("li").attr("class", "list-group-item d-flex justify-content-between align-items-center");
            const icon = listItem.append("span").attr("class", `attribute-icon ${attr.iconClass}`);
            listItem.append("span").text(attr.name);
            const badge = listItem.append("span").attr("class", "badge bg-success rounded-pill");
            badge.text(attr.value);
        });

        redAttributes.forEach(attr => {
            const listItem = attributesList.append("li").attr("class", "list-group-item d-flex justify-content-between align-items-center");
            const icon = listItem.append("span").attr("class", `attribute-icon ${attr.iconClass}`);
            listItem.append("span").text(attr.name);
            const badge = listItem.append("span").attr("class", "badge bg-danger rounded-pill");
            badge.text(attr.value);
        });

        nonBooleanAttributes.forEach(attr => {
            const listItem = attributesList.append("li").attr("class", "list-group-item d-flex justify-content-between align-items-center");
            const icon = listItem.append("span").attr("class", `attribute-icon ${attr.iconClass}`);
            listItem.append("span").text(attr.name);
        });

        // Restaurant Hours
        const restaurantHoursContainer = d3.select("#restaurant-hours");

        const hoursBox = restaurantHoursContainer.append("div").attr("class", "hours-box");

        const hoursContainer = hoursBox.append("div").attr("class", "hours-container");

        // Convert hours to 12-hour format
        const hours12 = {};
        Object.entries(restaurantData["hours"]).forEach(([key, value]) => {
            if (value === "Closed") {
                hours12[key] = value;
            } else {
                const [start, end] = value.split("-");
                const start12 = formatTime(start);
                const end12 = formatTime(end);
                hours12[key] = `${start12}-${end12}`;
            }
        });

        // Populate hours of operation
        const weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
        weekdays.forEach((weekday) => {
            const hoursText = hours12[weekday] || "Closed";
            const listItem = hoursContainer.append("div").attr("class", "row");

            const dayCol = listItem.append("div").attr("class", "col-4 col-md-3 pl-4 pr-0 text-left mb-2");
            dayCol.append("i").attr("class", "fas fa-clock mr-2");
            dayCol.append("span").text(weekday);

            const hoursCol = listItem.append("div").attr("class", "col-8 col-md-9  pl-0 pr-4 text-right mb-2");
            hoursCol.append("span").text(hoursText);
        });

        const restaurantPhotosUrl = `http://localhost:8080/businesses/${businessId}/photos`;

        fetch(restaurantPhotosUrl)
            .then(response => response.json())
            .then(data => {
                const photosContainer = document.getElementById('restaurant-photos-container');
                const photos = data.photos;

                photos.forEach(photo => {
                    const photoUrl = `http://localhost:8080${photo.url}`;
                    const imgElement = document.createElement('img');
                    imgElement.src = photoUrl;
                    imgElement.alt = photo.label;
                    photosContainer.appendChild(imgElement);
                });
            })
            .catch(error => console.error('Error fetching photos:', error));

        const restaurantReviewsContainer = d3.select("#restaurant-reviews");

        const ratingContainer = restaurantReviewsContainer.select(".restaurant-rating");
        const rating = parseFloat(restaurantData["stars"]);
        const fullStars = Math.floor(rating);
        const decimal = rating - fullStars;
        const halfStar = decimal >= 0.5;

        // Add a new span element with the text "Rating: " before the star icons
        for (let i = 0; i < fullStars; i++) {
            ratingContainer.append("i").attr("class", "fas fa-star yelp-star-red");
        }

        if (halfStar) {
            ratingContainer.append("i").attr("class", "fas fa-star-half-alt yelp-star-red");
        }

        for (let i = 0; i < 5 - Math.ceil(rating); i++) {
            ratingContainer.append("i").attr("class", "far fa-star yelp-star-red");
        }

        // Add a space character and a span element to display the rating number after the star icons
        ratingContainer.append("span").text(" (");
        ratingContainer.append("span").attr("class", "rating-number").text(rating);
        ratingContainer.append("span").text(" stars)");
        restaurantReviewsContainer.select(".restaurant-review-count").text(`Review Count: ${restaurantData["review_count"]}`);

        //restaurantReviewsContainer.select(".restaurant-relevance-score").text(`Relevance Score: ${restaurantData["relevance_score"]}`);
    });
});

function formatTime(time) {
    let [hour, minute] = time.split(":");
    let suffix = hour >= 12 ? "PM" : "AM";
    hour = hour % 12 || 12;
    minute = minute.padStart(2, "0"); // add leading zero to minute
    return `${hour}:${minute}${suffix}`;
}

const attributeMapping = {
    "BusinessAcceptsCreditCards": "Accepts Credit Cards",
    "Caters": "Caters",
    "DogsAllowed": "Dog-Friendly",
    "GoodForKids": "Kid-Friendly",
    "OutdoorSeating": "Outdoor Seating",
    "RestaurantsDelivery": "Delivery",
    "RestaurantsGoodForGroups": "Good for Groups",
    "RestaurantsReservations": "Reservations",
    "RestaurantsTableService": "Table Service",
    "RestaurantsTakeOut": "Takeout",
    "WheelchairAccessible": "Wheelchair Accessible",
    "ByAppointmentOnly": "By Appointment Only",
    "HappyHour": "Happy Hour",
    "HasTV": "Has TV",
    "NoiseLevel": "Noise Level",
    "RestaurantsAttire": "Attire",
    "WiFi": "WiFi"
};

const attributeIcons = {
    "Accepts Credit Cards": "far fa-credit-card",
    "Caters": "fas fa-utensils",
    "Dog-Friendly": "fas fa-dog",
    "Kid-Friendly": "fas fa-child",
    "Outdoor Seating": "fas fa-chair",
    "Delivery": "fas fa-truck",
    "Good for Groups": "fas fa-users",
    "Reservations": "fas fa-calendar-check",
    "Table Service": "fas fa-utensils",
    "Takeout": "fas fa-box",
    "Wheelchair Accessible": "fas fa-wheelchair",
    "By Appointment Only": "fas fa-clock",
    "Happy Hour": "fas fa-cocktail",
    "Has TV": "fas fa-tv",
    "Noise Level": "fas fa-volume-up",
    "Attire": "fas fa-tshirt",
    "WiFi": "fas fa-wifi"
};
