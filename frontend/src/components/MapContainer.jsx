import { useEffect, useRef, useCallback, useState } from 'react';
import { useMap } from '../hooks/useMap';
import { getNearbyEvents } from '../api/client';
import { CATEGORY_COLORS } from '../utils/categories';

export default function MapContainer({ onMapClick, onEventClick, events, onEventsLoad }) {
  const containerRef = useRef(null);
  const [userLocation, setUserLocation] = useState(null);
  const {
    ymaps,
    mapInstance,
    loading,
    error,
    initMap,
    setTempMarker,
    reverseGeocode,
    setEventMarkers,
  } = useMap();

  // Initialize map in the container
  useEffect(() => {
    if (!loading && !error && containerRef.current && !mapInstance) {
      initMap('yandex-map-container');
    }
  }, [loading, error, mapInstance, initMap]);

  // Request geolocation and re-center map
  useEffect(() => {
    if (!mapInstance) return;
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const coords = [pos.coords.latitude, pos.coords.longitude];
          setUserLocation(coords);
          mapInstance.setCenter(coords);
        },
        () => {}, // denied — stay on default center
        { timeout: 5000, maximumAge: 60000 }
      );
    }
  }, [mapInstance]);

  // Bind click handler to the map
  useEffect(() => {
    if (!mapInstance) return;

    const handler = async (e) => {
      const coords = e.get('coords');
      setTempMarker(coords);
      const addr = await reverseGeocode(coords);
      onMapClick(coords[0], coords[1], addr);
    };

    mapInstance.events.add('click', handler);
    return () => {
      mapInstance.events.remove('click', handler);
    };
  }, [mapInstance, setTempMarker, reverseGeocode, onMapClick]);

  // Load nearby events on map bounds change
  const loadEvents = useCallback(async () => {
    if (!mapInstance) return;
    const center = mapInstance.getCenter();
    try {
      const data = await getNearbyEvents(center[0], center[1], 50);
      if (data && data.items) {
        onEventsLoad(data.items);
      }
    } catch {
      // silently fail
    }
  }, [mapInstance, onEventsLoad]);

  // Debounced reload on map move
  useEffect(() => {
    if (!mapInstance) return;
    let timer;
    const handler = () => {
      clearTimeout(timer);
      timer = setTimeout(loadEvents, 500);
    };
    mapInstance.events.add('boundschange', handler);
    // Initial load
    loadEvents();
    return () => {
      clearTimeout(timer);
      mapInstance.events.remove('boundschange', handler);
    };
  }, [mapInstance, loadEvents]);

  // Update markers when events change
  useEffect(() => {
    if (!ymaps || !mapInstance || !events.length) return;
    setEventMarkers(events, onEventClick, CATEGORY_COLORS);
  }, [ymaps, mapInstance, events, onEventClick, setEventMarkers]);

  const handleLocateClick = () => {
    if (!mapInstance) return;
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const coords = [pos.coords.latitude, pos.coords.longitude];
          setUserLocation(coords);
          mapInstance.setCenter(coords);
        },
        () => {},
        { timeout: 5000, maximumAge: 30000 }
      );
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-100 text-gray-500">
        Загрузка карты...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-100 text-red-500">
        {error}
      </div>
    );
  }

  return (
    <div className="relative h-full w-full">
      <div
        id="yandex-map-container"
        ref={containerRef}
        className="yandex-map"
      />
      <button
        onClick={handleLocateClick}
        className="absolute bottom-6 right-6 z-10 w-10 h-10 bg-white rounded-lg shadow-md hover:shadow-lg flex items-center justify-center text-gray-700 hover:text-blue-600 transition-colors"
        title="Моё местоположение"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="3"/>
          <path d="M12 2v4"/>
          <path d="M12 18v4"/>
          <path d="M2 12h4"/>
          <path d="M18 12h4"/>
        </svg>
      </button>
    </div>
  );
}
