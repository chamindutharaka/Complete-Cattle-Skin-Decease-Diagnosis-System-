import { Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";

import DashboardLayout from "./layouts/DashboardLayout";
import ProtectedRoute from "./components/ProtectedRoute";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Monitoring from "./pages/Monitoring";
import RealtimeData from "./pages/RealtimeData";
import Diagnosis from "./pages/Diagnosis";
import Severity from "./pages/Severity";

function App() {
  return (
    <AuthProvider>
      <Routes>

        <Route path="/login" element={<Login />} />

        {/* Public route with layout */}
        <Route element={<DashboardLayout />}>
          <Route path="/realtime-data" element={<RealtimeData />} />
        </Route>

        {/* Protected routes */}
        <Route
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<Dashboard />} />
          <Route path="/monitoring" element={<Monitoring />} />
          <Route path="/diagnosis" element={<Diagnosis />} />
          <Route path="/severity" element={<Severity />} />
        </Route>

      </Routes>
    </AuthProvider>
  );
}

export default App;