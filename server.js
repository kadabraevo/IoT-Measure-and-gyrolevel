const express = require("express");
const sqlite3 = require("sqlite3");
const app = express();
const port = 3000;

// Enable CORS for all routes
app.use((req, res, next) => {
  res.header("Access-Control-Allow-Origin", "*");
  res.header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE");
  res.header("Access-Control-Allow-Headers", "Content-Type");
  next();
});

const db = new sqlite3.Database("sensor_data.db", (err) => {
  if (err) {
    console.error("Error opening database:", err.message);
  } else {
    console.log("Connected to the SQLite database.");
  }
});

db.run(
  "CREATE TABLE IF NOT EXISTS sensor_data (id INTEGER PRIMARY KEY AUTOINCREMENT, measure_cm INT, angle INT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)",
  (err) => {
    if (err) {
      console.error("Error creating table:", err.message);
    }
  }
);

// GET endpoint
app.get("/api/sensor", (req, res) => {
  console.log("GET /api/sensor endpoint hit");
  db.all("SELECT * FROM sensor_data", [], (err, rows) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    res.json({ data: rows });
  });
});

app.post("/api/sensor", (req, res) => {
  console.log("POST /api/sensor endpoint hit");
  const { measure_cm, angle } = req.query;
  db.run(
    "INSERT INTO sensor_data (measure_cm, angle) VALUES (?, ?)",
    [measure_cm, angle],
    function (err) {
      if (err) {
        return res.status(500).json({ error: err.message });
      }
      res.json({ message: "Data inserted successfully" });
    }
  );
});

// Trigger endpoint for remote measurement
let triggerFlag = false;

app.get("/api/trigger", (req, res) => {
  console.log("GET /api/trigger - Trigger requested");
  triggerFlag = true;
  res.json({ message: "Measurement trigger activated" });
});

app.get("/api/check-trigger", (req, res) => {
  console.log("GET /api/check-trigger - Pico checking for trigger");
  const shouldTrigger = triggerFlag;
  triggerFlag = false; // Reset flag after reading
  res.json({ trigger: shouldTrigger });
});

app.listen(port, () => {
  console.log(`Server running at
http://localhost:${port}`);
});
