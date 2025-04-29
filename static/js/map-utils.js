/**
 * Map Utilities for the Logistics CRM
 * This file contains functions for working with maps, routes, and geolocation
 */

// Map instances stored by container ID to avoid reinitializing
const mapInstances = {};

/**
 * Initialize a Leaflet map in the specified container
 * @param {string} containerId - ID of the HTML element to contain the map
 * @param {object} options - Map initialization options
 * @returns {object} The map instance
 */
function initMap(containerId, options = {}) {
    // Default options
    const defaultOptions = {
        center: [51.505, -0.09], // Default center (London)
        zoom: 13,            // Default zoom level
        maxZoom: 19,         // Maximum zoom level
        minZoom: 3          // Minimum zoom level
    };

    // Merge options with defaults
    const mapOptions = { ...defaultOptions, ...options };

    // Check if map already exists for this container
    if (mapInstances[containerId]) {
        // If exists, reset view to new center and zoom
        mapInstances[containerId].setView(
            mapOptions.center,
            mapOptions.zoom
        );
        return mapInstances[containerId];
    }

    // Create a new map instance
    const map = L.map(containerId, {
        center: mapOptions.center,
        zoom: mapOptions.zoom,
        maxZoom: mapOptions.maxZoom,
        minZoom: mapOptions.minZoom
    });

    // Add OpenStreetMap tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // Store map instance for future reference
    mapInstances[containerId] = map;

    return map;
}

/**
 * Extract coordinates from a Google Maps URL
 * @param {string} url - Google Maps URL
 * @returns {object|null} Object with lat and lng properties or null if invalid
 */
function extractCoordinatesFromGoogleMapsUrl(url) {
    try {
        // Handle different URL formats

        // Format 1: https://maps.app.goo.gl/JSibkzBSQSouqJBM6
        if (url.includes('maps.app.goo.gl')) {
            // For short URLs, we can't extract directly - need to make an API request
            // This would require server-side processing or using a redirect service
            console.log('Short Google Maps URL detected. Coordinates cannot be extracted directly.');
            return null;
        }

        // Format 2: https://www.google.com/maps?q=51.507,-0.127
        if (url.includes('google.com/maps?q=')) {
            const match = url.match(/q=(-?\d+\.\d+),(-?\d+\.\d+)/);
            if (match) {
                return {
                    lat: parseFloat(match[1]),
                    lng: parseFloat(match[2])
                };
            }
        }

        // Format 3: https://www.google.com/maps/@51.507,-0.127,15z
        if (url.includes('google.com/maps/@')) {
            const match = url.match(/@(-?\d+\.\d+),(-?\d+\.\d+)/);
            if (match) {
                return {
                    lat: parseFloat(match[1]),
                    lng: parseFloat(match[2])
                };
            }
        }

        // Format 4: https://www.google.com/maps/place/.../@51.507,-0.127,15z/...
        if (url.includes('google.com/maps/place/')) {
            const match = url.match(/@(-?\d+\.\d+),(-?\d+\.\d+)/);
            if (match) {
                return {
                    lat: parseFloat(match[1]),
                    lng: parseFloat(match[2])
                };
            }
        }

        // Handle more URL formats if needed

        console.log('Coordinates not found in Google Maps URL');
        return null;
    } catch (error) {
        console.error('Error extracting coordinates:', error);
        return null;
    }
}

/**
 * Add a marker to the map
 * @param {object} map - Leaflet map instance
 * @param {number} lat - Latitude
 * @param {number} lng - Longitude
 * @param {object} options - Marker options
 * @returns {object} The marker instance
 */
function addMarker(map, lat, lng, options = {}) {
    // Default marker options
    const defaultOptions = {
        draggable: false,
        title: '',
        icon: null,
        popupContent: null
    };

    // Merge options
    const markerOptions = { ...defaultOptions, ...options };

    // Create marker
    const marker = L.marker([lat, lng], {
        draggable: markerOptions.draggable,
        title: markerOptions.title,
        icon: markerOptions.icon || L.Icon.Default()
    }).addTo(map);

    // Add popup if content provided
    if (markerOptions.popupContent) {
        marker.bindPopup(markerOptions.popupContent);
    }

    return marker;
}

/**
 * Create a route between two points
 * @param {object} map - Leaflet map instance
 * @param {Array} startPoint - [lat, lng] of start point
 * @param {Array} endPoint - [lat, lng] of end point
 * @param {Array} waypoints - Array of [lat, lng] waypoints
 * @param {object} options - Route options
 * @returns {object} The polyline instance
 */
function createRoute(map, startPoint, endPoint, waypoints = [], options = {}) {
    // Default route options
    const defaultOptions = {
        color: '#0d6efd',
        weight: 5,
        opacity: 0.7
    };

    // Merge options
    const routeOptions = { ...defaultOptions, ...options };

    // Create points array including start, waypoints, and end
    const routePoints = [startPoint, ...waypoints, endPoint];

    // Create polyline
    const route = L.polyline(routePoints, routeOptions).addTo(map);

    // Fit map to route bounds
    map.fitBounds(route.getBounds(), { padding: [50, 50] });

    return route;
}

/**
 * Calculate distance between two points (haversine formula)
 * @param {Array} point1 - [lat1, lng1]
 * @param {Array} point2 - [lat2, lng2]
 * @returns {number} Distance in kilometers
 */
function calculateDistance(point1, point2) {
    const [lat1, lon1] = point1;
    const [lat2, lon2] = point2;

    const R = 6371; // Radius of the earth in km
    const dLat = deg2rad(lat2 - lat1);
    const dLon = deg2rad(lon2 - lon1);

    const a =
        Math.sin(dLat/2) * Math.sin(dLat/2) +
        Math.cos(deg2rad(lat1)) * Math.cos(deg2rad(lat2)) *
        Math.sin(dLon/2) * Math.sin(dLon/2);

    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    const distance = R * c; // Distance in km

    return distance;
}

/**
 * Convert degrees to radians
 * @param {number} deg - Degrees
 * @returns {number} Radians
 */
function deg2rad(deg) {
    return deg * (Math.PI/180);
}

/**
 * Estimate travel time based on distance
 * @param {number} distance - Distance in kilometers
 * @param {number} avgSpeed - Average speed in km/h (default: 50)
 * @returns {number} Estimated travel time in minutes
 */
function estimateTravelTime(distance, avgSpeed = 50) {
    const timeHours = distance / avgSpeed;
    return Math.round(timeHours * 60); // Convert to minutes
}

/**
 * Calculate total distance of a route
 * @param {Array} points - Array of [lat, lng] points including start, waypoints, and end
 * @returns {number} Total distance in kilometers
 */
function calculateTotalDistance(points) {
    let totalDistance = 0;

    for (let i = 0; i < points.length - 1; i++) {
        totalDistance += calculateDistance(points[i], points[i+1]);
    }

    return totalDistance;
}

/**
 * Generate waypoints between two points
 * @param {Array} startPoint - [lat, lng] of start point
 * @param {Array} endPoint - [lat, lng] of end point
 * @param {number} count - Number of waypoints to generate
 * @param {number} randomness - Factor of randomness (0-1), 0 means straight line
 * @returns {Array} Array of waypoint coordinates [lat, lng]
 */
function generateWaypoints(startPoint, endPoint, count = 3, randomness = 0.2) {
    const waypoints = [];

    // If no points to generate, return empty array
    if (count <= 0) {
        return waypoints;
    }

    // Calculate distance between points to determine scale of randomness
    const distance = calculateDistance(startPoint, endPoint);
    // Maximum deviation from straight line (in km)
    const maxDeviation = distance * randomness;

    for (let i = 1; i <= count; i++) {
        // Calculate position along straight line
        const fraction = i / (count + 1);
        const lat = startPoint[0] + fraction * (endPoint[0] - startPoint[0]);
        const lng = startPoint[1] + fraction * (endPoint[1] - startPoint[1]);

        // Add random deviation (perpendicular to the route)
        // First get direction vector
        const dx = endPoint[0] - startPoint[0];
        const dy = endPoint[1] - startPoint[1];

        // Calculate perpendicular vector
        const length = Math.sqrt(dx*dx + dy*dy);
        const perpX = -dy / length;
        const perpY = dx / length;

        // Generate random deviation
        const deviation = (Math.random() * 2 - 1) * maxDeviation;

        // Convert deviation to coordinate offsets (approximation)
        // 111.32 km = 1 degree latitude
        // 111.32 * cos(latitude) km = 1 degree longitude
        const latOffset = (deviation * perpX) / 111.32;
        const lngOffset = (deviation * perpY) / (111.32 * Math.cos(lat * Math.PI / 180));

        waypoints.push([lat + latOffset, lng + lngOffset]);
    }

    return waypoints;
}

/**
 * Geocode an address using Nominatim (OpenStreetMap)
 * @param {string} address - Address to geocode
 * @returns {Promise} Promise that resolves to coordinates {lat, lng} or null
 */
function geocodeAddress(address) {
    return new Promise((resolve, reject) => {
        const encodedAddress = encodeURIComponent(address);

        // Use OpenStreetMap's Nominatim for geocoding
        fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodedAddress}&limit=1`)
            .then(response => response.json())
            .then(data => {
                if (data && data.length > 0) {
                    resolve({
                        lat: parseFloat(data[0].lat),
                        lng: parseFloat(data[0].lon)
                    });
                } else {
                    console.log('No results found for address', address);
                    resolve(null);
                }
            })
            .catch(error => {
                console.error('Geocoding error:', error);
                reject(error);
            });
    });
}

/**
 * Initialize a route creation map with start and end markers that can be dragged
 * @param {string} containerId - Map container element ID
 * @param {function} onStartChange - Callback for start point changes
 * @param {function} onEndChange - Callback for end point changes
 * @param {function} onRouteChange - Callback for route changes (with distance and time)
 * @param {number} waypointCount - Number of waypoints to generate automatically
 * @returns {object} Object with map and control functions
 */
function initRouteCreationMap(containerId, onStartChange, onEndChange, onRouteChange, waypointCount = 3) {
    // Initialize map
    const map = initMap(containerId);

    // Create markers with default positions
    const startMarker = addMarker(map, map.getCenter().lat, map.getCenter().lng - 0.01, {
        draggable: true,
        title: 'Start Point',
        popupContent: 'Drag to set start point',
        icon: L.divIcon({
            className: 'custom-div-icon',
            html: '<div style="background-color: #dc3545; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white;"></div>',
            iconSize: [20, 20],
            iconAnchor: [10, 10]
        })
    });

    const endMarker = addMarker(map, map.getCenter().lat, map.getCenter().lng + 0.01, {
        draggable: true,
        title: 'End Point',
        popupContent: 'Drag to set end point',
        icon: L.divIcon({
            className: 'custom-div-icon',
            html: '<div style="background-color: #198754; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white;"></div>',
            iconSize: [20, 20],
            iconAnchor: [10, 10]
        })
    });

    // Track waypoint markers
    let waypointMarkers = [];

    // Initialize route
    let route = createRoute(
        map,
        [startMarker.getLatLng().lat, startMarker.getLatLng().lng],
        [endMarker.getLatLng().lat, endMarker.getLatLng().lng]
    );

    // Update route when markers are moved
    function updateRoute() {
        const startPoint = [startMarker.getLatLng().lat, startMarker.getLatLng().lng];
        const endPoint = [endMarker.getLatLng().lat, endMarker.getLatLng().lng];

        // Remove old route and waypoint markers
        map.removeLayer(route);
        waypointMarkers.forEach(marker => map.removeLayer(marker));
        waypointMarkers = [];

        // Generate waypoints
        const generatedWaypoints = generateWaypoints(startPoint, endPoint, waypointCount);

        // Create waypoint markers
        generatedWaypoints.forEach((waypoint, index) => {
            const waypointMarker = addMarker(map, waypoint[0], waypoint[1], {
                draggable: false,
                title: `Waypoint ${index + 1}`,
                popupContent: `Waypoint ${index + 1}`,
                icon: L.divIcon({
                    className: 'custom-div-icon',
                    html: '<div style="background-color: #0d6efd; width: 16px; height: 16px; border-radius: 50%; border: 2px solid white;"></div>',
                    iconSize: [16, 16],
                    iconAnchor: [8, 8]
                })
            });
            waypointMarkers.push(waypointMarker);
        });

        // Create new route with waypoints
        route = createRoute(map, startPoint, endPoint, generatedWaypoints);

        // Calculate distance and time
        const routePoints = [startPoint, ...generatedWaypoints, endPoint];
        const distance = calculateTotalDistance(routePoints);
        const time = estimateTravelTime(distance);

        // Transform waypoints to JSON structure for form
        const waypointsData = generatedWaypoints.map((point, index) => {
            return {
                location: `Waypoint ${index + 1}`,
                lat: point[0],
                lng: point[1],
                type: 'stop',
                completed: false
            };
        });

        // Call callback with route details
        if (typeof onRouteChange === 'function') {
            onRouteChange({
                startPoint: startPoint,
                endPoint: endPoint,
                waypoints: generatedWaypoints,
                waypointsData: waypointsData,
                distance: distance.toFixed(2),
                time: time
            });
        }
    }

    // Event handlers for marker drag events
    startMarker.on('dragend', function(event) {
        updateRoute();

        if (typeof onStartChange === 'function') {
            const latlng = startMarker.getLatLng();
            onStartChange([latlng.lat, latlng.lng]);
        }
    });

    endMarker.on('dragend', function(event) {
        updateRoute();

        if (typeof onEndChange === 'function') {
            const latlng = endMarker.getLatLng();
            onEndChange([latlng.lat, latlng.lng]);
        }
    });

    // Set points by coordinates
    function setStartPoint(lat, lng) {
        startMarker.setLatLng([lat, lng]);
        updateRoute();
    }

    function setEndPoint(lat, lng) {
        endMarker.setLatLng([lat, lng]);
        updateRoute();
    }

    // Set points by address
    function setStartByAddress(address) {
        return geocodeAddress(address).then(coords => {
            if (coords) {
                setStartPoint(coords.lat, coords.lng);
                return true;
            }
            return false;
        });
    }

    function setEndByAddress(address) {
        return geocodeAddress(address).then(coords => {
            if (coords) {
                setEndPoint(coords.lat, coords.lng);
                return true;
            }
            return false;
        });
    }

    // Set number of waypoints
    function setWaypointCount(count) {
        waypointCount = count;
        updateRoute();
    }

    // Initialize route calculation
    updateRoute();

    // Return map instance and control functions
    return {
        map,
        startMarker,
        endMarker,
        waypointMarkers,
        route,
        setStartPoint,
        setEndPoint,
        setStartByAddress,
        setEndByAddress,
        setWaypointCount,
        updateRoute
    };
}