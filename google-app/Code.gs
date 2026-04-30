function onFormSubmit(e) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
  const row = e.range.getRow();

  const name   = sheet.getRange(row, COL_NAME).getValue();
  const email  = sheet.getRange(row, COL_EMAIL).getValue();
  const adults = parseInt(sheet.getRange(row, COL_ADULTS).getValue()) || 0;
  const kids   = parseInt(sheet.getRange(row, COL_KIDS).getValue()) || 0;
  const total  = adults * PRICE_ADULT + kids * PRICE_KID;
  const code   = Math.random().toString(36).substr(2, 8).toUpperCase();

  sheet.getRange(row, COL_CODE).setValue(code);
  sheet.getRange(row, COL_TOTAL).setValue(total);

  sendRegistrationEmail(name, email, adults, kids, total, code);
}

function checkAndSendPendingTickets() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
  const lastRow = sheet.getLastRow();

  for (let row = 2; row <= lastRow; row++) {
    const paid = sheet.getRange(row, COL_PAID).getValue();
    const sent = sheet.getRange(row, COL_SENT).getValue();
    if (paid === true && sent !== true) {
      sendTicketEmail(sheet, row);
      sheet.getRange(row, COL_SENT).setValue(true);
    }
  }
}
