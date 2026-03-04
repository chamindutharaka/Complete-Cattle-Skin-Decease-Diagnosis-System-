import { useState } from "react";

function Severity() {
  const [level, setLevel] = useState(null);

  const checkSeverity = () => {
    setLevel("Moderate"); // Replace with API call
  };

  return (
    <div>
      <h2>Severity Analysis</h2>
      <button onClick={checkSeverity}>Analyze Severity</button>

      {level && <p>Severity Level: {level}</p>}
    </div>
  );
}

export default Severity;