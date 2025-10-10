function sendNewLeadsToCRM() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0]; 
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return; // no data beyond header row

  const dataRange = sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn()); // skip header
  const data = dataRange.getValues();

  for (let i = 0; i < data.length; i++) {
    let row = data[i];
    // Check if already sent (assumes last column is "status")
    if (row[15] === "SENT") {
      continue;
    }

    // ⚠️ Adjust indexes (0-based)
    let fullName = row[12];  // Column 12 (FULL_NAME)
    let phone    = row[13];  // Column 13 (PHONE)
    let city     = row[14];  // Column 14 (CITY)
    let origin   = row[9];   // Column 9  (ORIGIN)
    let platform = row[11];
    origin = origin + " " + platform;
    
    // Cleanup phone number → remove "p:+"
    if (phone && typeof phone === "string") {
      phone = phone.replace(/^p:\+/, "").trim();
    }

    // Prepare payload
    let payload = {
      CITY: city,
      ORIGIN: origin,
      PHONE: phone,
      FULL_NAME: fullName
    };

    // POST request
    let options = {
      method: "post",
      payload: payload // sent as x-www-form-urlencoded
    };

    try {
      let response = UrlFetchApp.fetch("https://crm.monarchbuildestate.com/facebook/lead/add", options);
      Logger.log("✅ Sent row " + (i + 2) + ": " + response.getContentText());

      // Mark row as processed
      sheet.getRange(i + 2, sheet.getLastColumn()).setValue("SENT");

    } catch (err) {
      Logger.log("❌ Error sending row " + (i + 2) + ": " + err);
    }
  }
}
