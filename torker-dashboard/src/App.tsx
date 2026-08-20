import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import { Layout } from './components/Layout';
import { ProtectedRoute, GuestRoute } from './components/ProtectedRoute';
import { HomePage } from './pages/HomePage';
import { ClientesPage } from './pages/ClientesPage';
import { AgendaPage } from './pages/AgendaPage';
import { ParchePage } from './pages/ParchePage';
import { InventarioPage } from './pages/InventarioPage';
import { OrdenesPage } from './pages/OrdenesPage';
import { LoginPage } from './pages/LoginPage';

export default function App() {
  return (
    <BrowserRouter basename="/pages/dashboard/app">
      <Routes>
        <Route element={<GuestRoute />}>
          <Route path="login" element={<LoginPage />} />
        </Route>

        <Route element={<ProtectedRoute />}>
          <Route
            element={
              <AppProvider>
                <Layout />
              </AppProvider>
            }
          >
            <Route index element={<HomePage />} />
            <Route path="clientes" element={<ClientesPage />} />
            <Route path="agenda" element={<AgendaPage />} />
            <Route path="inventario" element={<InventarioPage />} />
            <Route path="ordenes" element={<OrdenesPage />} />
            <Route path="parche" element={<ParchePage />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
