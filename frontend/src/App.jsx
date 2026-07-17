import { AuthProvider, useAuth } from './hooks/useAuth';
import AuthPage from './components/AuthPage';
import MapPage from './components/MapPage';

function AppContent() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900 text-white">
        <p className="text-lg">Загрузка...</p>
      </div>
    );
  }

  if (!user) {
    return <AuthPage />;
  }

  return <MapPage />;
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
