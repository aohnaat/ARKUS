CREATE DATABASE IF NOT EXISTS arkus_db;
USE arkus_db;

CREATE TABLE IF NOT EXISTS coletas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    endereco VARCHAR(255) NOT NULL,
    turno VARCHAR(50),
    tipo VARCHAR(50),
    preferencia_horario VARCHAR(50),
    data_agendamento DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'Pendente'
);

CREATE TABLE IF NOT EXISTS tecnicos (
    matricula VARCHAR(50) PRIMARY KEY,
    nome_completo VARCHAR(255) NOT NULL,
    horario_trabalho VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS motoboys (
    cpf VARCHAR(20) PRIMARY KEY,
    nome_completo VARCHAR(255) NOT NULL,
    placa_veiculo VARCHAR(20),
    horario_trabalho VARCHAR(100)
);
