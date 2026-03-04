import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";
import { Outlet } from "react-router-dom";

function DashboardLayout() {
  return (
    <div className="flex h-screen overflow-hidden bg-slate-50 font-sans text-slate-900">
      
      <Sidebar />

      <div className="flex-1 flex flex-col relative overflow-hidden">
        
        <Navbar />

        <main className="flex-1 overflow-y-auto p-8">
          {/* Centered container for better ultra-wide monitor support */}
          <div className="mx-auto max-w-7xl">
            <Outlet />
          </div>
        </main>

      </div>

    </div>
  );
}

export default DashboardLayout;