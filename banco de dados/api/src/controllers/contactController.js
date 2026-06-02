const Contact = require('../models/contactModel');

exports.createContact = async (req, res) => {
  const { company_name, contact_name, email } = req.body;

  if (!company_name || !contact_name || !email) {
    return res.status(400).json({ error: 'Campos obrigatórios ausentes' });
  }

  try {
    const id = await Contact.create(req.body);
    res.status(201).json({ success: true, id });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Erro ao salvar contato' });
  }
};
