import { useState, useCallback, useRef, useEffect } from 'react';

/**
 * Hook для работы с Яндекс Картой.
 * Загружает API Яндекс Карт, создаёт карту, управляет маркерами.
 */
export function useMap() {
  const [ymaps, setYmaps] = useState(null);
  const [mapInstance, setMapInstance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const tempMarkerRef = useRef(null);
  const eventMarkersRef = useRef([]);

  // Load Yandex Maps API key from backend config
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch('/api/v1/config');
        const config = await res.json();
        if (cancelled) return;

        const key = config.yandex_maps_api_key;
        if (!key) {
          setError('Ключ Яндекс Карт не настроен на сервере');
          setLoading(false);
          return;
        }

        const script = document.createElement('script');
        script.src = `https://api-maps.yandex.ru/2.1/?apikey=${key}&lang=ru_RU`;
        script.onload = () => {
          if (cancelled) return;
          window.ymaps.ready(() => {
            if (cancelled) return;
            setYmaps(window.ymaps);
            setLoading(false);
          });
        };
        script.onerror = () => {
          if (cancelled) return;
          setError('Не удалось загрузить Яндекс Карты');
          setLoading(false);
        };
        document.head.appendChild(script);
      } catch {
        if (!cancelled) {
          setError('Не удалось получить конфигурацию');
          setLoading(false);
        }
      }
    })();
    return () => { cancelled = true; };
  }, []);

  // Initialize map
  const initMap = useCallback(
    (containerId, center = [55.751244, 37.618423]) => {
      if (!ymaps || mapInstance) return null;
      const map = new ymaps.Map(containerId, {
        center,
        zoom: 12,
        controls: ['zoomControl', 'typeSelector'],
      });
      setMapInstance(map);
      return map;
    },
    [ymaps, mapInstance]
  );

  // Set temporary marker on click
  const setTempMarker = useCallback(
    (coords) => {
      if (!ymaps || !mapInstance) return;
      if (tempMarkerRef.current) {
        mapInstance.geoObjects.remove(tempMarkerRef.current);
      }
      const pm = new ymaps.Placemark(coords, {}, { preset: 'islands#redDotIcon' });
      mapInstance.geoObjects.add(pm);
      tempMarkerRef.current = pm;
    },
    [ymaps, mapInstance]
  );

  // Clear temporary marker
  const clearTempMarker = useCallback(() => {
    if (tempMarkerRef.current && mapInstance) {
      mapInstance.geoObjects.remove(tempMarkerRef.current);
      tempMarkerRef.current = null;
    }
  }, [mapInstance]);

  // Replace all event markers with new ones
  const setEventMarkers = useCallback(
    (events, onEventClick, colors) => {
      if (!ymaps || !mapInstance) return;
      // Clear old markers
      eventMarkersRef.current.forEach((m) => mapInstance.geoObjects.remove(m));
      eventMarkersRef.current = [];

      events.forEach((ev) => {
        const color = (colors && colors[ev.category]) || '#6b7280';
        const pm = new ymaps.Placemark(
          [ev.latitude, ev.longitude],
          {
            hintContent: ev.title,
            balloonContentHeader: `<strong>${ev.title}</strong>`,
            balloonContentBody: ev.address || '',
          },
          {
            preset: 'islands#dotIcon',
            iconColor: color,
          }
        );
        pm.events.add('click', () => onEventClick(ev));
        mapInstance.geoObjects.add(pm);
        eventMarkersRef.current.push(pm);
      });
    },
    [ymaps, mapInstance]
  );

  // Reverse geocode
  const reverseGeocode = useCallback(
    async (coords) => {
      if (!ymaps) return '';
      try {
        const res = await ymaps.geocode(coords);
        const obj = res.geoObjects.get(0);
        if (obj) {
          return obj.getAddressLine();
        }
      } catch {
        // ignore
      }
      return '';
    },
    [ymaps]
  );

  return {
    ymaps,
    mapInstance,
    loading,
    error,
    initMap,
    setTempMarker,
    clearTempMarker,
    setEventMarkers,
    reverseGeocode,
  };
}
