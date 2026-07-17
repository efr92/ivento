import { useState, useCallback } from 'react';
import Header from './Header';
import MapContainer from './MapContainer';
import EventForm from './EventForm';
import EventPopup from './EventPopup';

export default function MapPage() {
  const [selectedCoords, setSelectedCoords] = useState(null); // { lat, lon, address }
  const [showForm, setShowForm] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState(null); // event for popup
  const [nearbyEvents, setNearbyEvents] = useState([]);

  const handleMapClick = useCallback((lat, lon, address) => {
    setSelectedCoords({ lat, lon, address });
    setShowForm(true);
    setSelectedEvent(null); // close popup
  }, []);

  const handleEventClick = useCallback((event) => {
    setSelectedEvent(event);
    setShowForm(false); // close form if open
  }, []);

  const handleFormClose = useCallback(() => {
    setShowForm(false);
    setSelectedCoords(null);
  }, []);

  const handleEventCreated = useCallback(
    (created) => {
      // Add the new event to the list so marker appears immediately
      setNearbyEvents((prev) => [...prev, created]);
    },
    []
  );

  const handleEventsLoad = useCallback((events) => {
    setNearbyEvents(events);
  }, []);

  const handlePopupClose = useCallback(() => {
    setSelectedEvent(null);
  }, []);

  return (
    <div className="h-screen w-screen relative">
      <Header />

      {/* Map fills the entire screen */}
      <MapContainer
        onMapClick={handleMapClick}
        onEventClick={handleEventClick}
        events={nearbyEvents}
        onEventsLoad={handleEventsLoad}
      />

      {/* Event creation form modal */}
      {showForm && selectedCoords && (
        <div className="absolute top-20 right-4 z-20">
          <EventForm
            lat={selectedCoords.lat}
            lon={selectedCoords.lon}
            address={selectedCoords.address}
            onClose={handleFormClose}
            onCreated={handleEventCreated}
          />
        </div>
      )}

      {/* Event detail popup */}
      {selectedEvent && !showForm && (
        <div className="absolute top-20 right-4 z-20">
          <EventPopup event={selectedEvent} onClose={handlePopupClose} />
        </div>
      )}
    </div>
  );
}
