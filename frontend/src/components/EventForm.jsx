import { useState } from 'react';
import { createEvent } from '../api/client';
import { CATEGORIES } from '../utils/categories';

export default function EventForm({ lat, lon, address: initialAddress, onClose, onCreated }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [address, setAddress] = useState(initialAddress || '');
  const [category, setCategory] = useState('other');
  const [startTime, setStartTime] = useState(() => {
    // Default: tomorrow at 18:00
    const t = new Date();
    t.setDate(t.getDate() + 1);
    t.setHours(18, 0, 0, 0);
    return t.toISOString().slice(0, 16);
  });
  const [endTime, setEndTime] = useState('');
  const [maxParticipants, setMaxParticipants] = useState('');

  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!title.trim()) {
      setError('Укажите название события');
      return;
    }

    setSubmitting(true);
    try {
      const body = {
        title: title.trim(),
        description: description.trim() || undefined,
        latitude: lat,
        longitude: lon,
        address: address.trim() || undefined,
        category,
        start_time: new Date(startTime).toISOString(),
        end_time: endTime ? new Date(endTime).toISOString() : undefined,
        max_participants: maxParticipants ? parseInt(maxParticipants, 10) : undefined,
      };

      const created = await createEvent(body);
      onCreated(created);
      onClose();
    } catch (err) {
      setError(err.message || 'Не удалось создать событие');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-xl p-5 w-80 max-h-[90vh] overflow-y-auto event-popup-scroll">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-bold text-gray-900">Новое событие</h2>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 text-xl leading-none"
        >
          ×
        </button>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-300 text-red-700 px-3 py-1.5 rounded-lg mb-3 text-xs">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label className="block text-gray-700 text-xs mb-0.5 font-medium">
            Название *
          </label>
          <input
            type="text"
            required
            minLength={3}
            maxLength={200}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-3 py-1.5 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="Название события"
          />
        </div>

        <div>
          <label className="block text-gray-700 text-xs mb-0.5 font-medium">
            Описание
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={2}
            className="w-full px-3 py-1.5 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
            placeholder="Краткое описание"
          />
        </div>

        <div>
          <label className="block text-gray-700 text-xs mb-0.5 font-medium">
            Категория
          </label>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="w-full px-3 py-1.5 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {Object.entries(CATEGORIES).map(([key, label]) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-gray-700 text-xs mb-0.5 font-medium">
            Адрес
          </label>
          <input
            type="text"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            className="w-full px-3 py-1.5 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="Улица, дом"
          />
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="block text-gray-700 text-xs mb-0.5 font-medium">
              Начало *
            </label>
            <input
              type="datetime-local"
              required
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              className="w-full px-2 py-1.5 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-gray-700 text-xs mb-0.5 font-medium">
              Конец
            </label>
            <input
              type="datetime-local"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              className="w-full px-2 py-1.5 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-gray-700 text-xs mb-0.5 font-medium">
            Макс. участников
          </label>
          <input
            type="number"
            min={2}
            max={10000}
            value={maxParticipants}
            onChange={(e) => setMaxParticipants(e.target.value)}
            className="w-full px-3 py-1.5 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="Без ограничений"
          />
        </div>

        <p className="text-gray-400 text-xs">
          Координаты: {lat.toFixed(6)}, {lon.toFixed(6)}
        </p>

        <button
          type="submit"
          disabled={submitting}
          className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-800 disabled:cursor-not-allowed text-white rounded-lg transition-colors text-sm font-medium"
        >
          {submitting ? 'Создаю...' : 'Создать событие'}
        </button>
      </form>
    </div>
  );
}
