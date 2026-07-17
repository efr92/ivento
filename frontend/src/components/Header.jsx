import { useAuth } from '../hooks/useAuth';

export default function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="absolute top-0 left-0 right-0 z-10 bg-gray-900/90 backdrop-blur border-b border-gray-700 px-4 py-2 flex items-center justify-between">
      <h1 className="text-white font-bold text-lg">Ivento</h1>
      <div className="flex items-center gap-3">
        <span className="text-gray-300 text-sm">{user?.email}</span>
        <button
          onClick={logout}
          className="px-3 py-1 bg-red-600/80 hover:bg-red-700 text-white text-sm rounded-lg transition-colors"
        >
          Выйти
        </button>
      </div>
    </header>
  );
}
