google.charts.load("current", { packages: ["table"] });
google.charts.setOnLoadCallback(fetchAndDrawTable);

const url = "http://localhost:3000/api/sensor"; // Update with your server's IP address

// Function to prepare database data for Google Charts
function prepareDataForTable(databaseData) {
  // Check if data exists
  if (!databaseData || !databaseData.data || databaseData.data.length === 0) {
    console.log("No data available");
    return [];
  }

  // Transform database records into chart-ready format
  const preparedData = databaseData.data.map((record) => ({
    time: record.timestamp,
    angle: record.angle,
    measure: record.measure_cm,
  }));

  return preparedData;
}

// Fetch data and draw table
function fetchAndDrawTable() {
  fetch(url)
    .then((response) => response.json())
    .then((data) => {
      // Prepare the data for the table
      const measurements = prepareDataForTable(data);

      // Draw the table with prepared data
      drawTable(measurements);
    })
    .catch((error) => {
      console.error("Error fetching data:", error);
    });
}

function drawTable(measurements) {
  var data = new google.visualization.DataTable();
  data.addColumn("string", "Time");
  data.addColumn("number", "Angle");
  data.addColumn("number", "Measure (cm)");

  // Add rows from measurements
  if (measurements && measurements.length > 0) {
    measurements.forEach((measurement) => {
      data.addRow([measurement.time, measurement.angle, measurement.measure]);
    });
  }

  var options = {
    showRowNumbers: true,
    width: "100%",
    height: "100%",
  };

  var table = new google.visualization.Table(
    document.getElementById("table_div")
  );

  table.draw(data, options);
}
