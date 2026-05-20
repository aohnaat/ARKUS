from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
import csv
import io
import math
import random
from datetime import datetime

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
        host='DB_HOST',
        user='DB_USER',
        password='DB_PASSWORD',
        database='DB_NAME',
        cursorclass=pymysql.cursors.DictCursor
    )

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

                    lat, lon = obter_coordenadas(row['endereco'])

                    dados_em_lote.append((
                        row['paciente'],
                        row['endereco'],
                        row['turno'],
                        row['tipo'],
                        row['preferencia'],
                        row['data'],
                        'Pendente',
                        lat,
                        lon
                    ))

                cursor.executemany("""
                    INSERT INTO coletas (
                        nome,
                        endereco,
                        turno,
                        tipo,
                        preferencia_horario,
                        data_agendamento,
                        status,
                        latitude,
                        longitude
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, dados_em_lote)

            elif destino == 'tecnico':

                cursor.executemany(
                    """
                    INSERT INTO tecnicos (
                        matricula,
                        nome_completo,
                        horario_trabalho
                    )
                    VALUES (%s, %s, %s)
                    """,
                    [
                        (
                            r['matricula'],
                            r['nome_completo'],
                            r['horario_trabalho']
                        )
                        for r in csv_input
                    ]
                )

            elif destino == 'motoboy':

                cursor.executemany(
                    """
                    INSERT INTO motoboys (
                        cpf,
                        nome_completo,
                        placa_veiculo,
                        horario_trabalho
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    [
                        (
                            r['cpf'],
                            r['nome_completo'],
                            r['placa_veiculo'],
                            r['horario_trabalho']
                        )
                        for r in csv_input
                    ]
                )

        db.commit()

        return jsonify({
            "message": f"{len(csv_input)} registros processados!"
        }), 201

    except Exception as e:

        print(f"Erro na importação: {e}")

        return jsonify({
            "message": str(e)
        }), 500

    finally:
        db.close()

@app.route('/gerar_rotas', methods=['POST'])
def gerar_rotas():

    data_sel = request.json.get('data')

    if not data_sel:
        return jsonify({"message": "Data não informada"}), 400

    db = get_db()

    try:
        with db.cursor() as cursor:

            cursor.execute("""
                UPDATE coletas
                SET tecnico_id = NULL,
                    motoboy_id = NULL,
                    ordem_rota = NULL,
                    status = 'Pendente'
                WHERE data_agendamento = %s
            """, (data_sel,))

            cursor.execute("""
                SELECT matricula, horario_trabalho
                FROM tecnicos
            """)
            tecnicos = cursor.fetchall()

            cursor.execute("""
                SELECT cpf, horario_trabalho
                FROM motoboys
            """)
            motoboys = cursor.fetchall()

            cursor.execute("""
                SELECT
                    id,
                    tipo,
                    turno,
                    latitude,
                    longitude,
                    preferencia_horario
                FROM coletas
                WHERE data_agendamento = %s
            """, (data_sel,))

            todas_tarefas = cursor.fetchall()

            janelas = {
                "06:00 - 12:00": (6, 12),
                "07:00 - 13:00": (7, 13),
                "12:00 - 18:00": (12, 18),
                "13:00 - 19:00": (13, 19),
                "Manhã": (6, 12),
                "Tarde": (12, 19)
            }

            updates_tecnicos = []
            updates_motoboys = []

            def roteirizar(tipo_servico, equipe, lista_update):

                if not equipe:
                    return

                for turno_nome in ['Manhã', 'Tarde']:

                    if turno_nome == 'Manhã':
                        prof_turno = [
                            p for p in equipe
                            if any(
                                h in p['horario_trabalho']
                                for h in ["06:00", "07:00", "Manhã"]
                            )
                        ]
                    else:
                        prof_turno = [
                            p for p in equipe
                            if any(
                                h in p['horario_trabalho']
                                for h in ["12:00", "13:00", "Tarde"]
                            )
                        ]

                    tarefas = [
                        t for t in todas_tarefas
                        if t['tipo'] == tipo_servico
                        and t['turno'] == turno_nome
                    ]

                    tarefas.sort(
                        key=lambda x: str(x['preferencia_horario'])
                    )

                    agendas = {
                        (
                            p['matricula']
                            if 'matricula' in p
                            else p['cpf']
                        ): []
                        for p in prof_turno
                    }

                    for t in tarefas:

                        try:
                            h_tarefa = datetime.strptime(
                                str(t['preferencia_horario']),
                                "%H:%M"
                            )
                        except:
                            continue

                        prof_turno.sort(
                            key=lambda p: len(
                                agendas[
                                    p['matricula']
                                    if 'matricula' in p
                                    else p['cpf']
                                ]
                            )
                        )

                        for prof in prof_turno:

                            p_id = (
                                prof['matricula']
                                if 'matricula' in prof
                                else prof['cpf']
                            )

                            inicio, fim = janelas.get(
                                prof['horario_trabalho'],
                                (0, 24)
                            )

                            if inicio <= h_tarefa.hour < fim:

                                conflito = any(
                                    abs(
                                        (
                                            h_tarefa - h_exp
                                        ).total_seconds()
                                    ) < 3600
                                    for h_exp in agendas[p_id]
                                )

                                if not conflito:

                                    agendas[p_id].append(h_tarefa)

                                    lista_update.append((
                                        p_id,
                                        len(agendas[p_id]),
                                        t['id']
                                    ))

                                    break

            roteirizar(
                'Coleta',
                tecnicos,
                updates_tecnicos
            )

            roteirizar(
                'Retirada',
                motoboys,
                updates_motoboys
            )

            if updates_tecnicos:

                cursor.executemany("""
                    UPDATE coletas
                    SET tecnico_id = %s,
                        ordem_rota = %s,
                        status = 'Roteirizado'
                    WHERE id = %s
                """, updates_tecnicos)

            if updates_motoboys:

                cursor.executemany("""
                    UPDATE coletas
                    SET motoboy_id = %s,
                        ordem_rota = %s,
                        status = 'Roteirizado'
                    WHERE id = %s
                """, updates_motoboys)

        db.commit()

        return jsonify({
            "message": "Rotas otimizadas geradas!"
        }), 200

    except Exception as e:

        print(f"Erro: {e}")

        return jsonify({
            "message": "Erro interno"
        }), 500

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
                SELECT
                    c.*,
                    t.nome_completo as tecnico_nome,
                    t.horario_trabalho as tecnico_horario,
                    m.nome_completo as motoboy_nome,
                    m.horario_trabalho as motoboy_horario
                FROM coletas c
                LEFT JOIN tecnicos t
                    ON c.tecnico_id = t.matricula
                LEFT JOIN motoboys m
                    ON c.motoboy_id = m.cpf
                WHERE c.data_agendamento = %s
                AND (
                    c.tecnico_id IS NOT NULL
                    OR c.motoboy_id IS NOT NULL
                )
                ORDER BY c.ordem_rota ASC
            """

            cursor.execute(sql, (data_filtro,))

            return jsonify(cursor.fetchall()), 200

    finally:
        db.close()

@app.route('/listar_equipe/<tipo>', methods=['GET'])
def listar_equipe(tipo):

    horario = request.args.get('horario', '')

    tabela = (
        'tecnicos'
        if tipo == 'tecnico'
        else 'motoboys'
    )

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
                    INSERT INTO tecnicos (
                        matricula,
                        nome_completo,
                        horario_trabalho
                    )
                    VALUES (%s, %s, %s)
                """, (
                    data['id_ref'],
                    data['nome'],
                    data['horario']
                ))

            else:

                cursor.execute("""
                    INSERT INTO motoboys (
                        cpf,
                        nome_completo,
                        placa_veiculo,
                        horario_trabalho
                    )
                    VALUES (%s, %s, %s, %s)
                """, (
                    data['id_ref'],
                    data['nome'],
                    data['placa'],
                    data['horario']
                ))

        db.commit()

        return jsonify({
            "message": "Cadastrado com sucesso"
        }), 201

    finally:
        db.close()

@app.route('/excluir_massa_equipe/<tipo>', methods=['POST'])
def excluir_massa_equipe(tipo):

    ids = request.json.get('ids', [])

    tabela = (
        'tecnicos'
        if tipo == 'tecnico'
        else 'motoboys'
    )

    coluna = (
        'matricula'
        if tipo == 'tecnico'
        else 'cpf'
    )

    db = get_db()

    try:
        with db.cursor() as cursor:

            format_strings = ','.join(['%s'] * len(ids))

            cursor.execute(
                f"""
                DELETE FROM {tabela}
                WHERE {coluna} IN ({format_strings})
                """,
                tuple(ids)
            )

        db.commit()

        return jsonify({
            "message": "Excluídos com sucesso"
        }), 200

    finally:
        db.close()

@app.route('/resumo_pendencias', methods=['GET'])
def resumo_pendencias():

    data_filtro = request.args.get('data')

    if not data_filtro:
        return jsonify({
            "Coleta": 0,
            "Retirada": 0
        }), 200

    db = get_db()

    try:
        with db.cursor() as cursor:

            cursor.execute("""
                SELECT
                    tipo,
                    COUNT(*) as qtd
                FROM coletas
                WHERE data_agendamento = %s
                AND status = 'Pendente'
                GROUP BY tipo
            """, (data_filtro,))

            resultados = cursor.fetchall()

            resumo = {
                'Coleta': 0,
                'Retirada': 0
            }

            for r in resultados:
                resumo[r['tipo']] = r['qtd']

            return jsonify(resumo), 200

    finally:
        db.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
