from uuid import uuid4
from flask import Flask, render_template, request, redirect, url_for, flash
import redis
import json
from config import get_redis_client

app = Flask(__name__)
app.config.from_mapping(
    SECRET_KEY="dev-secret-key"
)

r = get_redis_client()
BOOK_SET_KEY = "libros:ids"
BOOK_KEY_PREFIX = "libro:"

def book_key(book_id: str) -> str:
    return f"{BOOK_KEY_PREFIX}{book_id}"

def serialize_book(book_id: str, data: dict) -> None:
    key = book_key(book_id)
    r.hset(key, mapping=data)
    r.sadd(BOOK_SET_KEY, book_id)

def deserialize_book(book_id: str) -> dict:
    key = book_key(book_id)
    book = r.hgetall(key)
    if not book:
        return None
    book["id"] = book_id
    return book

def all_books() -> list:
    ids = r.smembers(BOOK_SET_KEY) or set()
    books = []
    for bid in ids:
        b = deserialize_book(bid)
        if b:
            books.append(b)
    books.sort(key=lambda x: x.get("titulo", "").lower())
    return books

@app.route("/", methods=["GET"])
def index():
    query = request.args.get("q", "").strip()
    field = request.args.get("field", "titulo")

    books = all_books()
    if query:
        q = query.lower()
        if field == "titulo":
            books = [b for b in books if q in b.get("titulo", "").lower()]
        elif field == "autor":
            books = [b for b in books if q in b.get("autor", "").lower()]
        elif field == "genero":
            books = [b for b in books if q in b.get("genero", "").lower()]

    return render_template("index.html", books=books, q=query, field=field)

@app.route("/agregar", methods=["GET", "POST"])
def agregar():
    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        autor = request.form.get("autor", "").strip()
        genero = request.form.get("genero", "").strip()
        estado = request.form.get("estado", "").strip()

        if not titulo or not autor:
            flash("Título y autor son obligatorios.", "danger")
            return render_template("add_edit.html", book=request.form, action="Agregar")

        for b in all_books():
            if b.get("titulo", "").lower() == titulo.lower() and b.get("autor", "").lower() == autor.lower():
                flash("Ya existe un libro con el mismo título y autor.", "warning")
                return render_template("add_edit.html", book=request.form, action="Agregar")

        book_id = str(uuid4())
        data = {"titulo": titulo, "autor": autor, "genero": genero, "estado": estado}
        serialize_book(book_id, data)
        flash("Libro agregado correctamente.", "success")
        return redirect(url_for("index"))

    return render_template("add_edit.html", book=None, action="Agregar")

@app.route("/editar/<book_id>", methods=["GET", "POST"])
def editar(book_id):
    book = deserialize_book(book_id)
    if not book:
        flash("Libro no encontrado.", "danger")
        return redirect(url_for("index"))

    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        autor = request.form.get("autor", "").strip()
        genero = request.form.get("genero", "").strip()
        estado = request.form.get("estado", "").strip()

        if not titulo or not autor:
            flash("Título y autor son obligatorios.", "danger")
            return render_template("add_edit.html", book=request.form, action="Editar")

        data = {"titulo": titulo, "autor": autor, "genero": genero, "estado": estado}
        serialize_book(book_id, data)
        flash("Libro actualizado correctamente.", "success")
        return redirect(url_for("index"))

    return render_template("add_edit.html", book=book, action="Editar")

@app.route("/eliminar/<book_id>", methods=["POST"])
def eliminar(book_id):
    key = book_key(book_id)
    if r.exists(key):
        r.delete(key)
        r.srem(BOOK_SET_KEY, book_id)
        flash("Libro eliminado.", "success")
    else:
        flash("Libro no encontrado.", "danger")
    return redirect(url_for("index"))

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
