from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql
import pymysql
import csv
import io
import math
import random
import re
import traceback
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

def obter_coordenadas(endereco):
    lat_mock = -23.5505 + random.uniform(-0.05, 0.05)
    lon_mock = -46.6333 + random.uniform(-0.05, 0.05)
    return lat_mock, lon_mock

def calc_distancia(lat1, lon1, lat2, lon2):
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 999999
    return math.sqrt((float(lat2) - float(lat1))**2 + (float(lon2) - float(lon1))**2)

def get_db():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='1945',
        database='arkus_db',
        cursorclass=pymysql.cursors.DictCursor
    )

def init_db():
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    usuario VARCHAR(255) UNIQUE NOT NULL,
                    senha VARCHAR(255) NOT NULL
                )
            """)
        db.commit()
    except Exception as e:
        print("Erro ao criar tabela de usuarios:", e)
    finally:
        db.close()

@app.route('/api/cadastro', methods=['POST'])
def api_cadastro():
    data = request.json
    usuario = data.get('usuario')
    senha = data.get('senha')

    if not usuario or not senha:
        return jsonify({"sucesso": False, "mensagem": "Preencha todos os campos!"}), 400

    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM usuarios WHERE usuario = %s", (usuario,))
            if cursor.fetchone():
                return jsonify({"sucesso": False, "mensagem": "Este e-mail já está em uso."}), 400
            
            cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (%s, %s)", (usuario, senha))
        db.commit()
        return jsonify({"sucesso": True, "mensagem": "Conta criada com sucesso!"}), 201
    except Exception as e:
        return jsonify({"sucesso": False, "mensagem": f"Erro interno: {str(e)}"}), 500
    finally:
        db.close()

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    usuario = data.get('usuario')
    senha = data.get('senha')

    if usuario == 'admin' and senha == '123456':
        return jsonify({"sucesso": True, "mensagem": "Login aprovado"}), 200

    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM usuarios WHERE usuario = %s AND senha = %s", (usuario, senha))
            user = cursor.fetchone()
            
            if user:
                return jsonify({"sucesso": True, "mensagem": "Login aprovado"}), 200
            else:
                return jsonify({"sucesso": False, "mensagem": "Usuário ou senha incorretos!"}), 401
    except Exception as e:
        return jsonify({"sucesso": False, "mensagem": f"Erro interno: {str(e)}"}), 500
    finally:
        db.close()

@app.route('/listar_coletas', methods=['GET'])
def listar_coletas():
    data_filtro = request.args.get('data')
    ordem = request.args.get('ordem', 'ASC').upper()

    if ordem not in ['ASC', 'DESC']:
        ordem = 'ASC'

    db = get_db()
    try:
        with db.cursor() as cursor:
            if data_filtro:
                cursor.execute(
                    f"""
                    SELECT * FROM coletas
                    WHERE data_agendamento = %s
                    ORDER BY data_agendamento {ordem}, preferencia_horario ASC
                    """,
                    (data_filtro,)
                )
            else:
                cursor.execute(
                    f"""
                    SELECT * FROM coletas
                    ORDER BY data_agendamento {ordem}, preferencia_horario ASC
                    """
                )
            return jsonify(cursor.fetchall()), 200
    finally:
        db.close()

@app.route('/importar/<destino>', methods=['POST'])
def importar(destino):
    if 'file' not in request.files:
        return jsonify({"message": "Arquivo ausente"}), 400

    file = request.files['file']
    content = file.stream.read().decode("utf-8-sig").strip()

    stream = io.StringIO(content)
    csv_input = list(csv.DictReader(stream, skipinitialspace=True))

    db = get_db()
    try:
        with db.cursor() as cursor:
            if destino == 'coletas':
                dados_em_lote = []
                for row in csv_input:
                    lat = row.get('latitude') if row.get('latitude') else obter_coordenadas(row.get('endereco'))[0]
                    lon = row.get('longitude') if row.get('longitude') else obter_coordenadas(row.get('endereco'))[1]
                    
                    dados_em_lote.append((
                        row.get('nome'),
                        row.get('endereco'),
                        row.get('turno'),
                        row.get('tipo'),
                        row.get('preferencia_horario'),
                        row.get('data_agendamento'),
                        'Pendente',
                        float(lat),
                        float(lon)
                    ))

                cursor.executemany("""
                    INSERT INTO coletas (
                        nome, endereco, turno, tipo, preferencia_horario,
                        data_agendamento, status, latitude, longitude
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, dados_em_lote)

            elif destino == 'tecnico':
                cursor.executemany("""
                    INSERT INTO tecnicos (matricula, nome_completo, horario_trabalho)
                    VALUES (%s, %s, %s)
                """, [(r.get('matricula'), r.get('nome_completo'), r.get('horario_trabalho')) for r in csv_input])

            elif destino == 'motoboy':
                cursor.executemany("""
                    INSERT INTO motoboys (cpf, nome_completo, placa_veiculo, horario_trabalho)
                    VALUES (%s, %s, %s, %s)
                """, [(r.get('cpf'), r.get('nome_completo'), r.get('placa_veiculo'), r.get('horario_trabalho')) for r in csv_input])

        db.commit()
        return jsonify({"message": f"{len(csv_input)} registros processados com sucesso!"}), 201
    except Exception as e:
        traceback.print_exc()
        return jsonify({"message": str(e)}), 500
    finally:
        db.close()

def executar_algoritmo_roteirização(tipo_servico, equipe, lista_tarefas_dia, lista_update):
    if not equipe: return

    tarefas = [t for t in lista_tarefas_dia if t.get('tipo') == tipo_servico]
    
    def extract_time(val):
        from datetime import timedelta
        if isinstance(val, timedelta):
            total_sec = int(val.total_seconds())
            h = total_sec // 3600
            m = (total_sec % 3600) // 60
            return datetime.strptime(f"{h:02d}:{m:02d}", "%H:%M")
        elif isinstance(val, str):
            parts = val.split(':')
            if len(parts) >= 2:
                h, m = int(parts[0]), int(parts[1])
                return datetime.strptime(f"{h:02d}:{m:02d}", "%H:%M")
        return datetime.strptime("00:00", "%H:%M")

    tarefas.sort(key=lambda t: extract_time(t.get('preferencia_horario')))

    agendas = { (p.get('matricula') or p.get('cpf')): [] for p in equipe }
    ordem_por_profissional = { (p.get('matricula') or p.get('cpf')): 1 for p in equipe }

    for tarefa in tarefas:
        h_tarefa = extract_time(tarefa.get('preferencia_horario'))
        equipe_balanceada = sorted(equipe, key=lambda p: len(agendas[p.get('matricula') or p.get('cpf')]))

        for prof in equipe_balanceada:
            p_id = prof.get('matricula') or prof.get('cpf')
            horario_str = str(prof.get('horario_trabalho', '00:00 - 23:59'))
            
            try:
                inicio_str, fim_str = horario_str.split('-')
                h_inicio = datetime.strptime(inicio_str.strip(), "%H:%M").time()
                h_fim = datetime.strptime(fim_str.strip(), "%H:%M").time()
            except Exception:
                h_inicio = datetime.strptime("00:00", "%H:%M").time()
                h_fim = datetime.strptime("23:59", "%H:%M").time()

            if not (h_inicio <= h_tarefa.time() < h_fim):
                continue

            conflito = False
            for h_agendada in agendas[p_id]:
                diff_minutos = abs((h_tarefa - h_agendada).total_seconds()) / 60
                if diff_minutos < 60:
                    conflito = True
                    break

            if not conflito:
                agendas[p_id].append(h_tarefa)
                lista_update.append((p_id, ordem_por_profissional[p_id], tarefa['id']))
                ordem_por_profissional[p_id] += 1
                break 

@app.route('/gerar_rotas_pendentes', methods=['POST'])
def gerar_rotas_pendentes():
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM coletas WHERE (tecnico_id IS NULL OR tecnico_id = '') AND (motoboy_id IS NULL OR motoboy_id = '')")
            pendentes = cursor.fetchall()
            
            cursor.execute("SELECT matricula as id, horario_trabalho FROM tecnicos")
            tecnicos = cursor.fetchall()
            
            cursor.execute("SELECT cpf as id, horario_trabalho FROM motoboys")
            motoboys = cursor.fetchall()
            
            alocados = 0
            
            for paciente in pendentes:
                horario_paciente = paciente.get('preferencia_horario')
                if not horario_paciente:
                    continue
                    
                try:
                    if isinstance(horario_paciente, timedelta):
                        total_sec = int(horario_paciente.total_seconds())
                        h, m = total_sec // 3600, (total_sec % 3600) // 60
                        h_tarefa = datetime.strptime(f"{h:02d}:{m:02d}", "%H:%M").time()
                    else:
                        parts = str(horario_paciente).split(':')
                        h_tarefa = datetime.strptime(f"{int(parts[0]):02d}:{int(parts[1]):02d}", "%H:%M").time()
                except Exception:
                    continue

                data_paciente = paciente['data_agendamento']
                tipo_demanda = paciente['tipo']
                
                equipe = tecnicos if tipo_demanda == 'Coleta' else motoboys
                coluna_fk = 'tecnico_id' if tipo_demanda == 'Coleta' else 'motoboy_id'
                
                profissional_escolhido = None
                
                for prof in equipe:
                    horario_str = str(prof.get('horario_trabalho', '00:00 - 23:59'))
                    try:
                        inicio_str, fim_str = horario_str.split('-')
                        h_inicio = datetime.strptime(inicio_str.strip(), "%H:%M").time()
                        h_fim = datetime.strptime(fim_str.strip(), "%H:%M").time()
                    except Exception:
                        h_inicio = datetime.strptime("00:00", "%H:%M").time()
                        h_fim = datetime.strptime("23:59", "%H:%M").time()
                        
                    if not (h_inicio <= h_tarefa < h_fim):
                        continue
                        
                    query_conflito = f"""
                        SELECT 1 FROM coletas 
                        WHERE data_agendamento = %s 
                          AND {coluna_fk} = %s
                          AND ABS(TIME_TO_SEC(TIMEDIFF(preferencia_horario, %s))) < 3600
                        LIMIT 1
                    """
                    cursor.execute(query_conflito, (data_paciente, prof['id'], str(horario_paciente)))
                    if cursor.fetchone():
                        continue 
                        
                    profissional_escolhido = prof['id']
                    break
                    
                if profissional_escolhido:
                    query_ordem = """
                        SELECT COALESCE(MAX(ordem_rota), 0) + 1 as proxima_ordem 
                        FROM coletas 
                        WHERE data_agendamento = %s AND (tecnico_id = %s OR motoboy_id = %s)
                    """
                    cursor.execute(query_ordem, (data_paciente, profissional_escolhido, profissional_escolhido))
                    nova_ordem = cursor.fetchone()['proxima_ordem']
                    
                    query_update = f"""
                        UPDATE coletas 
                        SET {coluna_fk} = %s, ordem_rota = %s, status = 'Roteirizado' 
                        WHERE id = %s
                    """
                    cursor.execute(query_update, (profissional_escolhido, nova_ordem, paciente['id']))
                    alocados += 1
                    
        db.commit()
        if alocados > 0:
            msg = f"Varredura global concluída! {alocados} novas demandas foram alocadas."
        else:
            msg = "Varredura concluída! Nenhuma pendência pôde ser alocada."
            
        return jsonify({"message": msg})
    
    except Exception as e:
        print(f"Erro Crítico: {str(e)}")
        db.rollback()
        return jsonify({"error": "Erro no servidor ao processar as rotas"}), 500
    finally:
        db.close()
        
@app.route('/gerar_todas_rotas', methods=['POST'])
def gerar_todas_rotas():
    data = request.json
    data_inicio = data.get('data_inicio')
    
    if not data_inicio:
        return jsonify({"message": "Data de partida não informada!"}), 400

    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                UPDATE coletas
                SET tecnico_id = NULL, motoboy_id = NULL, ordem_rota = NULL, status = 'Pendente'
                WHERE data_agendamento >= %s
            """, (data_inicio,))
            
            cursor.execute("SELECT DISTINCT data_agendamento FROM coletas WHERE data_agendamento >= %s ORDER BY data_agendamento ASC", (data_inicio,))
            todas_datas = cursor.fetchall()

            if not todas_datas:
                return jsonify({"message": "Nenhuma coleta encontrada a partir desta data!"}), 200

            cursor.execute("SELECT matricula, horario_trabalho FROM tecnicos")
            tecnicos = cursor.fetchall()

            cursor.execute("SELECT cpf, horario_trabalho FROM motoboys")
            motoboys = cursor.fetchall()

            datas_processadas_count = 0
            
            for data_row in todas_datas:
                data_sel = data_row['data_agendamento']

                cursor.execute("""
                    SELECT id, tipo, turno, latitude, longitude, preferencia_horario 
                    FROM coletas WHERE data_agendamento = %s
                """, (data_sel,))
                tarefas_dia = cursor.fetchall()

                updates_tecnicos = []
                updates_motoboys = []

                executar_algoritmo_roteirização('Coleta', tecnicos, tarefas_dia, updates_tecnicos)
                executar_algoritmo_roteirização('Retirada', motoboys, tarefas_dia, updates_motoboys)

                if updates_tecnicos:
                    cursor.executemany("""
                        UPDATE coletas SET tecnico_id = %s, ordem_rota = %s, status = 'Roteirizado' WHERE id = %s
                    """, updates_tecnicos)

                if updates_motoboys:
                    cursor.executemany("""
                        UPDATE coletas SET motoboy_id = %s, ordem_rota = %s, status = 'Roteirizado' WHERE id = %s
                    """, updates_motoboys)
                
                datas_processadas_count += 1

        db.commit()
        return jsonify({"message": f"Sucesso! {datas_processadas_count} dias recalculados a partir de {data_inicio}."}), 200
    except Exception as e:
        print(f"Erro no recálculo total: {e}")
        return jsonify({"message": f"Erro interno: {str(e)}"}), 500
    finally:
        db.close()

@app.route('/visualizar_rotas', methods=['GET'])
def visualizar_rotas():
    data_filtro = request.args.get('data')
    if not data_filtro:
        return jsonify([]), 200

    db = get_db()
    try:
        with db.cursor() as cursor:
            sql = """
                SELECT c.*, t.nome_completo as tecnico_nome, t.horario_trabalho as tecnico_horario,
                       m.nome_completo as motoboy_nome, m.horario_trabalho as motoboy_horario
                FROM coletas c
                LEFT JOIN tecnicos t ON c.tecnico_id = t.matricula
                LEFT JOIN motoboys m ON c.motoboy_id = m.cpf
                WHERE c.data_agendamento = %s AND (c.tecnico_id IS NOT NULL OR c.motoboy_id IS NOT NULL)
                ORDER BY c.ordem_rota ASC
            """
            cursor.execute(sql, (data_filtro,))
            return jsonify(cursor.fetchall()), 200
    finally:
        db.close()

@app.route('/listar_equipe/<tipo>', methods=['GET'])
def listar_equipe(tipo):
    horario = request.args.get('horario', '')
    tabela = 'tecnicos' if tipo == 'tecnico' else 'motoboys'

    db = get_db()
    try:
        with db.cursor() as cursor:
            sql = f"SELECT * FROM {tabela}"
            if horario:
                sql += " WHERE horario_trabalho LIKE %s"
                cursor.execute(sql, (f"%{horario}%",))
            else:
                cursor.execute(sql)
            return jsonify(cursor.fetchall()), 200
    finally:
        db.close()

@app.route('/cadastrar_equipe/<tipo>', methods=['POST'])
def cadastrar_equipe(tipo):
    data = request.json
    db = get_db()
    try:
        with db.cursor() as cursor:
            if tipo == 'tecnico':
                cursor.execute("""
                    INSERT INTO tecnicos (matricula, nome_completo, horario_trabalho)
                    VALUES (%s, %s, %s)
                """, (data['id_ref'], data['nome'], data['horario']))
            else:
                cursor.execute("""
                    INSERT INTO motoboys (cpf, nome_completo, placa_veiculo, horario_trabalho)
                    VALUES (%s, %s, %s, %s)
                """, (data['id_ref'], data['nome'], data['placa'], data['horario']))
        db.commit()
        return jsonify({"message": "Cadastrado com sucesso"}), 201
    finally:
        db.close()

@app.route('/excluir_massa_equipe/<tipo>', methods=['POST'])
def excluir_massa_equipe(tipo):
    ids = request.json.get('ids', [])
    tabela = 'tecnicos' if tipo == 'tecnico' else 'motoboys'
    coluna = 'matricula' if tipo == 'tecnico' else 'cpf'

    db = get_db()
    try:
        with db.cursor() as cursor:
            format_strings = ','.join(['%s'] * len(ids))
            cursor.execute(f"DELETE FROM {tabela} WHERE {coluna} IN ({format_strings})", tuple(ids))
        db.commit()
        return jsonify({"message": "Excluídos com sucesso"}), 200
    finally:
        db.close()

@app.route('/excluir_massa_coletas', methods=['POST'])
def excluir_massa_coletas():
    ids = request.json.get('ids', [])
    if not ids:
        return jsonify({"message": "Nenhum ID informado"}), 400

    db = get_db()
    try:
        with db.cursor() as cursor:
            format_strings = ','.join(['%s'] * len(ids))
            cursor.execute(f"DELETE FROM coletas WHERE id IN ({format_strings})", tuple(ids))
        db.commit()
        return jsonify({"message": f"{len(ids)} agendamentos excluídos!"}), 200
    except Exception as e:
        print(f"Erro ao excluir coletas: {e}")
        return jsonify({"message": str(e)}), 500
    finally:
        db.close()

@app.route('/resumo_pendencias', methods=['GET'])
def resumo_pendencias():
    data_filtro = request.args.get('data')
    if not data_filtro:
        return jsonify({'Coleta': 0, 'Retirada': 0}), 200

    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT tipo, COUNT(*) as qtd FROM coletas
                WHERE data_agendamento = %s AND status = 'Pendente' GROUP BY tipo
            """, (data_filtro,))
            resumo = {'Coleta': 0, 'Retirada': 0}
            for r in cursor.fetchall():
                resumo[r['tipo']] = r['qtd']
            return jsonify(resumo), 200
    finally:
        db.close()

@app.route('/api/rotas_mapa', methods=['GET'])
def api_rotas_mapa():
    data_filtro = request.args.get('data')
    if not data_filtro:
        data_filtro = datetime.today().strftime('%Y-%m-%d')

    db = get_db()
    try:
        with db.cursor() as cursor:
            sql = """
                SELECT c.*, t.nome_completo as tecnico_nome, m.nome_completo as motoboy_nome
                FROM coletas c
                LEFT JOIN tecnicos t ON c.tecnico_id = t.matricula
                LEFT JOIN motoboys m ON c.motoboy_id = m.cpf
                WHERE c.data_agendamento = %s
            """
            cursor.execute(sql, (data_filtro,))
            coletas_db = cursor.fetchall()
            
            paradas = []
            profissionais_ativos = {}

            for c in coletas_db:
                if c['tipo'] == 'Coleta':
                    prof_id, prof_nome = c['tecnico_id'], c['tecnico_nome']
                else:
                    prof_id, prof_nome = c['motoboy_id'], c['motoboy_nome']

                if prof_id and prof_nome:
                    profissionais_ativos[prof_id] = {"id": prof_id, "nome": prof_nome, "tipo": c['tipo']}

                paradas.append({
                    "id": c['id'], "paciente": c['nome'], "endereco": c['endereco'], "tipo": c['tipo'],
                    "horario": str(c['preferencia_horario']), "lat": float(c['latitude']), "lng": float(c['longitude']),
                    "prof_id": prof_id, "ordem": c['ordem_rota']
                })
            
            return jsonify({"paradas": paradas, "profissionais": list(profissionais_ativos.values())}), 200
    except Exception as e:
        print(f"Erro no mapa: {e}")
        return jsonify({"erro": str(e)}), 500
    finally:
        db.close()

@app.route('/api/dashboard', methods=['GET'])
def api_dashboard():
    mes_filtro = request.args.get('mes')
    if not mes_filtro:
        mes_filtro = datetime.today().strftime('%Y-%m')

    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT horario_trabalho FROM tecnicos")
            horarios_tecnicos = list(cursor.fetchall()) 
            
            cursor.execute("SELECT horario_trabalho FROM motoboys")
            horarios_motoboys = list(cursor.fetchall()) 
            
            SLA_ATENDIMENTO = 50 
            limite_diario_total = 0
            
            equipe_completa = horarios_tecnicos + horarios_motoboys
            
            for p in equipe_completa:
                horas = re.findall(r'(\d{2}):(\d{2})', str(p['horario_trabalho']))
                if len(horas) == 2:
                    minutos = (int(horas[1][0]) * 60 + int(horas[1][1])) - (int(horas[0][0]) * 60 + int(horas[0][1]))
                    limite_diario_total += (minutos // SLA_ATENDIMENTO) if minutos > 0 else 8
                else:
                    limite_diario_total += 8

            cursor.execute("SELECT data_agendamento, turno, endereco FROM coletas WHERE data_agendamento LIKE %s", (f"{mes_filtro}%",))
            coletas_mes = cursor.fetchall()
            total_coletas_mes = len(coletas_mes)

            ano, mes = int(mes_filtro.split('-')[0]), int(mes_filtro.split('-')[1])
            data_iteracao = datetime(ano, mes, 1)
            dias_uteis_mes = 0
            while data_iteracao.month == mes:
                if data_iteracao.weekday() < 5:
                    dias_uteis_mes += 1
                data_iteracao += timedelta(days=1)

            limite_maximo_mensal = limite_diario_total * dias_uteis_mes
            vagas_restantes_mes = limite_maximo_mensal - total_coletas_mes
            
            total_profissionais = len(horarios_tecnicos) + len(horarios_motoboys)
            produtividade_media = round(total_coletas_mes / (total_profissionais * dias_uteis_mes), 1) if (total_profissionais * dias_uteis_mes) > 0 else 0

            if limite_maximo_mensal == 0:
                taxa_ocupacao = 100 if total_coletas_mes > 0 else 0
                status_mes = "vermelho"
                mensagem_status = "CRÍTICO: Sem profissionais cadastrados na frota para atender as demandas."
            else:
                taxa_ocupacao = round((total_coletas_mes / limite_maximo_mensal) * 100)
                if vagas_restantes_mes < 0:
                    status_mes = "vermelho"
                    mensagem_status = f"AGENDA ESGOTADA: Faltam {abs(vagas_restantes_mes)} vagas de horários no mês."
                elif taxa_ocupacao >= 80:
                    status_mes = "amarelo"
                    mensagem_status = f"Atenção: Restam apenas {vagas_restantes_mes} vagas disponíveis no mês."
                else:
                    status_mes = "verde"
                    mensagem_status = f"Operação com Folga: +{vagas_restantes_mes} horários disponíveis no mês."

            historico_meses = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]
            dados_historicos = {"meses": ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"], "manha": [], "tarde": []}
            
            for m_ref in historico_meses:
                cursor.execute("SELECT COUNT(*) as qtd FROM coletas WHERE data_agendamento LIKE %s AND turno = 'Manhã'", (f"{m_ref}%",))
                dados_historicos["manha"].append(cursor.fetchone()["qtd"])
                cursor.execute("SELECT COUNT(*) as qtd FROM coletas WHERE data_agendamento LIKE %s AND turno = 'Tarde'", (f"{m_ref}%",))
                dados_historicos["tarde"].append(cursor.fetchone()["qtd"])

            bairros_count = {}
            for c in coletas_mes:
                partes = [p.strip() for p in re.split(r'[,\-]', str(c.get('endereco', ''))) if p.strip()]
                bairro = "Região Não Identificada"
                termos_ignorados = ['sp', 'são paulo', 'sao paulo', 'capital', 'brasil']
                for parte in reversed(partes):
                    if parte.lower() not in termos_ignorados and not re.match(r'^[\d\.\-\s]+$', parte):
                        bairro = parte.title()
                        break
                if bairro != "Região Não Identificada": bairros_count[bairro] = bairros_count.get(bairro, 0) + 1
            
            top_bairros = sorted(bairros_count.items(), key=lambda x: x[1], reverse=True)[:5]
            max_bairro_qtd = top_bairros[0][1] if top_bairros else 1
            regioes_formatadas = [{"nome": b[0], "quantidade": b[1], "percentual": round((b[1]/max_bairro_qtd)*100)} for b in top_bairros]

            mes_atual_sistema = datetime.today().strftime('%Y-%m')
            if mes_filtro >= mes_atual_sistema:
                label_balanco = "Balanço Geral de Capacidade Comercial (Mês em Andamento)"
            else:
                label_balanco = "Balanço Geral de Capacidade Comercial (Mês Fechado)"

            return jsonify({
                "label_comercial": label_balanco,
                "regioes": regioes_formatadas,
                "equipe_ativa": total_profissionais,
                "total_demandas": total_coletas_mes,
                "limite_mensal": limite_maximo_mensal,
                "status_mes": status_mes,
                "mensagem_status": mensagem_status,
                "kpis": {
                    "ocupacao": taxa_ocupacao,
                    "vagas": vagas_restantes_mes,
                    "produtividade": produtividade_media
                },
                "historico": dados_historicos
            }), 200
    except Exception as e:
        print(f"Erro no Dashboard: {e}")
        return jsonify({"erro": str(e)}), 500
    finally:
        db.close()

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql
import pymysql
import csv
import io
import math
import random
import re
import traceback
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

def obter_coordenadas(endereco):
    lat_mock = -23.5505 + random.uniform(-0.05, 0.05)
    lon_mock = -46.6333 + random.uniform(-0.05, 0.05)
    return lat_mock, lon_mock

def calc_distancia(lat1, lon1, lat2, lon2):
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 999999
    return math.sqrt((float(lat2) - float(lat1))**2 + (float(lon2) - float(lon1))**2)

def get_db():
    return pymysql.connect(
        host='localhost',
        user='',
        password='',
        database='arkus_db',
        cursorclass=pymysql.cursors.DictCursor
    )

def init_db():
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    usuario VARCHAR(255) UNIQUE NOT NULL,
                    senha VARCHAR(255) NOT NULL
                )
            """)
        db.commit()
    except Exception as e:
        print("Erro ao criar tabela de usuarios:", e)
    finally:
        db.close()

@app.route('/api/cadastro', methods=['POST'])
def api_cadastro():
    data = request.json
    usuario = data.get('usuario')
    senha = data.get('senha')

    if not usuario or not senha:
        return jsonify({"sucesso": False, "mensagem": "Preencha todos os campos!"}), 400

    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM usuarios WHERE usuario = %s", (usuario,))
            if cursor.fetchone():
                return jsonify({"sucesso": False, "mensagem": "Este e-mail já está em uso."}), 400
            
            cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (%s, %s)", (usuario, senha))
        db.commit()
        return jsonify({"sucesso": True, "mensagem": "Conta criada com sucesso!"}), 201
    except Exception as e:
        return jsonify({"sucesso": False, "mensagem": f"Erro interno: {str(e)}"}), 500
    finally:
        db.close()

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    usuario = data.get('usuario')
    senha = data.get('senha')

    if usuario == 'admin' and senha == '123456':
        return jsonify({"sucesso": True, "mensagem": "Login aprovado"}), 200

    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM usuarios WHERE usuario = %s AND senha = %s", (usuario, senha))
            user = cursor.fetchone()
            
            if user:
                return jsonify({"sucesso": True, "mensagem": "Login aprovado"}), 200
            else:
                return jsonify({"sucesso": False, "mensagem": "Usuário ou senha incorretos!"}), 401
    except Exception as e:
        return jsonify({"sucesso": False, "mensagem": f"Erro interno: {str(e)}"}), 500
    finally:
        db.close()

@app.route('/listar_coletas', methods=['GET'])
def listar_coletas():
    data_filtro = request.args.get('data')
    ordem = request.args.get('ordem', 'ASC').upper()

    if ordem not in ['ASC', 'DESC']:
        ordem = 'ASC'

    db = get_db()
    try:
        with db.cursor() as cursor:
            if data_filtro:
                cursor.execute(
                    f"""
                    SELECT * FROM coletas
                    WHERE data_agendamento = %s
                    ORDER BY data_agendamento {ordem}, preferencia_horario ASC
                    """,
                    (data_filtro,)
                )
            else:
                cursor.execute(
                    f"""
                    SELECT * FROM coletas
                    ORDER BY data_agendamento {ordem}, preferencia_horario ASC
                    """
                )
            return jsonify(cursor.fetchall()), 200
    finally:
        db.close()

@app.route('/importar/<destino>', methods=['POST'])
def importar(destino):
    if 'file' not in request.files:
        return jsonify({"message": "Arquivo ausente"}), 400

    file = request.files['file']
    content = file.stream.read().decode("utf-8-sig").strip()

    stream = io.StringIO(content)
    csv_input = list(csv.DictReader(stream, skipinitialspace=True))

    db = get_db()
    try:
        with db.cursor() as cursor:
            if destino == 'coletas':
                dados_em_lote = []
                for row in csv_input:
                    lat = row.get('latitude') if row.get('latitude') else obter_coordenadas(row.get('endereco'))[0]
                    lon = row.get('longitude') if row.get('longitude') else obter_coordenadas(row.get('endereco'))[1]
                    
                    dados_em_lote.append((
                        row.get('nome'),
                        row.get('endereco'),
                        row.get('turno'),
                        row.get('tipo'),
                        row.get('preferencia_horario'),
                        row.get('data_agendamento'),
                        'Pendente',
                        float(lat),
                        float(lon)
                    ))

                cursor.executemany("""
                    INSERT INTO coletas (
                        nome, endereco, turno, tipo, preferencia_horario,
                        data_agendamento, status, latitude, longitude
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, dados_em_lote)

            elif destino == 'tecnico':
                cursor.executemany("""
                    INSERT INTO tecnicos (matricula, nome_completo, horario_trabalho)
                    VALUES (%s, %s, %s)
                """, [(r.get('matricula'), r.get('nome_completo'), r.get('horario_trabalho')) for r in csv_input])

            elif destino == 'motoboy':
                cursor.executemany("""
                    INSERT INTO motoboys (cpf, nome_completo, placa_veiculo, horario_trabalho)
                    VALUES (%s, %s, %s, %s)
                """, [(r.get('cpf'), r.get('nome_completo'), r.get('placa_veiculo'), r.get('horario_trabalho')) for r in csv_input])

        db.commit()
        return jsonify({"message": f"{len(csv_input)} registros processados com sucesso!"}), 201
    except Exception as e:
        traceback.print_exc()
        return jsonify({"message": str(e)}), 500
    finally:
        db.close()

def executar_algoritmo_roteirização(tipo_servico, equipe, lista_tarefas_dia, lista_update):
    if not equipe: return

    tarefas = [t for t in lista_tarefas_dia if t.get('tipo') == tipo_servico]
    
    def extract_time(val):
        from datetime import timedelta
        if isinstance(val, timedelta):
            total_sec = int(val.total_seconds())
            h = total_sec // 3600
            m = (total_sec % 3600) // 60
            return datetime.strptime(f"{h:02d}:{m:02d}", "%H:%M")
        elif isinstance(val, str):
            parts = val.split(':')
            if len(parts) >= 2:
                h, m = int(parts[0]), int(parts[1])
                return datetime.strptime(f"{h:02d}:{m:02d}", "%H:%M")
        return datetime.strptime("00:00", "%H:%M")

    tarefas.sort(key=lambda t: extract_time(t.get('preferencia_horario')))

    agendas = { (p.get('matricula') or p.get('cpf')): [] for p in equipe }
    ordem_por_profissional = { (p.get('matricula') or p.get('cpf')): 1 for p in equipe }

    for tarefa in tarefas:
        h_tarefa = extract_time(tarefa.get('preferencia_horario'))
        equipe_balanceada = sorted(equipe, key=lambda p: len(agendas[p.get('matricula') or p.get('cpf')]))

        for prof in equipe_balanceada:
            p_id = prof.get('matricula') or prof.get('cpf')
            horario_str = str(prof.get('horario_trabalho', '00:00 - 23:59'))
            
            try:
                inicio_str, fim_str = horario_str.split('-')
                h_inicio = datetime.strptime(inicio_str.strip(), "%H:%M").time()
                h_fim = datetime.strptime(fim_str.strip(), "%H:%M").time()
            except Exception:
                h_inicio = datetime.strptime("00:00", "%H:%M").time()
                h_fim = datetime.strptime("23:59", "%H:%M").time()

            if not (h_inicio <= h_tarefa.time() < h_fim):
                continue

            conflito = False
            for h_agendada in agendas[p_id]:
                diff_minutos = abs((h_tarefa - h_agendada).total_seconds()) / 60
                if diff_minutos < 60:
                    conflito = True
                    break

            if not conflito:
                agendas[p_id].append(h_tarefa)
                lista_update.append((p_id, ordem_por_profissional[p_id], tarefa['id']))
                ordem_por_profissional[p_id] += 1
                break 

@app.route('/gerar_rotas_pendentes', methods=['POST'])
def gerar_rotas_pendentes():
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM coletas WHERE (tecnico_id IS NULL OR tecnico_id = '') AND (motoboy_id IS NULL OR motoboy_id = '')")
            pendentes = cursor.fetchall()
            
            cursor.execute("SELECT matricula as id, horario_trabalho FROM tecnicos")
            tecnicos = cursor.fetchall()
            
            cursor.execute("SELECT cpf as id, horario_trabalho FROM motoboys")
            motoboys = cursor.fetchall()
            
            alocados = 0
            
            for paciente in pendentes:
                horario_paciente = paciente.get('preferencia_horario')
                if not horario_paciente:
                    continue
                    
                try:
                    if isinstance(horario_paciente, timedelta):
                        total_sec = int(horario_paciente.total_seconds())
                        h, m = total_sec // 3600, (total_sec % 3600) // 60
                        h_tarefa = datetime.strptime(f"{h:02d}:{m:02d}", "%H:%M").time()
                    else:
                        parts = str(horario_paciente).split(':')
                        h_tarefa = datetime.strptime(f"{int(parts[0]):02d}:{int(parts[1]):02d}", "%H:%M").time()
                except Exception:
                    continue

                data_paciente = paciente['data_agendamento']
                tipo_demanda = paciente['tipo']
                
                equipe = tecnicos if tipo_demanda == 'Coleta' else motoboys
                coluna_fk = 'tecnico_id' if tipo_demanda == 'Coleta' else 'motoboy_id'
                
                profissional_escolhido = None
                
                for prof in equipe:
                    horario_str = str(prof.get('horario_trabalho', '00:00 - 23:59'))
                    try:
                        inicio_str, fim_str = horario_str.split('-')
                        h_inicio = datetime.strptime(inicio_str.strip(), "%H:%M").time()
                        h_fim = datetime.strptime(fim_str.strip(), "%H:%M").time()
                    except Exception:
                        h_inicio = datetime.strptime("00:00", "%H:%M").time()
                        h_fim = datetime.strptime("23:59", "%H:%M").time()
                        
                    if not (h_inicio <= h_tarefa < h_fim):
                        continue
                        
                    query_conflito = f"""
                        SELECT 1 FROM coletas 
                        WHERE data_agendamento = %s 
                          AND {coluna_fk} = %s
                          AND ABS(TIME_TO_SEC(TIMEDIFF(preferencia_horario, %s))) < 3600
                        LIMIT 1
                    """
                    cursor.execute(query_conflito, (data_paciente, prof['id'], str(horario_paciente)))
                    if cursor.fetchone():
                        continue 
                        
                    profissional_escolhido = prof['id']
                    break
                    
                if profissional_escolhido:
                    query_ordem = """
                        SELECT COALESCE(MAX(ordem_rota), 0) + 1 as proxima_ordem 
                        FROM coletas 
                        WHERE data_agendamento = %s AND (tecnico_id = %s OR motoboy_id = %s)
                    """
                    cursor.execute(query_ordem, (data_paciente, profissional_escolhido, profissional_escolhido))
                    nova_ordem = cursor.fetchone()['proxima_ordem']
                    
                    query_update = f"""
                        UPDATE coletas 
                        SET {coluna_fk} = %s, ordem_rota = %s, status = 'Roteirizado' 
                        WHERE id = %s
                    """
                    cursor.execute(query_update, (profissional_escolhido, nova_ordem, paciente['id']))
                    alocados += 1
                    
        db.commit()
        if alocados > 0:
            msg = f"Varredura global concluída! {alocados} novas demandas foram alocadas."
        else:
            msg = "Varredura concluída! Nenhuma pendência pôde ser alocada."
            
        return jsonify({"message": msg})
    
    except Exception as e:
        print(f"Erro Crítico: {str(e)}")
        db.rollback()
        return jsonify({"error": "Erro no servidor ao processar as rotas"}), 500
    finally:
        db.close()
        
@app.route('/gerar_todas_rotas', methods=['POST'])
def gerar_todas_rotas():
    data = request.json
    data_inicio = data.get('data_inicio')
    
    if not data_inicio:
        return jsonify({"message": "Data de partida não informada!"}), 400

    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                UPDATE coletas
                SET tecnico_id = NULL, motoboy_id = NULL, ordem_rota = NULL, status = 'Pendente'
                WHERE data_agendamento >= %s
            """, (data_inicio,))
            
            cursor.execute("SELECT DISTINCT data_agendamento FROM coletas WHERE data_agendamento >= %s ORDER BY data_agendamento ASC", (data_inicio,))
            todas_datas = cursor.fetchall()

            if not todas_datas:
                return jsonify({"message": "Nenhuma coleta encontrada a partir desta data!"}), 200

            cursor.execute("SELECT matricula, horario_trabalho FROM tecnicos")
            tecnicos = cursor.fetchall()

            cursor.execute("SELECT cpf, horario_trabalho FROM motoboys")
            motoboys = cursor.fetchall()

            datas_processadas_count = 0
            
            for data_row in todas_datas:
                data_sel = data_row['data_agendamento']

                cursor.execute("""
                    SELECT id, tipo, turno, latitude, longitude, preferencia_horario 
                    FROM coletas WHERE data_agendamento = %s
                """, (data_sel,))
                tarefas_dia = cursor.fetchall()

                updates_tecnicos = []
                updates_motoboys = []

                executar_algoritmo_roteirização('Coleta', tecnicos, tarefas_dia, updates_tecnicos)
                executar_algoritmo_roteirização('Retirada', motoboys, tarefas_dia, updates_motoboys)

                if updates_tecnicos:
                    cursor.executemany("""
                        UPDATE coletas SET tecnico_id = %s, ordem_rota = %s, status = 'Roteirizado' WHERE id = %s
                    """, updates_tecnicos)

                if updates_motoboys:
                    cursor.executemany("""
                        UPDATE coletas SET motoboy_id = %s, ordem_rota = %s, status = 'Roteirizado' WHERE id = %s
                    """, updates_motoboys)
                
                datas_processadas_count += 1

        db.commit()
        return jsonify({"message": f"Sucesso! {datas_processadas_count} dias recalculados a partir de {data_inicio}."}), 200
    except Exception as e:
        print(f"Erro no recálculo total: {e}")
        return jsonify({"message": f"Erro interno: {str(e)}"}), 500
    finally:
        db.close()

@app.route('/visualizar_rotas', methods=['GET'])
def visualizar_rotas():
    data_filtro = request.args.get('data')
    if not data_filtro:
        return jsonify([]), 200

    db = get_db()
    try:
        with db.cursor() as cursor:
            sql = """
                SELECT c.*, t.nome_completo as tecnico_nome, t.horario_trabalho as tecnico_horario,
                       m.nome_completo as motoboy_nome, m.horario_trabalho as motoboy_horario
                FROM coletas c
                LEFT JOIN tecnicos t ON c.tecnico_id = t.matricula
                LEFT JOIN motoboys m ON c.motoboy_id = m.cpf
                WHERE c.data_agendamento = %s AND (c.tecnico_id IS NOT NULL OR c.motoboy_id IS NOT NULL)
                ORDER BY c.ordem_rota ASC
            """
            cursor.execute(sql, (data_filtro,))
            return jsonify(cursor.fetchall()), 200
    finally:
        db.close()

@app.route('/listar_equipe/<tipo>', methods=['GET'])
def listar_equipe(tipo):
    horario = request.args.get('horario', '')
    tabela = 'tecnicos' if tipo == 'tecnico' else 'motoboys'

    db = get_db()
    try:
        with db.cursor() as cursor:
            sql = f"SELECT * FROM {tabela}"
            if horario:
                sql += " WHERE horario_trabalho LIKE %s"
                cursor.execute(sql, (f"%{horario}%",))
            else:
                cursor.execute(sql)
            return jsonify(cursor.fetchall()), 200
    finally:
        db.close()

@app.route('/cadastrar_equipe/<tipo>', methods=['POST'])
def cadastrar_equipe(tipo):
    data = request.json
    db = get_db()
    try:
        with db.cursor() as cursor:
            if tipo == 'tecnico':
                cursor.execute("""
                    INSERT INTO tecnicos (matricula, nome_completo, horario_trabalho)
                    VALUES (%s, %s, %s)
                """, (data['id_ref'], data['nome'], data['horario']))
            else:
                cursor.execute("""
                    INSERT INTO motoboys (cpf, nome_completo, placa_veiculo, horario_trabalho)
                    VALUES (%s, %s, %s, %s)
                """, (data['id_ref'], data['nome'], data['placa'], data['horario']))
        db.commit()
        return jsonify({"message": "Cadastrado com sucesso"}), 201
    finally:
        db.close()

@app.route('/excluir_massa_equipe/<tipo>', methods=['POST'])
def excluir_massa_equipe(tipo):
    ids = request.json.get('ids', [])
    tabela = 'tecnicos' if tipo == 'tecnico' else 'motoboys'
    coluna = 'matricula' if tipo == 'tecnico' else 'cpf'

    db = get_db()
    try:
        with db.cursor() as cursor:
            format_strings = ','.join(['%s'] * len(ids))
            cursor.execute(f"DELETE FROM {tabela} WHERE {coluna} IN ({format_strings})", tuple(ids))
        db.commit()
        return jsonify({"message": "Excluídos com sucesso"}), 200
    finally:
        db.close()

@app.route('/excluir_massa_coletas', methods=['POST'])
def excluir_massa_coletas():
    ids = request.json.get('ids', [])
    if not ids:
        return jsonify({"message": "Nenhum ID informado"}), 400

    db = get_db()
    try:
        with db.cursor() as cursor:
            format_strings = ','.join(['%s'] * len(ids))
            cursor.execute(f"DELETE FROM coletas WHERE id IN ({format_strings})", tuple(ids))
        db.commit()
        return jsonify({"message": f"{len(ids)} agendamentos excluídos!"}), 200
    except Exception as e:
        print(f"Erro ao excluir coletas: {e}")
        return jsonify({"message": str(e)}), 500
    finally:
        db.close()

@app.route('/resumo_pendencias', methods=['GET'])
def resumo_pendencias():
    data_filtro = request.args.get('data')
    if not data_filtro:
        return jsonify({'Coleta': 0, 'Retirada': 0}), 200

    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT tipo, COUNT(*) as qtd FROM coletas
                WHERE data_agendamento = %s AND status = 'Pendente' GROUP BY tipo
            """, (data_filtro,))
            resumo = {'Coleta': 0, 'Retirada': 0}
            for r in cursor.fetchall():
                resumo[r['tipo']] = r['qtd']
            return jsonify(resumo), 200
    finally:
        db.close()

@app.route('/api/rotas_mapa', methods=['GET'])
def api_rotas_mapa():
    data_filtro = request.args.get('data')
    if not data_filtro:
        data_filtro = datetime.today().strftime('%Y-%m-%d')

    db = get_db()
    try:
        with db.cursor() as cursor:
            sql = """
                SELECT c.*, t.nome_completo as tecnico_nome, m.nome_completo as motoboy_nome
                FROM coletas c
                LEFT JOIN tecnicos t ON c.tecnico_id = t.matricula
                LEFT JOIN motoboys m ON c.motoboy_id = m.cpf
                WHERE c.data_agendamento = %s
            """
            cursor.execute(sql, (data_filtro,))
            coletas_db = cursor.fetchall()
            
            paradas = []
            profissionais_ativos = {}

            for c in coletas_db:
                if c['tipo'] == 'Coleta':
                    prof_id, prof_nome = c['tecnico_id'], c['tecnico_nome']
                else:
                    prof_id, prof_nome = c['motoboy_id'], c['motoboy_nome']

                if prof_id and prof_nome:
                    profissionais_ativos[prof_id] = {"id": prof_id, "nome": prof_nome, "tipo": c['tipo']}

                paradas.append({
                    "id": c['id'], "paciente": c['nome'], "endereco": c['endereco'], "tipo": c['tipo'],
                    "horario": str(c['preferencia_horario']), "lat": float(c['latitude']), "lng": float(c['longitude']),
                    "prof_id": prof_id, "ordem": c['ordem_rota']
                })
            
            return jsonify({"paradas": paradas, "profissionais": list(profissionais_ativos.values())}), 200
    except Exception as e:
        print(f"Erro no mapa: {e}")
        return jsonify({"erro": str(e)}), 500
    finally:
        db.close()

@app.route('/api/dashboard', methods=['GET'])
def api_dashboard():
    mes_filtro = request.args.get('mes')
    if not mes_filtro:
        mes_filtro = datetime.today().strftime('%Y-%m')

    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT horario_trabalho FROM tecnicos")
            horarios_tecnicos = list(cursor.fetchall()) 
            
            cursor.execute("SELECT horario_trabalho FROM motoboys")
            horarios_motoboys = list(cursor.fetchall()) 
            
            SLA_ATENDIMENTO = 50 
            limite_diario_total = 0
            
            equipe_completa = horarios_tecnicos + horarios_motoboys
            
            for p in equipe_completa:
                horas = re.findall(r'(\d{2}):(\d{2})', str(p['horario_trabalho']))
                if len(horas) == 2:
                    minutos = (int(horas[1][0]) * 60 + int(horas[1][1])) - (int(horas[0][0]) * 60 + int(horas[0][1]))
                    limite_diario_total += (minutos // SLA_ATENDIMENTO) if minutos > 0 else 8
                else:
                    limite_diario_total += 8

            cursor.execute("SELECT data_agendamento, turno, endereco FROM coletas WHERE data_agendamento LIKE %s", (f"{mes_filtro}%",))
            coletas_mes = cursor.fetchall()
            total_coletas_mes = len(coletas_mes)

            ano, mes = int(mes_filtro.split('-')[0]), int(mes_filtro.split('-')[1])
            data_iteracao = datetime(ano, mes, 1)
            dias_uteis_mes = 0
            while data_iteracao.month == mes:
                if data_iteracao.weekday() < 5:
                    dias_uteis_mes += 1
                data_iteracao += timedelta(days=1)

            limite_maximo_mensal = limite_diario_total * dias_uteis_mes
            vagas_restantes_mes = limite_maximo_mensal - total_coletas_mes
            
            total_profissionais = len(horarios_tecnicos) + len(horarios_motoboys)
            produtividade_media = round(total_coletas_mes / (total_profissionais * dias_uteis_mes), 1) if (total_profissionais * dias_uteis_mes) > 0 else 0

            if limite_maximo_mensal == 0:
                taxa_ocupacao = 100 if total_coletas_mes > 0 else 0
                status_mes = "vermelho"
                mensagem_status = "CRÍTICO: Sem profissionais cadastrados na frota para atender as demandas."
            else:
                taxa_ocupacao = round((total_coletas_mes / limite_maximo_mensal) * 100)
                if vagas_restantes_mes < 0:
                    status_mes = "vermelho"
                    mensagem_status = f"AGENDA ESGOTADA: Faltam {abs(vagas_restantes_mes)} vagas de horários no mês."
                elif taxa_ocupacao >= 80:
                    status_mes = "amarelo"
                    mensagem_status = f"Atenção: Restam apenas {vagas_restantes_mes} vagas disponíveis no mês."
                else:
                    status_mes = "verde"
                    mensagem_status = f"Operação com Folga: +{vagas_restantes_mes} horários disponíveis no mês."

            historico_meses = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]
            dados_historicos = {"meses": ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"], "manha": [], "tarde": []}
            
            for m_ref in historico_meses:
                cursor.execute("SELECT COUNT(*) as qtd FROM coletas WHERE data_agendamento LIKE %s AND turno = 'Manhã'", (f"{m_ref}%",))
                dados_historicos["manha"].append(cursor.fetchone()["qtd"])
                cursor.execute("SELECT COUNT(*) as qtd FROM coletas WHERE data_agendamento LIKE %s AND turno = 'Tarde'", (f"{m_ref}%",))
                dados_historicos["tarde"].append(cursor.fetchone()["qtd"])

            bairros_count = {}
            for c in coletas_mes:
                partes = [p.strip() for p in re.split(r'[,\-]', str(c.get('endereco', ''))) if p.strip()]
                bairro = "Região Não Identificada"
                termos_ignorados = ['sp', 'são paulo', 'sao paulo', 'capital', 'brasil']
                for parte in reversed(partes):
                    if parte.lower() not in termos_ignorados and not re.match(r'^[\d\.\-\s]+$', parte):
                        bairro = parte.title()
                        break
                if bairro != "Região Não Identificada": bairros_count[bairro] = bairros_count.get(bairro, 0) + 1
            
            top_bairros = sorted(bairros_count.items(), key=lambda x: x[1], reverse=True)[:5]
            max_bairro_qtd = top_bairros[0][1] if top_bairros else 1
            regioes_formatadas = [{"nome": b[0], "quantidade": b[1], "percentual": round((b[1]/max_bairro_qtd)*100)} for b in top_bairros]

            mes_atual_sistema = datetime.today().strftime('%Y-%m')
            if mes_filtro >= mes_atual_sistema:
                label_balanco = "Balanço Geral de Capacidade Comercial (Mês em Andamento)"
            else:
                label_balanco = "Balanço Geral de Capacidade Comercial (Mês Fechado)"

            return jsonify({
                "label_comercial": label_balanco,
                "regioes": regioes_formatadas,
                "equipe_ativa": total_profissionais,
                "total_demandas": total_coletas_mes,
                "limite_mensal": limite_maximo_mensal,
                "status_mes": status_mes,
                "mensagem_status": mensagem_status,
                "kpis": {
                    "ocupacao": taxa_ocupacao,
                    "vagas": vagas_restantes_mes,
                    "produtividade": produtividade_media
                },
                "historico": dados_historicos
            }), 200
    except Exception as e:
        print(f"Erro no Dashboard: {e}")
        return jsonify({"erro": str(e)}), 500
    finally:
        db.close()

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
