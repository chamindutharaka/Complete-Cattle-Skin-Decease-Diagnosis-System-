import React, { useState, useEffect } from "react";
import { monitoringAPI } from "../services/api";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  Thermometer,
  Droplets,
  Activity,
  AlertTriangle,
  Clock,
  TrendingUp,
  CheckCircle2,
  BrainCircuit,
  Download,
} from "lucide-react";

// CSV export helper
function downloadCSV(readings, cowName) {
  const headers = ["Timestamp", "Temperature (°C)", "Heart Rate (BPM)", "Humidity (%)"];
  const rows = readings
    .slice()
    .reverse()
    .map((r) => [r.dateStr, r.temp, r.heart, r.hum]);
  const csvContent = [headers, ...rows].map((r) => r.join(",")).join("\n");
  const blob = new Blob([csvContent], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${cowName || "cattle"}_history.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

function StatCard({ icon, label, value, unit, color }) {
  const colors = {
    orange: "bg-orange-100/50 text-orange-500 border-orange-100",
    rose: "bg-rose-100/50 text-rose-500 border-rose-100",
    blue: "bg-blue-100/50 text-blue-500 border-blue-100",
    amber: "bg-amber-100/50 text-amber-500 border-amber-100",
    violet: "bg-violet-100/50 text-violet-500 border-violet-100",
  };
  return (
    <div className="bg-white p-5 rounded-2xl shadow-[0_4px_20px_rgb(0,0,0,0.04)] flex items-center gap-4">
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center border shrink-0 ${colors[color]}`}>
        {icon}
      </div>
      <div className="min-w-0">
        <p className="text-xs text-slate-400 font-semibold truncate">{label}</p>
        <p className="text-2xl font-black text-slate-800 leading-tight">
          {value}<span className="text-sm font-semibold text-slate-400 ml-1">{unit}</span>
        </p>
      </div>
    </div>
  );
}

export default function HistoryData() {
  const [cattleList, setCattleList] = useState([]);
  const [selectedCattleId, setSelectedCattleId] = useState(null);
  const [cattleData, setCattleData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    monitoringAPI.get("/api/cattle/").then((res) => {
      setCattleList(res.data || []);
      if (res.data?.length) setSelectedCattleId(res.data[0].id);
    }).catch(console.error).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedCattleId) return;
    monitoringAPI.get(`/api/cattle/${selectedCattleId}`).then((res) => {
      const data = res.data;
      if (!data.sensorReadings) return;
      const readings = data.sensorReadings.map((r) => ({
        ...r,
        temp: Number(r.temperature),
        hum: Number(r.humidity),
        heart: Number(r.heartRate),
        time: new Date(r.createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        dateStr: new Date(r.createdAt).toLocaleString(),
      })).reverse();

      const avg = (arr) => arr.reduce((a, b) => a + b, 0) / arr.length;
      const temps = readings.map((r) => r.temp);
      const hearts = readings.map((r) => r.heart);
      const hums = readings.map((r) => r.hum);
      setStats({
        avgTemp: avg(temps).toFixed(1),
        maxTemp: Math.max(...temps).toFixed(1),
        minTemp: Math.min(...temps).toFixed(1),
        avgHeart: avg(hearts).toFixed(0),
        avgHum: avg(hums).toFixed(0),
        anomalyCount: data.alerts?.length ?? 0,
        totalReadings: readings.length,
        healthScore: Math.max(0, 100 - (data.alerts?.length ?? 0) * 5),
      });
      setCattleData({ ...data, sensorReadings: readings });
    }).catch(console.error);
  }, [selectedCattleId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="w-8 h-8 rounded-full border-4 border-emerald-500 border-t-transparent animate-spin" />
      </div>
    );
  }

  const selectedCow = cattleList.find((c) => c.id === selectedCattleId);

  return (
    <div className="space-y-5 animate-in fade-in slide-in-from-bottom-4 duration-500">

      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center bg-white p-5 rounded-2xl shadow-[0_4px_20px_rgb(0,0,0,0.04)] gap-3">
        <div>
          <h2 className="text-2xl font-black text-slate-800 tracking-tight">Historical Health Data</h2>
          <p className="text-slate-500 font-medium text-sm">Long-term sensor analysis &amp; anomaly review</p>
        </div>
        <div className="flex items-center gap-3 w-full sm:w-auto">
          {cattleList.length > 0 && (
            <select
              className="flex-1 sm:flex-none px-4 py-2.5 border border-slate-200 rounded-xl bg-slate-50 text-slate-700 font-semibold focus:outline-none focus:ring-4 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all hover:bg-white text-sm"
              value={selectedCattleId || ""}
              onChange={(e) => setSelectedCattleId(e.target.value)}
            >
              {cattleList.map((c) => (
                <option key={c.id} value={c.id}>{c.name} ({c.deviceId})</option>
              ))}
            </select>
          )}
          {cattleData && (
            <button
              onClick={() => downloadCSV(cattleData.sensorReadings, selectedCow?.name)}
              className="flex items-center gap-2 px-4 py-2.5 bg-emerald-500 text-white rounded-xl font-bold text-sm hover:bg-emerald-600 active:scale-95 transition-all shadow-lg shadow-emerald-500/25 whitespace-nowrap"
            >
              <Download size={16} />
              CSV
            </button>
          )}
        </div>
      </div>

      {cattleData && stats && (
        <>
          {/* Stat Cards Row */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
            <StatCard icon={<Thermometer size={20} />} label="Avg Temperature" value={stats.avgTemp} unit="°C" color="orange" />
            <StatCard icon={<Activity size={20} />} label="Avg Heart Rate" value={stats.avgHeart} unit="BPM" color="rose" />
            <StatCard icon={<Droplets size={20} />} label="Avg Humidity" value={stats.avgHum} unit="%" color="blue" />
            <StatCard icon={<TrendingUp size={20} />} label="Peak Temperature" value={stats.maxTemp} unit="°C" color="amber" />
            <StatCard icon={<AlertTriangle size={20} />} label="AI Anomalies" value={stats.anomalyCount} unit="" color="violet" />
          </div>

          {/* Charts Row 1: Temperature Area + Health Score */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
            <div className="lg:col-span-2 bg-white p-6 rounded-2xl shadow-[0_4px_20px_rgb(0,0,0,0.04)]">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-9 h-9 rounded-xl bg-orange-100/50 flex items-center justify-center text-orange-500 border border-orange-100">
                  <Thermometer size={18} />
                </div>
                <div className="flex-1">
                  <h3 className="text-base font-bold text-slate-800 leading-tight">Temperature History</h3>
                  <p className="text-xs text-slate-400 font-medium">Last {stats.totalReadings} readings · °C</p>
                </div>
                <div className="text-2xl font-black text-orange-500">{stats.avgTemp}°</div>
              </div>
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={cattleData.sensorReadings}>
                    <defs>
                      <linearGradient id="gradTemp" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#F97316" stopOpacity={0.2} />
                        <stop offset="95%" stopColor="#F97316" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                    <XAxis dataKey="time" stroke="#94A3B8" fontSize={10} tickMargin={8} minTickGap={30} axisLine={false} tickLine={false} />
                    <YAxis domain={["auto", "auto"]} stroke="#94A3B8" fontSize={10} width={36} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={{ borderRadius: "12px", border: "none", boxShadow: "0 10px 25px -5px rgba(0,0,0,0.1)", fontWeight: "bold", padding: "10px 14px" }} itemStyle={{ color: "#F97316" }} />
                    <Area type="monotone" dataKey="temp" name="Temp (°C)" stroke="#F97316" strokeWidth={3} fill="url(#gradTemp)" dot={false} activeDot={{ r: 5, strokeWidth: 0 }} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Health Score + Temp Range stacked */}
            <div className="flex flex-col gap-4">
              <div className="bg-gradient-to-br from-slate-800 to-slate-900 p-6 rounded-2xl text-white relative overflow-hidden flex-1">
                <div className="absolute -right-6 -top-6 w-32 h-32 bg-emerald-500/10 rounded-full blur-2xl" />
                <div className="flex items-center gap-2 mb-1 text-slate-400 font-semibold text-xs">
                  <BrainCircuit size={14} className="text-emerald-500" />
                  AI Health Score
                </div>
                <div className="text-6xl font-black tracking-tighter text-white mb-2">{stats.healthScore}</div>
                <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden mb-3">
                  <div className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full" style={{ width: `${stats.healthScore}%` }} />
                </div>
                <p className="text-slate-500 text-xs">{stats.totalReadings} readings · {stats.anomalyCount} anomalies flagged</p>
              </div>
              <div className="bg-white p-5 rounded-2xl shadow-[0_4px_20px_rgb(0,0,0,0.04)] flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-100/50 flex items-center justify-center text-emerald-500 border border-emerald-100 shrink-0">
                  <CheckCircle2 size={20} />
                </div>
                <div>
                  <p className="text-xs font-semibold text-slate-400">Temperature Range</p>
                  <p className="text-lg font-black text-slate-800">{stats.minTemp}° – {stats.maxTemp}°C</p>
                </div>
              </div>
            </div>
          </div>

          {/* Charts Row 2: Heart Rate + Humidity + Bar Distribution */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

            {/* Heart Rate */}
            <div className="bg-white p-6 rounded-2xl shadow-[0_4px_20px_rgb(0,0,0,0.04)]">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-9 h-9 rounded-xl bg-rose-100/50 flex items-center justify-center text-rose-500 border border-rose-100">
                  <Activity size={18} />
                </div>
                <div className="flex-1">
                  <h3 className="text-base font-bold text-slate-800">Heart Rate History</h3>
                  <p className="text-xs text-slate-400 font-medium">BPM over time</p>
                </div>
                <div className="text-2xl font-black text-rose-500">{stats.avgHeart}<span className="text-sm">bpm</span></div>
              </div>
              <div className="h-36">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={cattleData.sensorReadings}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                    <XAxis dataKey="time" hide />
                    <YAxis domain={["auto", "auto"]} fontSize={10} width={32} axisLine={false} tickLine={false} stroke="#94A3B8" />
                    <Tooltip contentStyle={{ borderRadius: "12px", border: "none", fontWeight: "bold", padding: "10px 14px" }} itemStyle={{ color: "#E11D48" }} />
                    <Line type="monotone" dataKey="heart" name="BPM" stroke="#E11D48" strokeWidth={3} dot={false} activeDot={{ r: 5, strokeWidth: 0 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Humidity */}
            <div className="bg-gradient-to-br from-blue-500 to-indigo-600 p-6 rounded-2xl shadow-lg shadow-blue-500/20 text-white relative overflow-hidden">
              <div className="absolute top-0 right-0 p-4 opacity-10">
                <Droplets size={64} />
              </div>
              <div className="relative z-10">
                <div className="flex items-center gap-2 mb-1 font-semibold text-blue-100 text-xs">
                  <Droplets size={14} /> Avg Humidity
                </div>
                <div className="text-5xl font-black tracking-tighter mb-4">{stats.avgHum}<span className="text-xl opacity-70">%</span></div>
                <div className="h-20 opacity-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={cattleData.sensorReadings}>
                      <defs>
                        <linearGradient id="gradHum" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#ffffff" stopOpacity={0.4} />
                          <stop offset="95%" stopColor="#ffffff" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <Area type="monotone" dataKey="hum" stroke="#ffffff" strokeWidth={2.5} fill="url(#gradHum)" dot={false} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
                <p className="text-blue-200 text-[11px] font-medium mt-2">Measured over {stats.totalReadings} readings</p>
              </div>
            </div>

            {/* Temp Distribution Bar */}
            <div className="bg-white p-6 rounded-2xl shadow-[0_4px_20px_rgb(0,0,0,0.04)]">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-9 h-9 rounded-xl bg-violet-100/50 flex items-center justify-center text-violet-500 border border-violet-100">
                  <Clock size={18} />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-800">Temp Distribution</h3>
                  <p className="text-xs text-slate-400 font-medium">Latest 20 readings</p>
                </div>
              </div>
              <div className="h-36">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={cattleData.sensorReadings.slice(-20)} barSize={9}>
                    <YAxis domain={["auto", "auto"]} hide />
                    <XAxis dataKey="time" hide />
                    <Tooltip contentStyle={{ borderRadius: "12px", border: "none", fontWeight: "bold", padding: "10px 14px" }} itemStyle={{ color: "#8B5CF6" }} />
                    <Bar dataKey="temp" name="Temp (°C)" fill="#8B5CF6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Sensor Log — Full Width Solo Row */}
          <div className="bg-white rounded-2xl shadow-[0_4px_20px_rgb(0,0,0,0.04)] overflow-hidden">
            <div className="flex items-center justify-between gap-3 px-6 py-4 border-b border-slate-100">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-slate-100 flex items-center justify-center text-slate-500 border border-slate-200">
                  <Clock size={18} />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-800">Sensor Log</h3>
                  <p className="text-xs text-slate-400 font-medium">{stats.totalReadings} records from MongoDB</p>
                </div>
              </div>
              <button
                onClick={() => downloadCSV(cattleData.sensorReadings, selectedCow?.name)}
                className="flex items-center gap-2 px-4 py-2 bg-slate-50 border border-slate-200 text-slate-600 rounded-xl font-bold text-xs hover:bg-emerald-50 hover:border-emerald-300 hover:text-emerald-600 active:scale-95 transition-all"
              >
                <Download size={14} />
                Download CSV
              </button>
            </div>
            <div className="overflow-auto max-h-64">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-slate-50 z-10">
                  <tr className="text-slate-400 text-xs font-black uppercase tracking-wider">
                    <th className="text-left py-3 px-6">Timestamp</th>
                    <th className="text-center py-3 px-4">Temp (°C)</th>
                    <th className="text-center py-3 px-4">Heart Rate (BPM)</th>
                    <th className="text-center py-3 px-4">Humidity (%)</th>
                    <th className="text-right py-3 px-6">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {cattleData.sensorReadings.slice().reverse().map((r, idx) => (
                    <tr key={r.id || idx} className="border-t border-slate-50 hover:bg-slate-50/80 transition-colors">
                      <td className="py-2.5 px-6 font-medium text-slate-600 text-xs">{r.dateStr}</td>
                      <td className={`text-center py-2.5 px-4 font-bold text-sm ${r.temp > 39.5 ? "text-orange-500" : "text-slate-700"}`}>{r.temp}</td>
                      <td className="text-center py-2.5 px-4 font-bold text-sm text-slate-700">{r.heart}</td>
                      <td className="text-center py-2.5 px-4 font-bold text-sm text-slate-700">{r.hum}</td>
                      <td className="text-right py-2.5 px-6">
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wide ${r.temp > 39.5 ? "bg-orange-100 text-orange-600" : "bg-emerald-100 text-emerald-600"}`}>
                          {r.temp > 39.5 ? "Warn" : "OK"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* AI Anomaly Panel — Full Width Solo Row */}
          <div className="bg-white rounded-2xl shadow-[0_4px_20px_rgb(0,0,0,0.04)] overflow-hidden border border-amber-100/60">
            <div className="flex items-center gap-3 px-6 py-4 border-b border-slate-100 bg-gradient-to-b from-amber-50/30 to-white">
              <div className="w-9 h-9 rounded-xl bg-amber-100/50 flex items-center justify-center text-amber-500 border border-amber-200/50">
                <AlertTriangle size={18} />
              </div>
              <div className="flex-1">
                <h3 className="text-base font-bold text-slate-800">AI Anomaly History</h3>
                <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider mt-0.5">Deep Learning Network Flags</p>
              </div>
              {stats.anomalyCount > 0 && (
                <div className="bg-amber-500 text-white text-xs font-bold px-2.5 py-1 rounded-lg">{stats.anomalyCount} alerts</div>
              )}
            </div>
            <div className="p-4">
              {cattleData.alerts && cattleData.alerts.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {cattleData.alerts.map((alert) => (
                    <div key={alert.id} className="p-4 rounded-2xl bg-amber-50/50 border border-amber-100 hover:border-amber-300 transition-colors flex gap-3">
                      <div className="mt-1.5 shrink-0">
                        <div className="w-2 h-2 rounded-full bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.6)]" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-slate-800 leading-snug">{alert.message}</p>
                        <p className="text-[11px] font-medium text-amber-600 mt-1">{new Date(alert.createdAt).toLocaleString()}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <div className="w-12 h-12 rounded-full bg-slate-50 flex items-center justify-center mb-3">
                    <AlertTriangle className="text-slate-300" size={22} />
                  </div>
                  <p className="text-slate-500 font-medium">No anomalies recorded for this animal</p>
                  <p className="text-xs text-slate-400 mt-1">The AI model has not flagged any abnormal patterns.</p>
                </div>
              )}
            </div>
          </div>

        </>
      )}
    </div>
  );
}
