# 🏥 ARKUS — Sistema de Gestão e Roteirização Domiciliar

O ARKUS é um sistema web desenvolvido como projeto acadêmico de conclusão de curso para apoiar a **organização de coletas domiciliares**, centralizando demandas, equipes e rotas em uma única aplicação.

A solução permite cadastrar e importar solicitações, gerenciar profissionais disponíveis, distribuir atendimentos, organizar rotas, visualizar demandas em mapa e acompanhar indicadores operacionais por meio de dashboard.

O projeto foi desenvolvido em arquitetura **Full-Stack**, utilizando:

* **Front-end:** HTML, CSS e JavaScript
* **Back-end:** Python com Flask
* **Banco de dados:** MySQL

---

## ⚙️ Principais funcionalidades

### 📋 Gestão de demandas
- Cadastro manual de solicitações
- Importação de demandas por CSV
- Consulta e acompanhamento de status
- Organização de informações de atendimento

### 👥 Gestão de equipes
- Cadastro de técnicos e motoboys
- Definição de horários de trabalho
- Importação de profissionais
- Identificação de disponibilidade

### 🚚 Distribuição e rotas
- Distribuição de demandas entre profissionais disponíveis
- Geração e organização das rotas do dia
- Sequenciamento dos atendimentos
- Identificação de pendências de alocação
- Reprocessamento das rotas quando necessário

### 🗺️ Visualização geográfica
- Exibição das demandas em mapa
- Consulta dos pontos de atendimento
- Visualização da distribuição geográfica das solicitações

### 📊 Dashboard
- Acompanhamento de capacidade operacional
- Indicadores de ocupação e produtividade
- Análise de demanda por turno
- Visão geral da capacidade de atendimento

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

## 🔮 Possíveis evoluções

Como possibilidades de evolução futura do projeto:

- Aprimoramento da otimização geográfica das rotas
- Evolução dos indicadores operacionais
- Expansão dos recursos de monitoramento
- Melhorias na análise de capacidade e produtividade

---

## 🎓 Projeto acadêmico

Projeto desenvolvido como parte da formação em **Análise e Desenvolvimento de Sistemas — 2026**.

### 👩‍💻 Desenvolvedora

**Laís dos Reis**

Projeto desenvolvido para fins acadêmicos e de portfólio.
