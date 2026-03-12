# 🏥 Projeto ARKUS - Sistema de Roteirização 

O **ARKUS** é uma solução de roteirização e gestão de demandas laboratoriais. O objetivo do sistema é organizar a coleta de exames domiciliares, permitindo que gestores controlem pedidos manuais e em lote, distribuindo-os de forma eficiente para as equipes técnicas.

---

## 📋 Escopo do Projeto (Sprint 1 - AC1)

Nesta primeira etapa, focamos na base de dados e na interface de entrada de informações:

1.  **Cadastro de Demandas em Lote:** Importação de arquivos CSV para processamento rápido de grandes volumes de pacientes.
2.  **Cadastro Manual:** Interface intuitiva para inserção de casos isolados ou emergenciais.
3.  **Visualização Dinâmica:** Filtro por calendário que permite ao gestor navegar entre os dias de atendimento.
4.  **Arquitetura Relacional:** Persistência de dados em servidor MySQL.

---

## 🛠️ Tecnologias e Arquitetura

O projeto foi construído utilizando uma arquitetura cliente-servidor para garantir escalabilidade e segurança:

* **Front-end:** HTML5, CSS3 e JavaScript (Vanila).
* **Back-end:** Python 3.14 com Framework Flask.
* **Banco de Dados:** MySQL Workbench (Banco Relacional).
* **Conectores:** `pymysql` e `cryptography` para autenticação segura.

---

## 🚀 Próximas Etapas (AC2 & Final)

O cronograma de desenvolvimento está dividido em 4 marcos principais:

1.  **[CONCLUÍDO]** Cadastro de demandas em lote e manual com persistência em MySQL.
2.  **[PRÓXIMO]** Módulo de Cadastro dos Técnicos (Gestão de RH e frotas).
3.  **[EM DESENVOLVIMENTO]** Triagem e confirmação da distribuição das rotas (Vínculo entre técnico e paciente).
4.  **[FINAL]** Dashboard de visualização das rotas otimizadas e Tela de Login para autenticação de gestores.

---

## ⚙️ Como executar o projeto

1. **Requisitos:** Certifique-se de ter o Python e o MySQL instalados.
2. **Dependências:**
   ```bash
   pip install flask flask-cors pymysql pandas cryptography
