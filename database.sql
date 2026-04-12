CREATE DATABASE IF NOT EXISTS arkus_db;
USE arkus_db;

CREATE TABLE IF NOT EXISTS coletas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    data_coleta DATE NOT NULL,
    cliente VARCHAR(255) NOT NULL,
    endereco VARCHAR(255) NOT NULL,
    bairro VARCHAR(100),
    status VARCHAR(50) DEFAULT 'Pendente'
);

CREATE TABLE IF NOT EXISTS tecnicos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    matricula VARCHAR(50) UNIQUE NOT NULL,
    turno VARCHAR(50),
    especialidade VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS motoboys (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    placa_veiculo VARCHAR(10),
    disponibilidade BOOLEAN DEFAULT TRUE
);