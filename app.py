import os
from datetime import date, datetime

from flask import (
    Flask,
    render_template,
    request,
    send_from_directory,
    abort,
    jsonify,
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_

app = Flask(__name__)

# --- Config -------------------------------------------------

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cases.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Carpeta donde estarán los PDFs u otros documentos
app.config["CASE_DOCS_DIR"] = os.path.join(app.root_path, "documents")

db = SQLAlchemy(app)

# --- Models -------------------------------------------------

case_tags = db.Table(
    "case_tags",
    db.Column("case_id", db.Integer, db.ForeignKey("case.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
)


class Case(db.Model):
    __tablename__ = "case"

    id = db.Column(db.Integer, primary_key=True)

    # Campos principales
    radicado = db.Column(db.String(50), nullable=False)
    fecha_laudo = db.Column(db.Date, nullable=True)

    title = db.Column(db.String(300), nullable=False)
    content = db.Column(db.Text, nullable=False)

    # Nombre de archivo del laudo (relativo a CASE_DOCS_DIR)
    doc_filename = db.Column(db.String(255), nullable=True)

    tags = db.relationship(
        "Tag",
        secondary=case_tags,
        lazy="subquery",
        backref=db.backref("cases", lazy=True),
    )


class Tag(db.Model):
    __tablename__ = "tag"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)


# --- DB init / datos de ejemplo ------------------------------

def init_db():
    """Crear tablas y sembrar datos demo si están vacías."""
    db.create_all()

    # Sembrar etiquetas si no hay ninguna
    if not Tag.query.first():
        arbitraje = Tag(name="arbitraje")
        construccion = Tag(name="construcción")
        seguros = Tag(name="seguros")
        consumo = Tag(name="consumo")

        db.session.add_all([arbitraje, construccion, seguros, consumo])
        db.session.commit()

    # Obtener tags
    arbitraje = Tag.query.filter_by(name="arbitraje").first()
    construccion = Tag.query.filter_by(name="construcción").first()
    seguros = Tag.query.filter_by(name="seguros").first()
    consumo = Tag.query.filter_by(name="consumo").first()

    # Sembrar casos si no hay ninguno
    if not Case.query.first():
        c1 = Case(
            radicado="2022 A 0048",
            fecha_laudo=date(2025, 1, 24),
            title="Radicado 2022 A 0048 – Luz Indely Mejía Berrío vs. Héctor Giovanny Castaño Díaz y otros",
            content=(
                "Radicado: 2022 A 0048. Laudo proferido el 24 de enero de 2025.\n\n"
                "Partes: LUZ INDELY MEJÍA BERRÍO contra HÉCTOR GIOVANNY CASTAÑO DÍAZ, "
                "JUAN CARLOS BEDOYA VALENCIA y PAULA ANDREA BEDOYA VALENCIA "
                "(litisconsorte necesaria)."
            ),
            tags=[arbitraje, consumo],
            doc_filename="2022 A 0048 22-01-2025.pdf",
        )

        c2 = Case(
            radicado="2024 A 0036",
            fecha_laudo=date(2025, 2, 17),
            title="Radicado 2024 A 0036 – Construcciones Aplomo S.A.S. vs. Promotora & Constructora de Proyectos S.A.S.",
            content=(
                "Radicado: 2024 A 0036. Laudo proferido el 17 de febrero de 2025.\n\n"
                "Partes: CONSTRUCCIONES APLOMO S.A.S. contra "
                "PROMOTORA & CONSTRUCTORA DE PROYECTOS S.A.S."
            ),
            tags=[arbitraje, construccion],
            doc_filename="2024 A 0036 17-02-2025.pdf",
        )

        c3 = Case(
            radicado="2024 A 0012",
            fecha_laudo=date(2025, 4, 9),
            title="Radicado 2024 A 0012 – Constructivamente S.A.S. vs. Arturo García Isaac",
            content=(
                "Radicado: 2024 A 0012. Laudo proferido el 9 de abril de 2025.\n\n"
                "Partes: CONSTRUCTIVAMENTE S.A.S. contra ARTURO GARCÍA ISAAC."
            ),
            tags=[arbitraje, construccion],
            doc_filename="2024 A 0012 09-04-2025.pdf",
        )

        c4 = Case(
            radicado="2024 A 0013",
            fecha_laudo=date(2025, 4, 9),
            title="Radicado 2024 A 0013 – C.I. Hermeco S.A. vs. Allianz Seguros S.A.",
            content=(
                "Radicado: 2024 A 0013. Laudo proferido el 9 de abril de 2025.\n\n"
                "Partes: C.I. HERMECO S.A. contra ALLIANZ SEGUROS S.A."
            ),
            tags=[arbitraje, seguros],
            doc_filename="2024 A 0013 09-04-2025.pdf",
        )

        c5 = Case(
            radicado="2024 A 0020",
            fecha_laudo=date(2025, 4, 10),
            title="Radicado 2024 A 0020 – Inverbetancur S.A.S. vs. Guillermo León Ruíz Tamayo y otra",
            content=(
                "Radicado: 2024 A 0020. Laudo proferido el 10 de abril de 2025.\n\n"
                "Partes: INVERBETANCUR S.A.S. contra GUILLERMO LEÓN RUÍZ TAMAYO y "
                "ALTAGRACIA DEL SOCORRO GUTIÉRREZ RESTREPO."
            ),
            tags=[arbitraje, construccion],
            doc_filename="2024 A 0020 10-04-2025.pdf",
        )

        c6 = Case(
            radicado="2024 A 0052",
            fecha_laudo=date(2025, 4, 30),
            title="Radicado 2024 A 0052 – Leonel Chica vs. Loyalty World S.A.S.",
            content=(
                "Radicado: 2024 A 0052. Laudo proferido el 30 de abril de 2025.\n\n"
                "Partes: LEONEL CHICA contra LOYALTY WORLD S.A.S."
            ),
            tags=[arbitraje, consumo],
            doc_filename="2024 A 0052 30-04-2025.pdf",
        )

        c7 = Case(
            radicado="2024 A 0006",
            fecha_laudo=date(2025, 5, 5),
            title="Radicado 2024 A 0006 – Inversiones ConsumAR S.A.S. vs. Operadora Colombiana de Cines S.A.S.",
            content=(
                "Radicado: 2024 A 0006. Laudo proferido el 5 de mayo de 2025.\n\n"
                "Partes: INVERSIONES CONSUMAR S.A.S. contra OPERADORA COLOMBIANA DE CINES S.A.S."
            ),
            tags=[arbitraje, consumo],
            doc_filename="2024 A 0006 05-05-2025.pdf",
        )

        db.session.add_all([c1, c2, c3, c4, c5, c6, c7])
        db.session.commit()


# --- Ruta de búsqueda ---------------------------------------

@app.route("/", methods=["GET"])
def search():
    q = (request.args.get("q") or "").strip()
    selected_tags_raw = request.args.getlist("tag")  # checkboxes: name="tag"
    selected_tag_ids = []
    for t in selected_tags_raw:
        try:
            selected_tag_ids.append(int(t))
        except ValueError:
            pass

    all_tags = Tag.query.order_by(Tag.name.asc()).all()

    query = Case.query

    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(
                Case.title.ilike(pattern),
                Case.content.ilike(pattern),
                Case.radicado.ilike(pattern),
            )
        )

    if selected_tag_ids:
        # lógica “cualquiera de estas etiquetas”
        query = query.filter(Case.tags.any(Tag.id.in_(selected_tag_ids)))

    results = query.order_by(Case.id.desc()).all()

    return render_template(
        "search.html",
        tags=all_tags,
        results=results,
        q=q,
        selected_tag_ids=selected_tag_ids,
    )


# --- Ruta de descarga ---------------------------------------

@app.route("/cases/<int:case_id>/download")
def download_case(case_id):
    case = Case.query.get_or_404(case_id)

    if not case.doc_filename:
        abort(404)

    docs_dir = app.config["CASE_DOCS_DIR"]
    filepath = os.path.join(docs_dir, case.doc_filename)
    if not os.path.isfile(filepath):
        abort(404)

    return send_from_directory(
        docs_dir,
        case.doc_filename,
        as_attachment=True,
    )


# --- Ruta de carga vía JSON ---------------------------------

@app.route("/api/cases", methods=["POST"])
def create_case():
    """
    Endpoint simple para registrar un caso nuevo.

    JSON esperado:
    {
      "radicado": "2025 A 0001",
      "fecha_laudo": "2025-06-30",         # opcional, formato ISO (YYYY-MM-DD)
      "title": "Título del caso",
      "content": "Resumen o notas del laudo",
      "path": "2025 A 0001 30-06-2025.pdf",  # o "doc_filename"
      "tags": ["arbitraje", "construcción"]
    }
    """
    data = request.get_json(silent=True) or {}

    radicado = (data.get("radicado") or "").strip()
    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()
    doc_filename = (data.get("doc_filename") or data.get("path") or "").strip()
    tags_in = data.get("tags") or []
    fecha_laudo_str = (data.get("fecha_laudo") or "").strip()

    if not radicado or not title or not content or not doc_filename:
        return (
            jsonify(
                {
                    "error": "radicado, title, content y path/doc_filename son obligatorios",
                }
            ),
            400,
        )

    # Parsear fecha del laudo si viene
    fecha_laudo = None
    if fecha_laudo_str:
        try:
            fecha_laudo = datetime.strptime(fecha_laudo_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "fecha_laudo debe tener formato YYYY-MM-DD"}), 400

    if not isinstance(tags_in, list):
        return jsonify({"error": "tags debe ser una lista de nombres de etiqueta"}), 400

    tag_objects = []
    for raw_name in tags_in:
        if not isinstance(raw_name, str):
            continue
        name = raw_name.strip()
        if not name:
            continue

        tag = Tag.query.filter_by(name=name).first()
        if not tag:
            tag = Tag(name=name)
            db.session.add(tag)
        tag_objects.append(tag)

    new_case = Case(
        radicado=radicado,
        fecha_laudo=fecha_laudo,
        title=title,
        content=content,
        doc_filename=doc_filename,
        tags=tag_objects,
    )

    db.session.add(new_case)
    db.session.commit()

    return (
        jsonify(
            {
                "id": new_case.id,
                "radicado": new_case.radicado,
                "fecha_laudo": new_case.fecha_laudo.isoformat()
                if new_case.fecha_laudo
                else None,
                "title": new_case.title,
                "doc_filename": new_case.doc_filename,
                "tags": [t.name for t in new_case.tags],
            }
        ),
        201,
    )


# --- Main ---------------------------------------------------

if __name__ == "__main__":
    # Asegurar carpeta de documentos
    os.makedirs(app.config["CASE_DOCS_DIR"], exist_ok=True)

    # Inicializar DB + sembrar datos (para demo)
    with app.app_context():
        init_db()

    app.run(host="0.0.0.0")
