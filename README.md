# 🏥 ARKUS — Sistema de Gestão e Roteirização Domiciliar

Sistema web desenvolvido para auxiliar no **gerenciamento, distribuição e monitoramento de coletas domiciliares**, integrando gestão de demandas, equipes, roteirização, visualização geográfica e indicadores operacionais.

O ARKUS foi desenvolvido como projeto acadêmico de conclusão de curso, utilizando uma arquitetura **Full-Stack**, com aplicação web, API em Python/Flask e banco de dados MySQL.

---

## 📌 Sobre o projeto

O ARKUS surgiu com o objetivo de centralizar e organizar o fluxo de coletas domiciliares, permitindo que as demandas sejam cadastradas, distribuídas entre profissionais disponíveis e acompanhadas por meio de diferentes painéis operacionais.

A aplicação integra três camadas principais:

* **Front-end:** interface utilizada pelos operadores para gerenciamento e acompanhamento das informações.
* **Back-end:** API desenvolvida em Python com Flask, responsável pelas regras de negócio, processamento e distribuição das demandas.
* **Banco de dados:** MySQL, responsável pela persistência e organização das informações do sistema.

---

## ⚙️ Principais funcionalidades

### 📋 Gestão de demandas

* Cadastro manual de solicitações.
* Importação de demandas por arquivo CSV.
* Consulta e acompanhamento das solicitações.
* Controle de status das demandas.
* Organização das informações de pacientes, endereços e horários.

### 👥 Gestão de equipes

* Cadastro de técnicos.
* Cadastro de motoboys.
* Controle de matrícula.
* Definição de horários de trabalho.
* Importação de listas de profissionais.
* Identificação dos profissionais disponíveis para atendimento.

### 🚚 Roteirização e distribuição

* Geração das rotas do dia.
* Distribuição das demandas entre profissionais disponíveis.
* Organização das coletas por sequência de atendimento.
* Organização das retiradas realizadas pelos motoboys.
* Identificação de pendências de alocação.
* Reprocessamento das rotas quando necessário.

### 🗺️ Monitoramento geográfico

* Visualização das demandas em mapa.
* Distribuição geográfica das solicitações.
* Identificação das regiões com maior concentração de demandas.
* Consulta das informações associadas aos pontos de atendimento.

### 📊 Dashboard gerencial

* Monitoramento da capacidade operacional.
* Indicadores de ocupação.
* Produtividade operacional.
* Disponibilidade de vagas.
* Análise de demanda por turno.
* Identificação de zonas de alta demanda.
* Balanço geral da capacidade de atendimento.

---

## 🖥️ Principais telas

> *As imagens abaixo serão adicionadas ao repositório posteriormente.*

### 📊 Dashboard Gerencial

**Painel de acompanhamento dos principais indicadores operacionais.**

`[ imagem do dashboard ]`

---

### 📋 Agendamentos

**Tela responsável pelo cadastro, importação e acompanhamento das demandas.**

`[ imagem de agendamentos ]`

---

### 👥 Gestão de Equipe

**Gerenciamento dos técnicos e motoboys disponíveis para atendimento.**

`[ imagem de gestão de equipe ]`

---

### 🚚 Rotas

**Painel de distribuição e organização das coletas e retiradas.**

`[ imagem de rotas ]`

---

### 🗺️ Mapa de Rotas

**Visualização geográfica das demandas e pontos de atendimento.**

`[ imagem do mapa ]`

---

## 🔄 Fluxo do sistema

O funcionamento do ARKUS pode ser representado de forma simplificada:

```text
Demandas
   │
   ▼
Agendamentos
   │
   ▼
Profissionais disponíveis
   │
   ▼
Distribuição das demandas
   │
   ▼
Geração das rotas
   │
   ├──────────────► Mapa de Rotas
   │
   ▼
Acompanhamento operacional
   │
   ▼
Dashboard e indicadores
```

---

## 🧩 Arquitetura

```text
┌─────────────────────────────────┐
│            FRONT-END            │
│      HTML • CSS • JavaScript    │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│            BACK-END             │
│          Python • Flask         │
│                                 │
│ • API                           │
│ • Regras de negócio             │
│ • Distribuição de demandas      │
│ • Processamento das rotas       │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│           BANCO DE DADOS        │
│              MySQL              │
│                                 │
│ • Demandas                      │
│ • Profissionais                 │
│ • Agendamentos                  │
│ • Rotas                         │
└─────────────────────────────────┘
```

---

## 🛠️ Tecnologias utilizadas

| Tecnologia             | Utilização                                |
| ---------------------- | ----------------------------------------- |
| **Python**             | Desenvolvimento do back-end               |
| **Flask**              | Construção da API e integração do sistema |
| **MySQL**              | Banco de dados relacional                 |
| **HTML5**              | Estrutura das interfaces                  |
| **CSS3**               | Estilização das interfaces                |
| **JavaScript**         | Interatividade e integração das telas     |
| **GitHub**             | Versionamento e armazenamento do projeto  |
| **Visual Studio Code** | Ambiente de desenvolvimento               |

---

## 📁 Estrutura do projeto

```text
ARKUS/
│
├── backend/
│   └── API, conexão com banco e lógica de roteirização
│
├── database/
│   └── Estrutura e modelagem do banco de dados MySQL
│
├── front-end/
│   └── Interfaces, dashboards e funcionalidades visuais
│
└── README.md
```

---

## 🚀 Evolução do projeto

O ARKUS foi desenvolvido de forma incremental, evoluindo desde a estruturação dos dados e gerenciamento das demandas até a integração entre interface, back-end, banco de dados e funcionalidades de distribuição.

Entre as funcionalidades desenvolvidas estão:

* Estruturação do banco de dados.
* Gestão de demandas.
* Gestão de equipes.
* Integração entre front-end e back-end.
* Distribuição automática das demandas.
* Geração e organização de rotas.
* Visualização geográfica.
* Dashboard de indicadores operacionais.

---

## 🔮 Próximos passos

Entre as possibilidades de evolução do projeto estão:

* Aprimoramento da otimização geográfica das rotas.
* Evolução dos indicadores operacionais.
* Expansão dos recursos de monitoramento.
* Melhorias na análise de capacidade e produtividade.

---

## 🎓 Projeto acadêmico

Projeto desenvolvido para fins acadêmicos como parte da formação em **Análise e Desenvolvimento de Sistemas — 2026**.

### 👩‍💻 Desenvolvedora

**Laís dos Reis**

Projeto desenvolvido individualmente.

---

## 📄 Licença

Projeto desenvolvido para fins acadêmicos e de portfólio.
