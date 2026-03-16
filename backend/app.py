from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
import csv
import io

app = Flask(__name__)
CORS(app)

def get_db():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='1945',
        database='arkus_db',
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/importar_csv', methods=['POST'])
def importar_csv():
    try:
        file = request.files['file']
        content = file.stream.read().decode("utf-8-sig").strip()
        stream = io.StringIO(content)
        csv_input = csv.DictReader(stream, skipinitialspace=True)

        db = get_db()
        with db.cursor() as cursor:
            for row in csv_input:
                sql = """INSERT INTO coletas 
                (nome, endereco, turno, tipo, preferencia_horario, data_agendamento, status) 
                VALUES (%s, %s, %s, %s, %s, %s, 'Pendente')"""
                
                cursor.execute(sql, (
                    row['nome'],
                    row['endereco'],
                    row['turno'],
                    row['tipo'],
                    row['preferencia_horario'],
                    row['data']
                ))

        db.commit()
        return jsonify({"message": "Importação concluída"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    data = request.json
    db = get_db()
    with db.cursor() as cursor:
        sql = """INSERT INTO coletas 
        (nome, endereco, turno, tipo, preferencia_horario, data_agendamento, status) 
        VALUES (%s, %s, %s, %s, %s, %s, 'Pendente')"""
        cursor.execute(sql, (
            data['nome'],
            data['endereco'],
            data['turno'],
            data['tipo'],
            data['preferencia_horario'],
            data['data']
        ))
    db.commit()
    return jsonify({"message": "Cadastrado com sucesso"}), 201

@app.route('/listar', methods=['GET'])
def listar():
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM coletas ORDER BY data_agendamento DESC")
        return jsonify(cursor.fetchall()), 200

@app.route('/deletar/<int:id>', methods=['DELETE'])
def deletar(id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("DELETE FROM coletas WHERE id = %s", (id,))
    db.commit()
    return jsonify({"message": "Removido"}), 200
    
if __name__ == '__main__':
    app.run(debug=True)
