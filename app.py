from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_mysqldb import MySQL, MySQLdb
from flask import send_from_directory
import re
import base64
import os
import json
import uuid
import time

app = Flask(__name__)

application = app

app.secret_key = "aarz2005"

# configuracion de la base de datos

app.config["MYSQL_HOST"] = "sql.freedb.tech"
app.config["MYSQL_USER"] = "freedb_streetrp"
app.config["MYSQL_PASSWORD"] = "h@5E!S9SRJ83yAa"
app.config["MYSQL_DB"] = "freedb_streetrp"
mysql = MySQL(app)


@app.route("/")
def index():

    return render_template("login.html")


@app.route("/authError")
def authError():
    return render_template("401.html")


@app.route("/home")
def home():
    if "username" in session and session["role"] == "admin":
        conn = mysql.connection.cursor()
        conn.execute("SELECT * FROM palets")
        data = conn.fetchall()
        return render_template("home.html", data=data)
    else:
        return redirect(url_for("authError"))


@app.route("/admin")
def admin():
    if "username" in session and session["role"] == "admin":
        conn = mysql.connection.cursor()
        conn.execute("SELECT * FROM palets")
        data = conn.fetchall()
        con = mysql.connection.cursor()
        con.execute('SELECT * FROM users WHERE rol = "empleado"')
        dataempl = con.fetchall()
        return render_template("admin.html", data=data, dataempl=dataempl)
    else:
        return redirect(url_for("authError"))


@app.route("/entregar")
def entregas():

    if "username" in session and session["role"] == "empleado":
        id_empleado = str(session["userId"])
        print(id_empleado)
        conn = mysql.connection.cursor()
        conn.execute("SELECT * FROM palets WHERE empleado = %s", id_empleado)
        data = conn.fetchall()

        con = mysql.connection.cursor()

        return render_template("entregar.html", data=data)
    else:
        return redirect(url_for("authError"))


@app.route("/empleado")
def empleado():
    if "username" in session and session["role"] == "empleado":
        user = session["username"]
        print(user)
        return render_template("empleados.html", user=user)
    else:
        return redirect(url_for("authError"))


@app.route("/empleado/<string:albaran>")
def detail_empleado(albaran):
    empleado = session["userId"]
    conn = mysql.connection.cursor()
    conn.execute("SELECT * FROM palets WHERE palets.albaran = %s", (albaran,))
    data = conn.fetchone()

    return render_template("detail_entrega.html", data=data, empleado=empleado)


@app.route("/entrega/<string:empleado>/<string:albaran>")
def entrega(empleado, albaran):

    return render_template("entrega.html", albaran=albaran)


@app.route("/entrega_completa/<string:albaran>", methods=["POST"])
def entrega_completa(albaran):
    name = request.form["name"]
    dni = request.form["dni"]
    nota = request.form["notas"]
    entregado = 1
    albaran = albaran
    conn = mysql.connection.cursor()
    conn.execute(
        "UPDATE palets SET recibe_nombre = %s, recibe_dni = %s, nota = %s, entrega = %s WHERE albaran = %s",
        (name, dni, nota, entregado, albaran),
    )
    mysql.connection.commit()
    return redirect(url_for("empleado"))


# ruta paraguardar la firma
@app.route("/guardar_firma", methods=["POST"])
def guardar_firma():
    firma_base64 = request.form[
        "firma"
    ]  # Obtener la firma en base64 desde el formulario

    # Decodificar la firma desde base64 y guardarla como archivo PNG
    with open(f"firma_{uuid.uuid4()}.png", "wb") as f:
        f.write(base64.b64decode(firma_base64.split(",")[1]))
    # falta guardar la firma en el disco C
    return redirect(url_for("empleado"))


@app.route("/add_palet", methods=["POST"])
def add_palet():
    if request.method == "POST":
        id = request.form["id"]
        direccion = request.form["direccion"]
        peso = request.form["peso"]
        contacto = request.form["contacto"]
        fecha_entrega = request.form["fecha_entrega"]
        num_palets = request.form["palets"]
        tipo_palet = request.form["tipo_palet"]
        nota = request.form["nota"]
        despaletizado = request.form.get("despaletizado", False)
        conn = mysql.connection.cursor()
        conn.execute(
            "INSERT INTO palets (albaran, contacto, direccion, fecha_entrega, numpalets, peso, tipo_palet, nota, despaletizado) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                id,
                contacto,
                direccion,
                fecha_entrega,
                num_palets,
                peso,
                tipo_palet,
                nota,
                despaletizado,
            ),
        )
        mysql.connection.commit()
        return redirect(url_for("home"))


@app.route("/assign_palets", methods=["POST"])
def assign_palets():
    if request.method == "POST":
        selected_palets = request.form.getlist("selected_palets")
        conn = mysql.connection.cursor()
        for palet_id in selected_palets:
            conn.execute(
                "UPDATE palets SET empresa = %s WHERE id = %s", ("mam", palet_id)
            )
        mysql.connection.commit()
        return redirect(url_for("home"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["correo"]
        password = request.form["pass"]
        conn = mysql.connection.cursor()
        conn.execute(
            "SELECT * FROM `users` WHERE `nombre` = %s AND `password` = %s",
            (username, password),
        )
        account = conn.fetchone()

        mysql.connection.commit()

        if account:
            session["userId"] = account[0]
            session["username"] = account[2]
            session["role"] = account[1]

            if account[1] == "empresa":
                return redirect(url_for("home"))
            elif account[1] == "admin":
                return redirect(url_for("admin"))
            elif account[1] == "empleado":
                return redirect(url_for("empleado"))
        else:
            error = "Usuario o Contraseña incorrectos"
            return render_template("login.html", error=error)

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.pop("username", None)
    session.pop("role", None)
    return redirect(url_for("login"))


@app.route("/add_employed", methods=["POST"])
def add_employed():
    if request.method == "POST":
        nombre = request.form["nombre"]
        contacto = request.form["contacto"]
        correo = request.form["correo"]
        conn = mysql.connection.cursor()
        conn.execute(
            "INSERT INTO users (rol, nombre, correo, contacto) VALUES (%s, %s, %s, %s)",
            ("empleado", nombre, correo, contacto),
        )
        mysql.connection.commit()
        return redirect(url_for("admin"))


@app.route("/add_company", methods=["POST"])
def add_company():
    print(request.form)


@app.route("/assign_employed", methods=["POST"])
def assign_empolyed():
    if request.method == "POST":
        selected_palets = request.form.getlist("selected_palets")
        employed = request.form.get("employed")
        print(employed)
        conn = mysql.connection.cursor()
        for palet_id in selected_palets:
            conn.execute(
                "UPDATE palets SET empleado = %s WHERE id = %s",
                (str(employed), palet_id),
            )
        mysql.connection.commit()
        return redirect(url_for("assign_palets"))


@app.route("/img/<filename>")
def send_uploaded_file(filename):
    return send_from_directory("C:/imgmrms", filename)


@app.route("/upload_images/<string:albaran>", methods=["POST"])
def upload_images(albaran):
    print(albaran)
    images = request.json["imgBase64"]
    image_names = []  # Lista para guardar los nombres de las imágenes
    for img in images:
        img_data = base64.b64decode(img.split(",")[1])
        unique_filename = str(uuid.uuid4()) + ".png"  # Generate a unique filename
        with open(os.path.join("C:/imgmrms", unique_filename), "wb") as f:
            f.write(img_data)
        image_names.append(unique_filename)  # Agrega el nombre de la imagen a la lista

    # Convierte la lista de nombres de imágenes en una cadena de texto
    image_names_str = ", ".join(image_names)

    # Actualiza la fila existente con la cadena de nombres de imágenes
    cur = mysql.connection.cursor()
    cur.execute(
        "UPDATE palets SET img = %s WHERE albaran = %s", (image_names_str, albaran)
    )
    mysql.connection.commit()
    print("hola")

    return redirect(url_for("empleado"))


if __name__ == "__main__":
    app.run(debug=True)
