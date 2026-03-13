CREATE DATABASE IF NOT EXISTS arkus_db;
USE arkus_db;

CREATE TABLE IF NOT EXISTS coletas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255),
    endereco VARCHAR(255),
    turno VARCHAR(50),
    tipo VARCHAR(50),
    data_agendamento DATE,
    preferencia_horario VARCHAR(50)
);
