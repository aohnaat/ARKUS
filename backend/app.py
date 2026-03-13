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
    file = request.files['file']
    content = file.stream.read().decode("utf-8-sig").strip()
    stream = io.StringIO(content)
    csv_input = csv.DictReader(stream, skipinitialspace=True)
    db = get_db()
    with db.cursor() as cursor:
        for row in csv_input:
            sql = "INSERT INTO coletas (nome, endereco, turno, tipo, data_agendamento) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (row['nome'], row['endereco'], row['turno'], row['tipo'], row['data']))
    db.commit()
    return jsonify({"message": "Sucesso"}), 201

@app.route('/listar_demandas', methods=['GET'])
def listar_demandas():
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM coletas")
        return jsonify(cursor.fetchall()), 200

if __name__ == '__main__':
    app.run(debug=True)
