CREATE DATABASE IF NOT EXISTS arkus_db;
USE arkus_db;

CREATE TABLE IF NOT EXISTS coletas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    endereco VARCHAR(255) NOT NULL,
    turno VARCHAR(50),
    tipo VARCHAR(100),
    preferencia_horario VARCHAR(50),
    data_agendamento DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'Pendente'
);
