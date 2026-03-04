import { useEffect, useState } from "react";

function Monitoring() {
  const [temperature, setTemperature] = useState(0);
  const [humidity, setHumidity] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      // Replace with API call
      setTemperature((38 + Math.random()).toFixed(2));
      setHumidity((60 + Math.random() * 10).toFixed(2));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <h2>Real-Time Monitoring</h2>
      <p>Temperature: {temperature}°C</p>
      <p>Humidity: {humidity}%</p>
    </div>
  );
}

export default Monitoring;