function Navbar() {
  return (
    <header className="h-20 bg-white border-b border-slate-200 flex items-center justify-between px-8 shadow-sm z-10">
      
      <div className="flex items-center gap-4">
        <h2 className="text-xl font-semibold text-slate-800 tracking-tight">
          Cattle Skin Disease Monitoring
        </h2>
      </div>

      <div className="flex items-center gap-6">
        {/* Modern Status Indicator */}
        <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-50 border border-emerald-100 rounded-full shadow-sm">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
          </span>
          <span className="text-sm font-medium text-emerald-700">Connected</span>
        </div>

        {/* Profile Avatar Placeholder */}
        <div className="w-10 h-10 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-600 font-bold cursor-pointer hover:bg-slate-200 transition-colors">
          A
        </div>
      </div>

    </header>
  );
}

export default Navbar;