import { Link, useLocation } from "react-router-dom";
import { LayoutDashboard, Activity, BarChart3, Stethoscope, AlertTriangle, Clock } from "lucide-react";

function Sidebar() {
  const location = useLocation();

  // Array of links to map over, making it easier to manage icons and paths
  const navItems = [
    { path: "/", label: "Dashboard", icon: <LayoutDashboard size={20} /> },
    { path: "/monitoring", label: "Monitoring", icon: <Activity size={20} /> },
    { path: "/realtime-data", label: "Realtime Data", icon: <BarChart3 size={20} /> },
    { path: "/history", label: "History", icon: <Clock size={20} /> },
    { path: "/diagnosis", label: "Diagnosis", icon: <Stethoscope size={20} /> },
    { path: "/severity", label: "Severity", icon: <AlertTriangle size={20} /> },
  ];

  return (
    <aside className="w-64 h-screen bg-slate-950 text-slate-300 flex flex-col border-r border-slate-800">
      
      {/* Brand Header */}
      <div className="h-20 flex items-center gap-3 px-6 border-b border-slate-800/60">
        <div className="w-8 h-8 bg-emerald-500 rounded-lg flex items-center justify-center text-white font-bold shadow-lg shadow-emerald-500/20">
          C
        </div>
        <h1 className="text-xl font-bold text-white tracking-wide">
          Cattle AI
        </h1>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                isActive
                  ? "bg-emerald-500/10 text-emerald-400 font-medium"
                  : "hover:bg-slate-800/50 hover:text-white text-slate-400"
              }`}
            >
              <span className={isActive ? "text-emerald-400" : "text-slate-500"}>
                {item.icon}
              </span>
              {item.label}
            </Link>
          );
        })}
      </nav>

    </aside>
  );
}

export default Sidebar;