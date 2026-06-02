const mysql = require('mysql2/promise');
const fs = require('fs');

// lê a senha do secret
const DB_PASSWORD = fs.readFileSync('/run/secrets/db_app_password', 'utf8').trim();

const pool = mysql.createPool({
    host: process.env.DB_HOST || 'localhost',
    user: process.env.DB_USER || 'brlia_app',
    password: DB_PASSWORD,
    database: process.env.DB_NAME || 'brlia_prod',
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0
});

module.exports = pool;

