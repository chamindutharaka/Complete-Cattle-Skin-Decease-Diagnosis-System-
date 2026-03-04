import React, { useState, useEffect } from "react";
import { 
  UploadCloud, Thermometer, Droplets, Activity, 
  RefreshCw, ShieldAlert, LineChart, Calendar 
} from "lucide-react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Line } from "react-chartjs-2";

// --- Register ChartJS Components ---
ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler
);

function Diagnosis() {
  const [preview, setPreview] = useState(null);
  const [file, setFile] = useState(null);
  
  // Input States
  const [temperature, setTemperature] = useState("");
  const [humidity, setHumidity] = useState("");
  
  // App States
  const [diagnosisText, setDiagnosisText] = useState("No image analyzed yet");
  const [isLoading, setIsLoading] = useState(false);
  const [contextInfo, setContextInfo] = useState([]);
  
  // Data States
  const [iotData, setIotData] = useState({ temperature: null, humidity: null, device_id: null });
  const [historyData, setHistoryData] = useState([]);
  const [dateFilter, setDateFilter] = useState("");

  // --- 1. Auto-Refresh Live Data ---
  useEffect(() => {
    const fetchIoTData = async () => {
      try {
        const response = await fetch("http://127.0.0.1:2200/iot-data");
        const data = await response.json();
        if (!data.error) {
          setIotData({ 
            temperature: data.temperature, 
            humidity: data.humidity,
            device_id: data.device_id || "ESP32-01"
          });
        }
      } catch (error) { 
        // Silently fail on network error
      }
    };
    fetchIoTData();
    const intervalId = setInterval(fetchIoTData, 2000);
    return () => clearInterval(intervalId);
  }, []);

  // --- 2. Fetch Historical Data ---
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await fetch("http://127.0.0.1:2200/historical-data");
        const data = await response.json();
        if (Array.isArray(data)) {
          setHistoryData(data);
        }
      } catch (error) {
        console.error("Failed to load history");
      }
    };
    fetchHistory();
  }, []);

  // --- Helper: Fill Inputs from IoT ---
  const syncWithSensors = () => {
    if (iotData.temperature !== null) setTemperature(iotData.temperature);
    if (iotData.humidity !== null) setHumidity(iotData.humidity);
  };

  const previewImage = (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;
    setFile(selectedFile);
    setContextInfo([]);
    setDiagnosisText("No image analyzed yet");
    const reader = new FileReader();
    reader.onload = () => setPreview(reader.result);
    reader.readAsDataURL(selectedFile);
  };

  const generateContextBoxes = (temp, hum) => {
    const messages = [];
    if (!isNaN(temp)) {
      if (temp >= 41) messages.push({ type: "danger", text: `High Body Temp (${temp}°C) indicates severe fever.` });
      else if (temp >= 40) messages.push({ type: "warning", text: `Elevated Body Temp (${temp}°C) may indicate infection.` });
      else messages.push({ type: "normal", text: `Normal Body Temp (${temp}°C).` });
    }
    if (!isNaN(hum)) {
      if (hum >= 75) messages.push({ type: "danger", text: `High Humidity (${hum}%) favors disease vectors.` });
      else if (hum >= 65) messages.push({ type: "warning", text: `Moderate Humidity (${hum}%) increases risk.` });
      else messages.push({ type: "normal", text: `Normal Humidity (${hum}%).` });
    }
    setContextInfo(messages);
  };

  const uploadImage = async () => {
    if (!file) {
      alert("Please upload an image first.");
      return;
    }
    setIsLoading(true);
    setDiagnosisText("Analyzing image...");
    setContextInfo([]);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://127.0.0.1:2200/predict", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();

      if (data.error) {
        setDiagnosisText(data.error);
      } else if (data.prediction) {
        setDiagnosisText(`Prediction: ${data.prediction} (${data.confidence}% confidence)`);
      } else {
        setDiagnosisText("No visible cattle skin disease detected.");
      }
      generateContextBoxes(parseFloat(temperature), parseFloat(humidity));
    } catch {
      setDiagnosisText("Server error during prediction.");
    } finally {
      setIsLoading(false);
    }
  };

  // --- Chart Configuration ---
  const chartData = {
    labels: historyData.slice(-15).map(d => d.Timestamp || d.Date || ""),
    datasets: [
      {
        label: 'Temperature (°C)',
        data: historyData.slice(-15).map(d => d.Temperature),
        borderColor: '#10b981', // emerald-500
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.4,
        fill: true,
      },
      {
        label: 'Humidity (%)',
        data: historyData.slice(-15).map(d => d.Humidity),
        borderColor: '#3b82f6', // blue-500
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
        fill: true,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: '#94a3b8' } },
    },
    scales: {
      y: { grid: { color: '#334155' }, ticks: { color: '#94a3b8' } },
      x: { grid: { display: false }, ticks: { color: '#94a3b8' } },
    }
  };

  // --- Filtered Table Data ---
  const filteredHistory = historyData.filter(item => {
    if (!dateFilter) return true;
    const itemDate = item.Timestamp || item.Date || "";
    return itemDate.includes(dateFilter);
  });

  return (
    <div className="animate-in fade-in duration-500 bg-slate-900 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-800 to-slate-900 p-8 rounded-3xl text-slate-200 border border-slate-800 shadow-2xl space-y-12">
      
      {/* Header */}
      <header className="flex items-center gap-4">
        <div className="w-12 h-12 bg-emerald-500/20 rounded-xl flex items-center justify-center text-emerald-400 border border-emerald-500/30 shadow-inner">
          <ShieldAlert size={24} />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Cattle Diagnostic AI</h1>
          <p className="text-slate-400 text-sm mt-1">Smart Skin Disease Analysis & Environmental Context</p>
        </div>
      </header>

      {/* TOP GRID: Upload & Current Results */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Left Column: Input & Upload */}
        <div className="bg-slate-800 p-6 rounded-2xl shadow-lg border border-slate-700 flex flex-col gap-6">
          
          <label className={`relative flex flex-col items-center justify-center border-2 border-dashed rounded-xl h-64 cursor-pointer transition-colors overflow-hidden ${preview ? 'border-transparent bg-transparent' : 'border-slate-600 bg-white/5 hover:border-emerald-500 hover:bg-emerald-500/10'}`}>
            <input type="file" accept="image/*" hidden onChange={previewImage} />
            {preview ? (
              <img src={preview} alt="preview" className="absolute inset-0 w-full h-full object-cover" />
            ) : (
              <div className="flex flex-col items-center gap-3 text-slate-400">
                <div className="w-12 h-12 bg-slate-700 rounded-full flex items-center justify-center text-slate-300">
                  <UploadCloud size={24} />
                </div>
                <div className="text-center">
                  <span className="block font-semibold text-slate-300">Click to Upload Image</span>
                  <span className="text-xs opacity-70">Supports JPG, PNG</span>
                </div>
              </div>
            )}
          </label>

          <div>
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Environmental Data</h3>
              <button 
                onClick={syncWithSensors}
                className="flex items-center gap-2 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-medium rounded-lg transition-colors border border-slate-600"
              >
                <RefreshCw size={14} /> Sync Sensors
              </button>
            </div>
            
            <div className="flex gap-4">
              <div className="relative flex-1">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                  <Thermometer size={18} />
                </div>
                <input
                  type="number"
                  placeholder="Temp (°C)"
                  value={temperature}
                  onChange={(e) => setTemperature(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-slate-900 border border-slate-700 rounded-xl focus:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-colors text-sm text-white placeholder-slate-500"
                />
              </div>
              <div className="relative flex-1">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                  <Droplets size={18} />
                </div>
                <input
                  type="number"
                  placeholder="Humidity (%)"
                  value={humidity}
                  onChange={(e) => setHumidity(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-slate-900 border border-slate-700 rounded-xl focus:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-colors text-sm text-white placeholder-slate-500"
                />
              </div>
            </div>
          </div>

          <button 
            onClick={uploadImage} 
            disabled={isLoading}
            className="mt-auto w-full bg-emerald-600 hover:bg-emerald-500 text-white font-medium py-3 px-4 rounded-xl transition-all duration-200 shadow-lg shadow-emerald-900/50 focus:outline-none disabled:opacity-70 flex justify-center items-center gap-2"
          >
            {isLoading ? (
              <><div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div> Analyzing...</>
            ) : "Run AI Diagnosis"}
          </button>
        </div>

        {/* Right Column: Results & Live IoT */}
        <div className="flex flex-col gap-6">
          
          <div className="bg-slate-800 p-6 rounded-2xl shadow-lg border border-slate-700">
            <div className="flex items-center gap-2 text-slate-400 text-xs font-semibold uppercase tracking-wider mb-4">
              <Activity size={16} /><span>Diagnosis Result</span>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 border-l-4 border-l-emerald-500 shadow-inner">
              <h3 className="text-white font-medium text-lg m-0">{diagnosisText}</h3>
            </div>
          </div>

          {contextInfo.length > 0 && (
            <div className="flex flex-col gap-3">
              {contextInfo.map((item, index) => {
                const isDanger = item.type === "danger";
                const isWarning = item.type === "warning";
                return (
                  <div key={index} className={`p-4 rounded-xl border-l-4 text-sm bg-slate-800 ${
                    isDanger ? 'border-l-red-500 text-red-400' : isWarning ? 'border-l-amber-500 text-amber-400' : 'border-l-emerald-500 text-emerald-400'
                  }`}>
                    <strong className="block mb-1 text-white">{isDanger ? "Critical" : isWarning ? "Warning" : "Normal"}</strong>
                    {item.text}
                  </div>
                );
              })}
            </div>
          )}

          <div className="bg-slate-800 p-6 rounded-2xl shadow-lg border border-slate-700 mt-auto">
            <div className="flex justify-between items-center mb-6">
              <div className="flex items-center gap-2 text-slate-400 text-xs font-semibold uppercase tracking-wider">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>Live Sensors
              </div>
              <div className="text-slate-500 text-xs font-medium bg-slate-900 px-2 py-1 rounded">
                Device: {iotData.device_id || "ESP32-01"}
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-900 rounded-xl p-4 border border-slate-800 shadow-inner">
                <span className="block text-slate-500 text-xs mb-1">Temperature</span>
                <span className="text-2xl font-bold text-white">{iotData.temperature !== null ? iotData.temperature : "--"}°C</span>
              </div>
              <div className="bg-slate-900 rounded-xl p-4 border border-slate-800 shadow-inner">
                <span className="block text-slate-500 text-xs mb-1">Humidity</span>
                <span className="text-2xl font-bold text-white">{iotData.humidity !== null ? iotData.humidity : "--"}%</span>
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* BOTTOM GRID: Historical Data Chart & Table */}
      <div className="pt-4 border-t border-slate-800">
        <h2 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
          <LineChart size={24} className="text-emerald-500" /> 
          Historical Analysis & Trends
        </h2>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Chart Panel */}
          <div className="bg-slate-800 p-6 rounded-2xl shadow-lg border border-slate-700 flex flex-col">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">Environment Trends (Last 15)</h3>
            <div className="flex-1 min-h-[250px] relative">
              <Line data={chartData} options={chartOptions} />
            </div>
          </div>

          {/* Table Panel */}
          <div className="bg-slate-800 p-6 rounded-2xl shadow-lg border border-slate-700 flex flex-col">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Data Logs</h3>
              <div className="relative">
                <Calendar size={14} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-500" />
                <input 
                  type="date" 
                  onChange={(e) => setDateFilter(e.target.value)} 
                  className="pl-9 pr-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-300 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 [color-scheme:dark]"
                />
              </div>
            </div>
            
            <div className="overflow-y-auto max-h-[250px] pr-2 rounded-lg border border-slate-700">
              <table className="w-full text-left text-sm whitespace-nowrap">
                <thead className="sticky top-0 bg-slate-900 text-slate-400 border-b border-slate-700 shadow-sm">
                  <tr>
                    <th className="px-4 py-3 font-medium">Time / Date</th>
                    <th className="px-4 py-3 font-medium">Temp</th>
                    <th className="px-4 py-3 font-medium">Humidity</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/50 bg-slate-800/50">
                  {filteredHistory.length > 0 ? (
                    filteredHistory.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-700/30 transition-colors text-slate-300">
                        <td className="px-4 py-3">{row.Timestamp || row.Date}</td>
                        <td className="px-4 py-3">{row.Temperature}°C</td>
                        <td className="px-4 py-3">{row.Humidity}%</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="3" className="px-4 py-8 text-center text-slate-500">
                        No historical records found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

        </div>
      </div>
      
    </div>
  );
}

export default Diagnosis;