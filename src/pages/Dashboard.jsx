function Dashboard() {
    return (
      <div>
        <h2>Dashboard</h2>
        <div style={{ display: "flex", gap: "20px", marginTop: "20px" }}>
          <div style={cardStyle}>Total Cattle: 120</div>
          <div style={cardStyle}>Avg Temp: 38.5°C</div>
          <div style={cardStyle}>Humidity: 67%</div>
        </div>
      </div>
    );
  }
  
  const cardStyle = {
    padding: "20px",
    background: "#e2e8f0",
    borderRadius: "10px"
  };
  
  export default Dashboard;