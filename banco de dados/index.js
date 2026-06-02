const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const contactsRouter = require('./routes/contacts');

const app = express();
const PORT = 3000;

// Middlewares
app.use(cors());
app.use(bodyParser.json());

// Rotas
app.use('/api/contacts', contactsRouter);

// Healthcheck
app.get('/health', (req, res) => res.send('API rodando'));

// Start
app.listen(PORT, () => {
    console.log(`API rodando na porta ${PORT}`);
});
