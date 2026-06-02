const express = require('express');
const router = express.Router();
const pool = require('../db');

// POST /api/contacts
router.post('/', async (req, res) => {
    try {
        const { company_name, segment, contact_name, position, email, phone, message } = req.body;

        // Inserir no banco
        const [result] = await pool.query(
            `INSERT INTO contacts (company_name, segment, contact_name, position, email, phone, message)
             VALUES (?, ?, ?, ?, ?, ?, ?)`,
            [company_name, segment, contact_name, position, email, phone, message]
        );

        res.json({ success: true, id: result.insertId });
    } catch (err) {
        console.error(err);
        res.json({ success: false, error: err.message });
    }
});

module.exports = router;
