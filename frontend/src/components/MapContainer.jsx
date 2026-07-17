import { useEffect, useRef, useCallback } from 'react';
import { useMap } from '../hooks/useMap';
import { getNearbyEvents } from '../api/client';
import { CATEGORY_COLORS } from '../utils/categories';

export default function MapContainer({ onMapClick, onEventClick, events, onEventsLoad }) {
  const containerRef = useRef(null);
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
      if (data && data.events) {
        onEventsLoad(data.events);
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
    <div
      id="yandex-map-container"
      ref={containerRef}
      className="yandex-map"
    />
  );
}
