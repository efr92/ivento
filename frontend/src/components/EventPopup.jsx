import { useState } from 'react';
import { joinEvent } from '../api/client';
import { CATEGORIES } from '../utils/categories';
import { formatDate } from '../utils/formatDate';

export default function EventPopup({ event, onClose }) {
  const [joining, setJoining] = useState(false);
  const [joinError, setJoinError] = useState('');
  const [joined, setJoined] = useState(false);
  const [participants, setParticipants] = useState(event.current_participants);

  const handleJoin = async () => {
    setJoining(true);
    setJoinError('');
    try {
      await joinEvent(event.id);
      setJoined(true);
      setParticipants((p) => p + 1);
    } catch (err) {
      setJoinError(err.message || 'Не удалось присоединиться');
    } finally {
      setJoining(false);
    }
  };

  const isFull =
    event.max_participants && participants >= event.max_participants;

  return (
    <div className="bg-white rounded-xl shadow-xl p-5 w-80 max-h-96 overflow-y-auto event-popup-scroll">
      <div className="flex justify-between items-start mb-3">
        <h2 className="text-lg font-bold text-gray-900">{event.title}</h2>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 text-xl leading-none"
        >
          ×
        </button>
      </div>

      <span className="inline-block px-2 py-0.5 bg-indigo-100 text-indigo-700 text-xs rounded-full mb-3">
        {CATEGORIES[event.category] || event.category}
      </span>

      {event.description && (
        <p className="text-gray-600 text-sm mb-3">{event.description}</p>
      )}

      <div className="text-gray-500 text-xs space-y-1 mb-3">
        {event.address && <p>📍 {event.address}</p>}
        <p>🕐 {formatDate(event.start_time)}</p>
        {event.end_time && <p>⏹ {formatDate(event.end_time)}</p>}
        <p>
          👥 {participants}
          {event.max_participants ? ` / ${event.max_participants}` : ''}
        </p>
      </div>

      {joinError && (
        <div className="bg-red-100 border border-red-300 text-red-700 px-3 py-1.5 rounded-lg mb-3 text-xs">
          {joinError}
        </div>
      )}

      {!joined ? (
        <button
          onClick={handleJoin}
          disabled={joining || isFull}
          className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white text-sm rounded-lg transition-colors"
        >
          {isFull
            ? 'Мест нет'
            : joining
              ? 'Подождите...'
              : 'Присоединиться'}
        </button>
      ) : (
        <p className="text-green-600 text-sm text-center font-medium">✓ Вы участвуете</p>
      )}
    </div>
  );
}
