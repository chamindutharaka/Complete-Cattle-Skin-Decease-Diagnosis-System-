import React, { useState, useEffect } from "react";
import { monitoringAPI } from "../services/api";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Activity, Thermometer, Droplets, AlertTriangle } from "lucide-react";

function RealtimeData() {
  const [cattleList, setCattleList] = useState([]);
  const [selectedCattleId, setSelectedCattleId] = useState(null);
  const [cattleData, setCattleData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch cattle list on mount
  useEffect(() => {
    const fetchCattle = async () => {
      try {
        const response = await monitoringAPI.get("/api/cattle/");
        setCattleList(response.data);
        if (response.data.length > 0) {
          setSelectedCattleId(response.data[0].id);
        }
      } catch (err) {
        console.error("Failed to fetch cattle list", err);
      } finally {
        setLoading(false);
      }
    };
    fetchCattle();
  }, []);

  // Fetch Detailed cattle data with a 5s polling interval (simulating realtime)
  useEffect(() => {
    if (!selectedCattleId) return;

    const fetchCattleData = async () => {
      try {
        const response = await monitoringAPI.get(`/api/cattle/${selectedCattleId}`);
        const data = response.data;
        if (data.sensorReadings) {
          // Reverse array to put earliest at the front, latest at the end for the chart
          data.sensorReadings = data.sensorReadings.reverse().map((r) => ({
            ...r,
            temperature: Number(r.temperature), // Ensure numbers
            humidity: Number(r.humidity),
            heartRate: Number(r.heartRate),
            time: new Date(r.createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
          }));
        }
        setCattleData(data);
      } catch (err) {
        console.error("Failed to fetch specific cattle details", err);
      }
    };

    // Initial fetch
    fetchCattleData();

    // Setup polling (Every 5 seconds)
    const intervalId = setInterval(fetchCattleData, 5000);

    return () => clearInterval(intervalId);

  }, [selectedCattleId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="w-8 h-8 rounded-full border-4 border-emerald-500 border-t-transparent animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      
      {/* Header and selector */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center bg-white p-6 rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] gap-4">
        <div>
          <h2 className="text-2xl font-black text-slate-800 tracking-tight">Real-Time Data Streams</h2>
          <p className="text-slate-500 font-medium">Live IoT sensors & Deep Learning analysis</p>
        </div>
        
        {cattleList.length > 0 && (
          <select 
            className="px-4 py-3 border border-slate-200 rounded-xl bg-slate-50 text-slate-700 font-semibold focus:outline-none focus:ring-4 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all shadow-sm w-full sm:w-auto hover:bg-white"
            value={selectedCattleId || ""}
            onChange={(e) => setSelectedCattleId(Number(e.target.value))}
          >
            {cattleList.map((c) => (
              <option key={c.id} value={c.id}>{c.name} ({c.deviceId})</option>
            ))}
          </select>
        )}
      </div>

      {cattleData && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Main Chart Column */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Temperature Chart */}
            <div className="bg-white p-6 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)]">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-xl bg-orange-100/50 flex items-center justify-center text-orange-500 border border-orange-100">
                  <Thermometer size={20} />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-800 leading-tight">Temperature</h3>
                  <p className="text-sm text-slate-400 font-medium">Celsius (°C)</p>
                </div>
                {cattleData.sensorReadings.length > 0 && (
                  <div className="ml-auto text-2xl font-black text-orange-500">
                    {cattleData.sensorReadings[cattleData.sensorReadings.length - 1].temperature.toFixed(1)}°
                  </div>
                )}
              </div>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={cattleData.sensorReadings}>
                    <defs>
                        <linearGradient id="colorTemp" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#F97316" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#F97316" stopOpacity={0}/>
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                    <XAxis dataKey="time" stroke="#94A3B8" fontSize={11} tickMargin={12} minTickGap={30} />
                    <YAxis domain={['auto', 'auto']} stroke="#94A3B8" fontSize={11} width={40} axisLine={false} tickLine={false} />
                    <Tooltip 
                      contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 10px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)', padding: '12px 16px', fontWeight: 'bold' }} 
                      itemStyle={{ color: '#F97316' }}
                    />
                    <Line type="monotone" dataKey="temperature" name="Temp" stroke="#F97316" strokeWidth={3} dot={false} activeDot={{ r: 6, strokeWidth: 0 }} animationDuration={500} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Heart Rate Chart */}
            <div className="bg-white p-6 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)]">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-xl bg-rose-100/50 flex items-center justify-center text-rose-500 border border-rose-100">
                  <Activity size={20} />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-800 leading-tight">Heart Rate</h3>
                  <p className="text-sm text-slate-400 font-medium">Beats Per Minute (BPM)</p>
                </div>
                {cattleData.sensorReadings.length > 0 && (
                  <div className="ml-auto text-2xl font-black text-rose-500">
                    {cattleData.sensorReadings[cattleData.sensorReadings.length - 1].heartRate.toFixed(0)} <span className="text-sm">bpm</span>
                  </div>
                )}
              </div>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={cattleData.sensorReadings}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                    <XAxis dataKey="time" stroke="#94A3B8" fontSize={11} tickMargin={12} minTickGap={30} />
                    <YAxis domain={['auto', 'auto']} stroke="#94A3B8" fontSize={11} width={40} axisLine={false} tickLine={false} />
                    <Tooltip 
                      contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 10px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)', padding: '12px 16px', fontWeight: 'bold' }}
                      itemStyle={{ color: '#E11D48' }}
                    />
                    <Line type="monotone" dataKey="heartRate" name="BPM" stroke="#E11D48" strokeWidth={3} dot={false} activeDot={{ r: 6, strokeWidth: 0 }} animationDuration={500} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

          </div>

          {/* Side Column */}
          <div className="space-y-6 flex flex-col">
            
            {/* Humidity Card */}
            <div className="bg-gradient-to-br from-blue-500 to-indigo-600 p-6 rounded-3xl shadow-lg shadow-blue-500/20 text-white relative overflow-hidden group">
               <div className="absolute top-0 right-0 p-4 opacity-20 transform translate-x-2 -translate-y-2 group-hover:scale-110 transition-transform duration-500">
                  <Droplets size={80} />
               </div>
               <div className="relative z-10 flex flex-col h-full">
                 <div className="flex items-center gap-2 mb-2 font-semibold text-blue-100">
                    <Droplets size={18} />
                    <span>Average Humidity</span>
                  </div>
                  {cattleData.sensorReadings.length > 0 && (
                     <div className="text-5xl font-black tracking-tighter mt-2 mb-6">
                       {cattleData.sensorReadings[cattleData.sensorReadings.length - 1].humidity.toFixed(0)}<span className="text-2xl opacity-70">%</span>
                     </div>
                  )}
                  
                  <div className="h-24 w-full mt-auto opacity-70">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={cattleData.sensorReadings}>
                          <Line type="monotone" dataKey="humidity" stroke="#ffffff" strokeWidth={3} dot={false} animationDuration={500} />
                        </LineChart>
                      </ResponsiveContainer>
                  </div>
               </div>
            </div>

            {/* AI Alerts Box */}
            <div className="bg-white rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] flex-1 border border-amber-100/50 flex flex-col overflow-hidden">
              <div className="flex items-center gap-3 p-6 pb-4 border-b border-slate-100 bg-gradient-to-b from-amber-50/30 to-white">
                <div className="w-10 h-10 rounded-xl bg-amber-100/50 flex items-center justify-center text-amber-500 border border-amber-200/50">
                  <AlertTriangle size={20} />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-800 leading-tight">AI Anomalies</h3>
                  <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider mt-0.5">Deep Learning Network</p>
                </div>
                {cattleData.alerts && cattleData.alerts.length > 0 && (
                   <div className="ml-auto bg-amber-500 text-white text-xs font-bold px-2 py-1 rounded-md">
                     {cattleData.alerts.length} NEW
                   </div>
                )}
              </div>
              <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
                {cattleData.alerts && cattleData.alerts.length > 0 ? (
                  cattleData.alerts.map(alert => (
                    <div key={alert.id} className="p-4 rounded-2xl bg-amber-50/50 border border-amber-100 hover:border-amber-300 transition-colors flex gap-3 group">
                      <div className="mt-1">
                        <div className="w-2 h-2 rounded-full bg-amber-500 group-hover:scale-150 transition-transform shadow-[0_0_8px_rgba(245,158,11,0.6)]"></div>
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-slate-800 leading-snug">{alert.message}</p>
                        <p className="text-[11px] font-medium text-amber-600 mt-1.5 opacity-80">{new Date(alert.createdAt).toLocaleString()}</p>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="flex flex-col items-center justify-center h-full my-8 text-center px-4">
                    <div className="w-12 h-12 rounded-full bg-slate-50 flex items-center justify-center mb-3">
                       <AlertTriangle className="text-slate-300" size={24} />
                    </div>
                    <p className="text-slate-500 font-medium">No anomalies detected</p>
                    <p className="text-xs text-slate-400 mt-1">The DL model has not flagged any recent patterns as abnormal.</p>
                  </div>
                )}
              </div>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}

export default RealtimeData;
