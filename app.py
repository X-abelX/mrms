from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL, MySQLdb
import re

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
    return render_template("index.html")


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


@app.route("/empleado")
def empleado():
    if "username" in session and session["role"] == "empleado":
        conn = mysql.connection.cursor()
        conn.execute('SELECT * FROM users WHERE rol = "empleado"')
        data = conn.fetchall()

        con = mysql.connection.cursor()

        query = """
        SELECT 
            users.nombre,
            users.contacto,
            COUNT(palets.empleado) AS cantidad_palets
        FROM 
            users
        INNER JOIN 
            palets  ON users.id = palets.empleado
        GROUP BY 
            palets.empleado
        """
        con.execute(query)
        palets = con.fetchall()

        return render_template("empleados.html", data=data, palets=palets)
    else:
        return redirect(url_for("authError"))


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
            # session["loggedin"] = True
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


if __name__ == "__main__":
    app.run(debug=True)
