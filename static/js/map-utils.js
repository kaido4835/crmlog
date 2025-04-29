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
        console.log('Attempting to extract coordinates from URL:', url);

        // Check if it's a short URL
        if (url.includes('maps.app.goo.gl') || url.includes('goo.gl/maps')) {
            // For short URLs, we need to use the server-side endpoint
            console.log('Short Google Maps URL detected. Using server endpoint...');
            return processShortUrl(url);
        }

        // Format: https://www.google.com/maps?q=51.507,-0.127
        const queryParamMatch = url.match(/q=(-?\d+\.\d+),(-?\d+\.\d+)/);
        if (queryParamMatch) {
            console.log('Extracted coordinates from q= format:', queryParamMatch[1], queryParamMatch[2]);
            return {
                lat: parseFloat(queryParamMatch[1]),
                lng: parseFloat(queryParamMatch[2])
            };
        }

        // Format: https://www.google.com/maps/@51.507,-0.127,15z
        const atSymbolMatch = url.match(/@(-?\d+\.\d+),(-?\d+\.\d+)/);
        if (atSymbolMatch) {
            console.log('Extracted coordinates from @ format:', atSymbolMatch[1], atSymbolMatch[2]);
            return {
                lat: parseFloat(atSymbolMatch[1]),
                lng: parseFloat(atSymbolMatch[2])
            };
        }

        // Format: https://www.google.com/maps/search/51.507,+-0.127/
        const searchFormatMatch = url.match(/\/maps\/search\/(-?\d+\.\d+),\s*(-?\d+\.\d+)/);
        if (searchFormatMatch) {
            console.log('Extracted coordinates from search format:', searchFormatMatch[1], searchFormatMatch[2]);
            return {
                lat: parseFloat(searchFormatMatch[1]),
                lng: parseFloat(searchFormatMatch[2])
            };
        }

        // Format: https://www.google.com/maps/place/...!3d51.507!4d-0.127...
        const detailedFormatMatch = url.match(/!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)/);
        if (detailedFormatMatch) {
            console.log('Extracted coordinates from !3d!4d format:', detailedFormatMatch[1], detailedFormatMatch[2]);
            return {
                lat: parseFloat(detailedFormatMatch[1]),
                lng: parseFloat(detailedFormatMatch[2])
            };
        }

        console.log('Coordinates not found in Google Maps URL');
        return null;
    } catch (error) {
        console.error('Error extracting coordinates:', error);
        return null;
    }
}

/**
 * Process a short Google Maps URL using server-side endpoint
 * @param {string} url - Short Google Maps URL
 * @returns {Promise<object|null>} Promise resolving to coordinates or null if invalid
 */
function processShortUrl(url) {
    return new Promise((resolve, reject) => {
        fetch('/routes/process-short-url', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ url: url })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.latitude && data.longitude) {
                console.log('Server successfully processed short URL:', data);
                resolve({
                    lat: data.latitude,
                    lng: data.longitude
                });
            } else {
                console.warn('Server could not extract coordinates:', data.error || 'Unknown error');
                resolve(null);
            }
        })
        .catch(error => {
            console.error('Error processing short URL:', error);
            resolve(null);
        });
    });
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
 * Geocode an address using Nominatim (OpenStreetMap)
 * @param {string} address - Address to geocode
 * @returns {Promise} Promise that resolves to coordinates {lat, lng} or null
 */
function geocodeAddress(address) {
    return new Promise((resolve, reject) => {
        console.log('Geocoding address:', address);

        // Check if it's a Google Maps URL first
        if (address.includes('google.com/maps') || address.includes('maps.app.goo.gl') || address.includes('goo.gl/maps')) {
            const coords = extractCoordinatesFromGoogleMapsUrl(address);
            if (coords && typeof coords.then === 'function') {
                // It's a promise (for short URLs)
                coords.then(result => {
                    if (result) {
                        resolve(result);
                    } else {
                        // Fall back to Nominatim if extracting from URL failed
                        geocodeWithNominatim(address).then(resolve).catch(reject);
                    }
                });
            } else if (coords) {
                // Direct result
                resolve(coords);
            } else {
                // Fall back to Nominatim if extracting from URL failed
                geocodeWithNominatim(address).then(resolve).catch(reject);
            }
        } else {
            // Not a Google Maps URL, use Nominatim
            geocodeWithNominatim(address).then(resolve).catch(reject);
        }
    });
}

/**
 * Geocode an address using Nominatim
 * @param {string} address - Address to geocode
 * @returns {Promise} Promise that resolves to coordinates {lat, lng} or null
 */
function geocodeWithNominatim(address) {
    return new Promise((resolve, reject) => {
        const encodedAddress = encodeURIComponent(address);

        // Use OpenStreetMap's Nominatim for geocoding
        fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodedAddress}&limit=1`, {
            headers: {
                'User-Agent': 'LogisticsCRM/1.0'
            }
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Geocoding failed with status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data && data.length > 0) {
                    console.log('Geocoding result:', data[0]);
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
 * @returns {object} Object with map and control functions
 */
function initRouteCreationMap(containerId, onStartChange, onEndChange, onRouteChange) {
    console.log('Initializing route creation map');

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

    // Initialize route
    let route = createRoute(
        map,
        [startMarker.getLatLng().lat, startMarker.getLatLng().lng],
        [endMarker.getLatLng().lat, endMarker.getLatLng().lng]
    );

    // Update route when markers are moved
    function updateRoute() {
        console.log('Updating route');
        const startPoint = [startMarker.getLatLng().lat, startMarker.getLatLng().lng];
        const endPoint = [endMarker.getLatLng().lat, endMarker.getLatLng().lng];

        // Remove old route
        map.removeLayer(route);

        // Create new route
        route = createRoute(map, startPoint, endPoint);

        // Calculate distance and time
        const distance = calculateDistance(startPoint, endPoint);
        const time = estimateTravelTime(distance);

        console.log(`Route updated: ${distance.toFixed(2)} km, ${time} minutes`);

        // Call callback with route details
        if (typeof onRouteChange === 'function') {
            onRouteChange({
                startPoint: startPoint,
                endPoint: endPoint,
                distance: distance.toFixed(2),
                time: time
            });
        }
    }

    // Event handlers for marker drag events
    startMarker.on('dragend', function(event) {
        console.log('Start marker dragged');
        updateRoute();

        if (typeof onStartChange === 'function') {
            const latlng = startMarker.getLatLng();
            onStartChange([latlng.lat, latlng.lng]);
        }
    });

    endMarker.on('dragend', function(event) {
        console.log('End marker dragged');
        updateRoute();

        if (typeof onEndChange === 'function') {
            const latlng = endMarker.getLatLng();
            onEndChange([latlng.lat, latlng.lng]);
        }
    });

    // Set points by coordinates - with updateRoute call
    function setStartPoint(lat, lng) {
        console.log(`Setting start point to: ${lat}, ${lng}`);
        startMarker.setLatLng([lat, lng]);
        // Explicitly call updateRoute after setting point
        updateRoute();
    }

    function setEndPoint(lat, lng) {
        console.log(`Setting end point to: ${lat}, ${lng}`);
        endMarker.setLatLng([lat, lng]);
        // Explicitly call updateRoute after setting point
        updateRoute();
    }

    // Set points by address - with better error handling
    function setStartByAddress(address) {
        console.log('Setting start point by address:', address);
        return geocodeAddress(address)
            .then(coords => {
                if (coords) {
                    console.log(`Address resolved to coordinates: ${coords.lat}, ${coords.lng}`);
                    setStartPoint(coords.lat, coords.lng);
                    return true;
                }
                console.warn('Could not geocode address for start point');
                return false;
            })
            .catch(error => {
                console.error('Error setting start point by address:', error);
                return false;
            });
    }

    function setEndByAddress(address) {
        console.log('Setting end point by address:', address);
        return geocodeAddress(address)
            .then(coords => {
                if (coords) {
                    console.log(`Address resolved to coordinates: ${coords.lat}, ${coords.lng}`);
                    setEndPoint(coords.lat, coords.lng);
                    return true;
                }
                console.warn('Could not geocode address for end point');
                return false;
            })
            .catch(error => {
                console.error('Error setting end point by address:', error);
                return false;
            });
    }

    // Initialize route calculation
    updateRoute();

    // Return map instance and control functions
    return {
        map,
        startMarker,
        endMarker,
        route,
        setStartPoint,
        setEndPoint,
        setStartByAddress,
        setEndByAddress,
        updateRoute
    };
}