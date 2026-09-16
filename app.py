from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import date, datetime
import os

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "presenca.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            data TEXT NOT NULL,
            horario TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Presente', 'Falta')),
            observacao TEXT
        )
    """)
    conn.commit()
    conn.close()


@app.route("/", methods=["GET"])
def index():
    filtro_data = request.args.get("filtro_data", "")
    filtro_nome = request.args.get("filtro_nome", "")

    query = "SELECT * FROM registros WHERE 1=1"
    params = []

    if filtro_data:
        query += " AND data = ?"
        params.append(filtro_data)

    if filtro_nome:
        query += " AND nome LIKE ?"
        params.append(f"%{filtro_nome}%")

    query += " ORDER BY data DESC, horario DESC, id DESC"

    conn = get_conn()
    registros = conn.execute(query, params).fetchall()

    total = len(registros)
    presentes = sum(1 for r in registros if r["status"] == "Presente")
    faltas = total - presentes

    conn.close()

    return render_template(
        "index.html",
        registros=registros,
        hoje=date.today().isoformat(),
        agora=datetime.now().strftime("%H:%M"),
        filtro_data=filtro_data,
        filtro_nome=filtro_nome,
        total=total,
        presentes=presentes,
        faltas=faltas,
    )


@app.route("/adicionar", methods=["POST"])
def adicionar():
    nome = request.form.get("nome", "").strip()
    data_registro = request.form.get("data", "")
    horario = request.form.get("horario", "")
    status = request.form.get("status", "Presente")
    observacao = request.form.get("observacao", "").strip()

    if nome and data_registro and horario:
        conn = get_conn()
        conn.execute(
            "INSERT INTO registros (nome, data, horario, status, observacao) VALUES (?, ?, ?, ?, ?)",
            (nome, data_registro, horario, status, observacao),
        )
        conn.commit()
        conn.close()

    return redirect(url_for("index"))


@app.route("/excluir/<int:registro_id>", methods=["POST"])
def excluir(registro_id):
    conn = get_conn()
    conn.execute("DELETE FROM registros WHERE id = ?", (registro_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
