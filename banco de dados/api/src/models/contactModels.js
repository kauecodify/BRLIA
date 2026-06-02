const db = require('../config/database');

exports.create = async (data) => {
  const {
    company_name,
    segment,
    employee_range,
    contact_name,
    position,
    email,
    phone,
    message
  } = data;

  const [result] = await db.execute(
    `INSERT INTO contact_requests
     (company_name, segment, employee_range, contact_name, position, email, phone, message)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
    [
      company_name,
      segment,
      employee_range,
      contact_name,
      position,
      email,
      phone,
      message
    ]
  );

  return result.insertId;
};
