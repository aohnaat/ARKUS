from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
import csv
import io

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

def get_db():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='1945',
        database='arkus_db',
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/listar_coletas', methods=['GET'])
def listar_coletas():
    data_filtro = request.args.get('data')
    db = get_db()
    try:
        with db.cursor() as cursor:
            if data_filtro:
                cursor.execute("SELECT * FROM coletas WHERE data_agendamento = %s", (data_filtro,))
            else:
                cursor.execute("SELECT * FROM coletas ORDER BY data_agendamento DESC")
            return jsonify(cursor.fetchall()), 200
    finally:
        db.close()

@app.route('/cadastrar_coleta', methods=['POST'])
def cadastrar_coleta():
    data = request.json
    db = get_db()
    try:
        with db.cursor() as cursor:
            sql = """INSERT INTO coletas (nome, endereco, turno, tipo, preferencia_horario, data_agendamento, status) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, (data['paciente'], data['endereco'], data['turno'], data['tipo'], data['preferencia'], data['data'], 'Pendente'))
        db.commit()
        return jsonify({"message": "Sucesso"}), 201
    finally:
        db.close()

@app.route('/excluir_coletas', methods=['POST'])
def excluir_coletas():
    ids = request.json.get('ids', [])
    db = get_db()
    try:
        with db.cursor() as cursor:
            if ids:
                format_strings = ','.join(['%s'] * len(ids))
                cursor.execute(f"DELETE FROM coletas WHERE id IN ({format_strings})", tuple(ids))
        db.commit()
        return jsonify({"message": "OK"}), 200
    finally:
        db.close()

@app.route('/listar_equipe/<tipo>', methods=['GET'])
def listar_equipe(tipo):
    horario = request.args.get('horario')
    db = get_db()
    tabela = "tecnicos" if tipo == "tecnico" else "motoboys"
    try:
        with db.cursor() as cursor:
            if horario:
                cursor.execute(f"SELECT * FROM {tabela} WHERE horario_trabalho LIKE %s", (f"%{horario}%",))
            else:
                cursor.execute(f"SELECT * FROM {tabela}")
            return jsonify(cursor.fetchall()), 200
    finally:
        db.close()

@app.route('/cadastrar_equipe/<tipo>', methods=['POST'])
def cadastrar_equipe(tipo):
    data = request.json
    db = get_db()
    tabela = "tecnicos" if tipo == "tecnico" else "motoboys"
    try:
        with db.cursor() as cursor:
            if tipo == "tecnico":
                sql = f"INSERT INTO {tabela} (matricula, nome_completo, horario_trabalho) VALUES (%s, %s, %s)"
                cursor.execute(sql, (data['id_ref'], data['nome'], data['horario']))
            else:
                sql = f"INSERT INTO {tabela} (cpf, nome_completo, placa_veiculo, horario_trabalho) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (data['id_ref'], data['nome'], data['placa'], data['horario']))
        db.commit()
        return jsonify({"message": "Sucesso"}), 201
    except pymysql.err.IntegrityError:
        return jsonify({"message": "ID duplicado"}), 409
    finally:
        db.close()

@app.route('/excluir_massa_equipe/<tipo>', methods=['POST'])
def excluir_massa_equipe(tipo):
    ids = request.json.get('ids', [])
    tabela = "tecnicos" if tipo == "tecnico" else "motoboys"
    coluna = "matricula" if tipo == "tecnico" else "cpf"
    db = get_db()
    try:
        with db.cursor() as cursor:
            if ids:
                format_strings = ','.join(['%s'] * len(ids))
                cursor.execute(f"DELETE FROM {tabela} WHERE {coluna} IN ({format_strings})", tuple(ids))
        db.commit()
        return jsonify({"message": "OK"}), 200
    finally:
        db.close()

@app.route('/importar/<destino>', methods=['POST'])
def importar(destino):
    if 'file' not in request.files: return jsonify({"message": "Arquivo ausente"}), 400
    file = request.files['file']
    content = file.stream.read().decode("utf-8-sig").strip()
    stream = io.StringIO(content)
    csv_input = csv.DictReader(stream, skipinitialspace=True)
    db = get_db()
    try:
        with db.cursor() as cursor:
            for row in csv_input:
                if destino == 'coletas':
                    cursor.execute("INSERT INTO coletas (nome, endereco, turno, tipo, preferencia_horario, data_agendamento) VALUES (%s, %s, %s, %s, %s, %s)", 
                                   (row['paciente'], row['endereco'], row['turno'], row['tipo'], row['preferencia'], row['data']))
                elif destino == 'tecnico':
                    cursor.execute("INSERT INTO tecnicos (matricula, nome_completo, horario_trabalho) VALUES (%s, %s, %s)",
                                   (row['matricula'], row['nome_completo'], row['horario_trabalho']))
                elif destino == 'motoboy':
                    cursor.execute("INSERT INTO motoboys (cpf, nome_completo, placa_veiculo, horario_trabalho) VALUES (%s, %s, %s, %s)", 
                                   (row['cpf'], row['nome_completo'], row['placa_veiculo'], row['horario_trabalho']))
        db.commit()
        return jsonify({"message": "Importação concluída"}), 201
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        db.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
