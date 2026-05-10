CREATE DATABASE arkus_db;
USE arkus_db;

CREATE TABLE tecnicos (
    matricula VARCHAR(50) PRIMARY KEY,
    nome_completo VARCHAR(255),
    horario_trabalho VARCHAR(100)
);

CREATE TABLE motoboys (
    cpf VARCHAR(20) PRIMARY KEY,
    nome_completo VARCHAR(255),
    placa_veiculo VARCHAR(20),
    horario_trabalho VARCHAR(100)
);

CREATE TABLE coletas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255),
    endereco TEXT,
    turno VARCHAR(50),
    tipo VARCHAR(50),
    preferencia_horario VARCHAR(50),
    data_agendamento DATE,
    status VARCHAR(50),
    tecnico_id VARCHAR(50),
    longitude DECIMAL(11,8),
    latitude DECIMAL(10,8),
    ordem_rota INT,
    motoboy_id VARCHAR(50),

    CONSTRAINT fk_tecnico
        FOREIGN KEY (tecnico_id)
        REFERENCES tecnicos(matricula)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

    CONSTRAINT fk_motoboy
        FOREIGN KEY (motoboy_id)
        REFERENCES motoboys(cpf)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);
