2 MILHÕES P K > MARGEM DE VENDA (50MILHÕES ~ 200MILHÕES)

DEPENDÊNCIAS

node -v > verifica a instalacao do node
mysql -u root -p > testa a conexão sql

--------------------------------------------------------------------

CRIAÇÃO DO DATABASE

CREATE DATABASE contacts_db;

USE contacts_db;

CREATE TABLE contact_requests (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    segment VARCHAR(100),
    employee_range VARCHAR(50),
    contact_name VARCHAR(255) NOT NULL,
    position VARCHAR(100),
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    message TEXT,
    status ENUM('new', 'contacted', 'closed') DEFAULT 'new',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

------------------------------------------------------------------------------

CRIANDO PROJETO NO NODE.JS

mkdir api-contacts
cd api-contacts
npm init -y

INSTALANDO DEPENDÊNCIAS DO NODE.JS

npm install express mysql2 dotenv cors

-------------------------------------------------------------------------------

.env > trocar a senha pela senha do mysql

PORT=3000
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=sua_senha
DB_NAME=contacts_db

-------------------------------------------------------------------------------

RODAR API

node src/server.js >>> http://localhost:3000/api/contacts

-------------------------------------------------------------------------------
npm init -y
npm install express mysql2 dotenv

-------------------------------------------------------------------------------

Frontend envia JSON
         ↓
API Routes (/api/contacts)
         ↓
Controller valida e chama Model
         ↓
Model executa INSERT no MySQL
         ↓
Registro criado na tabela contact_requests
         ↓
API retorna { success: true, id }

----------------------------------------------------------------------------

api/
├── src/
│   ├── config/
│   │   └── database.js        # Conexão com MySQL
│   ├── models/
│   │   └── contactModel.js    # Função de INSERT
│   ├── controllers/
│   │   └── contactController.js
│   ├── routes/
│   │   └── contactRoutes.js
│   ├── app.js                 # Configuração do Express
│   └── server.js              # Inicializa o servidor
├── .env                       # Variáveis de ambiente
├── package.json
└── README.md

----------------------------------------------------------------------------

TABELA SQL

CREATE TABLE contact_requests (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    segment VARCHAR(100),
    employee_range VARCHAR(50),
    contact_name VARCHAR(255) NOT NULL,
    position VARCHAR(100),
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    message TEXT,
    status ENUM('new', 'contacted', 'closed') DEFAULT 'new',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-----------------------------------------------------------------------------

CONSULTA DO SQL

-- Todos os contatos
SELECT * FROM contact_requests;

-- Contatos novos
SELECT * FROM contact_requests WHERE status = 'new';

-- Atualizar status
UPDATE contact_requests
SET status = 'contacted'
WHERE id = 1;

------------------------------------------------------

2 MILHÕES P K > MARGEM DE VENDA (50MILHÕES ~ 200MILHÕES)