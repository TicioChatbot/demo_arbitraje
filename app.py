import os
from datetime import datetime

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
    name = db.Column(db.String(100), unique=True, nullable=False)


# --- DB init / datos de ejemplo ------------------------------

def init_db():
    """Crear tablas y sembrar datos demo si están vacías."""
    db.create_all()

    # Si ya hay casos, no volvemos a sembrar
    if Case.query.first():
        return

    # Datos provenientes de tu JSON (adaptados a Python)
    cases_data = [
        {
            "radicado": "2024 A 0052",
            "fecha_laudo": "2025-04-30",
            "title": "Leonel Chica vs. Loyalty World S.A.S.",
            "content": """En el plano procesal, el laudo analiza la existencia, validez y oponibilidad del pacto arbitral contenido en el Contrato de Afiliación No. MED1298, la jurisdicción y competencia del tribunal conforme a la Ley 1563 de 2012, así como la correcta integración del tribunal, la capacidad de las partes y el cumplimiento de los presupuestos procesales (demanda en forma, legitimación en la causa, integración del contradictorio y término del proceso). También se valora la inactividad de la parte convocada, que no contestó la demanda ni asistió a las audiencias, y las consecuencias probatorias de su incomparecencia y silencio frente a las afirmaciones de la parte convocante.

En el plano sustancial, el tribunal estudia si procede declarar la nulidad relativa del contrato por dolo como vicio del consentimiento, a partir de la información engañosa y las maniobras desplegadas por los empleados de Loyalty World para inducir al demandante a suscribir un contrato de afiliación distinto a lo ofrecido verbalmente. Igualmente examina el eventual incumplimiento de los deberes de información consagrados en el Estatuto del Consumidor, la eficacia de la cláusula de permanencia mínima de cuatro años considerada como cláusula abusiva, y las consecuencias económicas derivadas del crédito de consumo gestionado con el Banco de Bogotá (cuotas, intereses, seguros y demás cargos) para efectos de la restitución de lo pagado y la indemnización de perjuicios.""",
            "path": "2024 A 0052 30-04-2025.pdf",
            "tags": [
                "pacto_arbitral",
                "competencia_tribunal",
                "presupuestos_procesales",
                "incomparecencia_demandado",
                "nulidad_relativa_por_dolo",
                "estatuto_consumidor",
                "clausula_abusiva_permanencia_minima",
                "informacion_al_consumidor",
            ],
        },
        {
            "radicado": "2024 A 0036",
            "fecha_laudo": "2025-02-17",
            "title": "Construcciones A Plomo S.A.S. vs. Promotora & Constructora de Proyectos S.A.S.",
            "content": """En el plano procesal, el laudo examina la existencia y alcance del pacto arbitral contenido en los contratos de obra 024 – Portello y 033 – Oz, así como la competencia del tribunal bajo la Ley 1563 de 2012 y el Reglamento de Arbitraje Social de la Cámara de Comercio de Medellín. Se verifica el cumplimiento de los presupuestos procesales y materiales (capacidad, representación, demanda en forma, legitimación en la causa, interés para obrar, ausencia de cosa juzgada, caducidad, transacción o conciliación) y se analiza el trámite arbitral en rebeldía de la convocada, resaltando las consecuencias de la falta de contestación de la demanda y de la inactividad procesal de la demandada, en particular la confesión ficta prevista en el artículo 97 del Código General del Proceso, así como la fijación, cómputo y prórroga del término para proferir el laudo en un escenario de arbitraje social.

En el plano sustancial, el tribunal estudia la relación contractual de obra civil entre las partes, centrando el problema jurídico en determinar si las sumas retenidas (el 10% del valor de los contratos) debían ser reembolsadas al contratista una vez terminadas las obras. A partir de la cláusula de forma de pago y del parágrafo sobre el retenido, se define la naturaleza de estas sumas como valores causados y reconocidos en actas de corte de obra y comunicaciones posteriores, sometidos a una condición temporal y a la elaboración de un memorando de entrega de retenido que el contratante nunca expidió dentro del plazo de un mes. El laudo concluye, con apoyo en el principio pacta sunt servanda y en la buena fe contractual, que la convocada incumplió la carga de emitir oportunamente dicho memorando y no probó la supuesta menor obra ejecutada ni el pago en exceso, por lo que debe reembolsar los valores retenidos debidamente indexados, rechazando la compensación unilateral pretendida por la contratante.""",
            "path": "2024 A 0036 17-02-2025.pdf",
            "tags": [
                "pacto_arbitral",
                "competencia_tribunal",
                "rebeldia_demandado",
                "confesion_ficta",
                "contrato_de_obra",
                "retenido_contractual",
                "incumplimiento_pago",
                "indexacion_monetaria",
            ],
        },
        {
            "radicado": "2024 A 0020",
            "fecha_laudo": "2025-04-10",
            "title": "INVERBETANCUR S.A.S. vs. Guillermo León Ruiz Tamayo y Altagracia del Socorro Gutiérrez Restrepo",
            "content": """En el plano procesal, el laudo verifica de manera sistemática los presupuestos procesales de capacidad, demanda en forma, competencia del tribunal y legitimación en la causa para la demanda principal y la reconvención, a partir de la cláusula compromisoria del contrato de arrendamiento y su modificación en un trámite anterior. Se describen las actuaciones relevantes del trámite (admisión de la demanda, integración de la litis con la reconvención, decreto y práctica de pruebas, alegatos y saneamiento), se analiza la arbitrabilidad subjetiva y objetiva, y se estudia en detalle la excepción de cosa juzgada parcial frente a dos laudos arbitrales previos, contrastando identidad de partes, objeto y causa a la luz del artículo 302 del Código General del Proceso y la jurisprudencia de la Corte Suprema de Justicia.

En el plano sustancial, el tribunal centra la controversia en el contrato de arrendamiento del lote destinado a estación de servicio de combustible y en la imputación recíproca de incumplimientos: de un lado, la arrendataria sostiene que los arrendadores perturbaron el uso pacífico del inmueble mediante cambios de candados, restricciones de acceso a agua e instalaciones, quejas ante la autoridad ambiental y negativa de permisos para muestras, lo que habría generado pérdida de utilidades, costos adicionales y activación de la cláusula penal; del otro, los arrendadores alegan que la arrendataria incumplió obligaciones de mantenimiento, uso adecuado y obtención y conservación de permisos ambientales, causando sanciones y deterioro del bien, así como cánones dejados de pagar. El tribunal estudia el alcance de las obligaciones contractuales de cada parte, la carga probatoria sobre los hechos alegados, la procedencia de las indemnizaciones reclamadas y la aplicación de la cláusula penal y del juramento estimatorio en este contexto.""",
            "path": "2024 A 0020 10-04-2025.pdf",
            "tags": [
                "clausula_compromisoria",
                "competencia_tribunal",
                "cosa_juzgada_parcial",
                "demanda_de_reconvencion",
                "contrato_de_arrendamiento",
                "incumplimiento_contractual",
                "obligaciones_ambientales",
                "clausula_penal",
            ],
        },
        {
            "radicado": "2024 A 0013",
            "fecha_laudo": "2025-04-09",
            "title": "CONSTRUCTIVAMENTE S.A.S. vs. Arturo García Isaac",
            "content": """En el plano procesal, el laudo examina la existencia, alcance y posterior modificación de la cláusula compromisoria del contrato de administración delegada para el proyecto Green Mecano – Casa Arturo García, así como la correcta integración del tribunal y su competencia subjetiva y objetiva conforme a la Ley 1563 de 2012. Se estudia el trámite de la demanda principal y de la demanda de reconvención, la admisión de ambas, los recursos contra el auto admisorio, las excepciones de mérito, la audiencia de conciliación, la fijación y pago de gastos, la práctica de una amplia actividad probatoria (documentos, testimonios, interrogatorios, dictámenes periciales, ratificación de documentos y juramento estimatorio) y la posterior reconstrucción parcial del expediente por problemas en la plataforma MASCINFO. El tribunal también analiza el decreto de pruebas de oficio, la incidencia de la acción de tutela promovida contra dichas decisiones probatorias y concluye sobre la validez de la actuación y la concurrencia de los presupuestos procesales para dictar un laudo de mérito.

En el plano sustancial, el tribunal centra la controversia en el contrato de administración delegada de obra suscrito para la construcción de la vivienda Green Mecano – Casa Arturo García y en la imputación recíproca de incumplimientos: de un lado, CONSTRUCTIVAMENTE S.A.S. reclama el pago de un saldo importante por concepto de obra ejecutada y honorarios, apoyándose en los sobrecostos derivados de cambios de diseño, mayores cantidades de obra y un porcentaje de avance cercano al 95–99%; de otro lado, ARTURO GARCÍA ISAAC sostiene que cumplió integralmente sus obligaciones de pago, incluidos aportes al fondo rotatorio y suministro de materiales, y que fue el contratista quien abandonó la obra sin terminarla, sin rendir cuentas claras ni entregar información presupuestal y contable acorde con lo pactado. El laudo aborda la naturaleza jurídica del contrato de administración delegada, el régimen de riesgos y sobrecostos, el alcance de las obligaciones de rendición de cuentas y de entrega de la obra terminada y habitable, la procedencia de la excepción de contrato no cumplido y del cobro de mayores sumas, así como la legitimidad de la terminación anticipada y la prueba de los sobrecostos y perjuicios reclamados por el convocado en reconvención.""",
            "path": "2024 A 0013 09-04-2025.pdf",
            "tags": [
                "clausula_compromisoria",
                "competencia_tribunal",
                "demanda_de_reconvencion",
                "reconstruccion_expediente",
                "contrato_administracion_delegada",
                "contrato_de_obra",
                "incumplimiento_contractual",
                "sobrecostos_obra",
            ],
        },
        {
            "radicado": "2024 A 0012",
            "fecha_laudo": "2025-04-09",
            "title": "C.I. HERMECO S.A. vs. Allianz Seguros S.A.",
            "content": """En el plano procesal, el laudo constata el cumplimiento de los presupuestos procesales (demanda en forma, capacidad, representación y legitimación de las partes) y la validez del pacto arbitral contenido en la póliza de seguro de infidelidad y riesgos financieros, así como la correcta integración del tribunal y su competencia objetiva y subjetiva conforme a la Ley 1563 de 2012. Se reseñan las principales actuaciones: presentación y subsanación de la demanda, contestación con excepciones de mérito, objeciones al juramento estimatorio, reforma de la demanda y su contestación, fijación de gastos y honorarios, celebración de la primera audiencia de trámite donde se declara la competencia, decreto y práctica de pruebas documentales, testimoniales, interrogatorios y exhibición de documentos, así como las discusiones sobre la eventual renuencia en la exhibición y el alcance del artículo 267 del Código General del Proceso, concluyendo que no se configuran nulidades ni causales que impidan un pronunciamiento de mérito.

En el plano sustancial, el tribunal examina el contrato de seguro de infidelidad y riesgos financieros (póliza No. 022729240/0) suscrito entre HERMECO y ALLIANZ, centrando la controversia en la ocurrencia del siniestro derivado de una estafa por suplantación de la representante legal de HERMECO y en la procedencia de la cobertura bajo el amparo de falsificación extendida. Se analizan las pretensiones de HERMECO para que se declare injustificada la objeción de la aseguradora y se ordene el pago del límite asegurado, frente a las excepciones de mérito de ALLIANZ, que sostienen que las pérdidas están excluidas por la falta de segregación de funciones y de doble control en las transferencias (exclusiones 26 y 31), así como por otros límites y deducibles del contrato. El tribunal interpreta de manera restrictiva el clausulado de la póliza, el alcance técnico del control dual y la segregación de funciones según los manuales y prácticas internas de HERMECO, valora la prueba sobre la forma real en que se ejecutaron las operaciones bancarias y define si se configuraron o no las exclusiones invocadas, así como la procedencia de los intereses moratorios, la suma asegurada reclamada y las demás consecuencias patrimoniales del siniestro.""",
            "path": "2024 A 0012 09-04-2025.pdf",
            "tags": [
                "clausula_compromisoria",
                "presupuestos_procesales",
                "competencia_tribunal",
                "exhibicion_documental",
                "contrato_de_seguro",
                "poliza_infidelidad_y_riesgos_financieros",
                "exclusiones_de_cobertura",
                "interpretacion_restrictiva_seguro",
            ],
        },
        {
            "radicado": "2024 A 0006",
            "fecha_laudo": "2025-05-05",
            "title": "INVERSIONES CONSUMAR S.A.S. vs. OPERADORA COLOMBIANA DE CINES S.A.S.",
            "content": """En el plano procesal, el laudo verifica la existencia, validez, eficacia y oponibilidad de la cláusula compromisoria del contrato de arrendamiento del local comercial 330 del Centro Comercial City Plaza, así como la competencia objetiva y subjetiva del tribunal para conocer las pretensiones de la demanda principal y de la demanda de reconvención, con la salvedad de la pretensión relativa a la comisión para la entrega del inmueble. Se detalla el trámite arbitral (admisión de la demanda, contestación con objeción al juramento estimatorio, demanda de reconvención, traslados, fijación de gastos, primera audiencia de trámite, decreto y práctica de pruebas documentales, testimoniales, interrogatorios y peritajes, así como sucesivas audiencias de pruebas y alegatos), se aprecia la tacha de sospecha frente a un testigo relacionado con el apoderado de la convocante conforme al artículo 211 del Código General del Proceso y a la jurisprudencia constitucional, y se concluye que, pese a dicho interés, su testimonio solo puede valorarse con mayor rigor dentro del conjunto probatorio, sin que se configure nulidad ni vicio procesal que impida proferir la decisión de fondo.

En el plano sustancial, el tribunal centra el debate en la existencia, vigencia y alcances del contrato de arrendamiento de local comercial suscrito en 2013 y modificado por el Otrosí No. 1 de 2020, a partir del cual se discute si el vínculo terminó el 17 de septiembre de 2023, como sostiene la arrendadora, o si se renovó en los términos de los artículos 518 y 520 del Código de Comercio, como alega la arrendataria. Para ello, analiza el carácter tuitivo del régimen de arrendamiento de local comercial, la distinción entre prórroga y renovación, la naturaleza de la cláusula tercera del Otrosí No. 1 y su posible ineficacia por contrariar normas imperativas (artículo 524 del Código de Comercio), así como las comunicaciones cruzadas sobre la renovación, la alegada necesidad de desahucio, los señalamientos de mala fe y abuso del derecho, y la procedencia de las pretensiones principales y subsidiarias relativas a la restitución del inmueble, la cláusula penal, la regulación judicial del canon de arrendamiento posterior al 18 de septiembre de 2023, los intereses moratorios y la fijación del valor del canon con apoyo en los diversos dictámenes periciales de parte y de contradicción.""",
            "path": "2024 A 0006 05-05-2025.pdf",
            "tags": [
                "clausula_compromisoria",
                "competencia_tribunal",
                "demanda_de_reconvencion",
                "tacha_de_testigo",
                "contrato_de_arrendamiento",
                "derecho_de_renovacion",
                "desahucio_comercial",
                "canon_de_arrendamiento",
            ],
        },
        {
            "radicado": "2022 A 0048",
            "fecha_laudo": "2025-01-24",
            "title": "LUZ INDELY MEJÍA BERRÍO vs. HÉCTOR GIOVANNY CASTAÑO DÍAZ, JUAN CARLOS BEDOYA VALENCIA y PAULA ANDREA BEDOYA VALENCIA (litisconsorte necesaria)",
            "content": """En el plano procesal, el tribunal analiza la existencia, validez y alcance de las cláusulas compromisorias incluidas tanto en la promesa inicial como en la nota aclaratoria, para afirmar su competencia frente a todos los sujetos involucrados, incluyendo la integración de Paula Andrea Bedoya Valencia como litisconsorte necesaria en el polo pasivo por su doble condición de promitente compradora y apoderada general de uno de los demandados. Se estudian las excepciones de mérito relacionadas con la falta de conciliación como requisito de procedibilidad, la alegada falta de competencia, la indebida integración del contradictorio, la existencia de pleito acabado, compensación, prejudicialidad y otras defensas procesales, concluyendo que varias de ellas carecen de soporte fáctico y que la referencia a la conciliación se hizo con base en una ley ya derogada (Ley 640 de 2001) frente a la entrada en vigor de la Ley 2220 de 2022. Igualmente se abordan las medidas cautelares sobre el inmueble, las solicitudes de amparo de pobreza, las tachas de sospecha a testigos cercanos a las partes y las suspensiones convencionales del proceso, llevando al saneamiento integral del trámite y a la constatación de que no existen nulidades que impidan decidir de fondo.

En el plano sustancial, el tribunal concluye que el negocio denominado por las partes contrato de promesa de compraventa, que en realidad se estructura como una promesa de permuta de lote por unidades inmobiliarias futuras, complementada con una nota aclaratoria, carece de validez por no cumplir los requisitos legales de la promesa de contrato, por lo que se declara la nulidad del pacto y se descarta cualquier análisis de incumplimiento bilateral. A partir de esa nulidad, se ordena la restitución recíproca de las prestaciones: la demandante recupera la plena propiedad del inmueble identificado originalmente con la matrícula 001-693546, hoy 001-1288992 tras el englobe, con todas sus accesiones y edificaciones, mientras que debe restituir a los demandados las sumas recibidas por precio y financiación del proyecto, y estos son condenados a pagar a la actora los frutos percibidos del bien durante el periodo comprendido entre la presentación de la demanda y la fecha del laudo. El tribunal deja a salvo eventuales reclamaciones sobre el valor de las mejoras útiles y las relaciones con terceros acreedores hipotecarios, indicando que esas controversias tendrían que ventilarse en procesos judiciales distintos.""",
            "path": "2022 A 0048 22-01-2025.pdf",
            "tags": [
                "clausula_compromisoria",
                "competencia_tribunal",
                "litisconsorcio_necesario",
                "medidas_cautelares",
                "promesa_de_compraventa",
                "promesa_de_permuta",
                "nulidad_absoluta",
                "restitucion_de_prestaciones",
                "mejoras_utiles",
            ],
        },
    ]

    for item in cases_data:
        fecha_laudo = datetime.strptime(item["fecha_laudo"], "%Y-%m-%d").date()

        tag_objects = []
        for tag_name in item["tags"]:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            tag_objects.append(tag)

        case = Case(
            radicado=item["radicado"],
            fecha_laudo=fecha_laudo,
            title=item["title"],
            content=item["content"],
            doc_filename=item["path"],
            tags=tag_objects,
        )
        db.session.add(case)

    db.session.commit()


# --- Ruta de búsqueda (tags incluidos en keyword, orden, paginación) ---

@app.route("/", methods=["GET"])
def search():
    q = (request.args.get("q") or "").strip()
    selected_tags_raw = request.args.getlist("tag")  # checkboxes: name="tag"
    sort = request.args.get("sort", "fecha_desc")
    page = request.args.get("page", 1, type=int)
    per_page = 5

    # Parsear IDs de tags seleccionados
    selected_tag_ids = []
    for t in selected_tags_raw:
        try:
            selected_tag_ids.append(int(t))
        except ValueError:
            pass

    all_tags = Tag.query.order_by(Tag.name.asc()).all()

    query = Case.query

    # Búsqueda por palabra clave: radicado, título, contenido y nombre de etiqueta
    if q:
        pattern = f"%{q}%"
        query = (
            query.outerjoin(Case.tags)
            .filter(
                or_(
                    Case.title.ilike(pattern),
                    Case.content.ilike(pattern),
                    Case.radicado.ilike(pattern),
                    Tag.name.ilike(pattern),
                )
            )
            .distinct()
        )

    # Filtro por tags (facetas)
    if selected_tag_ids:
        query = query.filter(Case.tags.any(Tag.id.in_(selected_tag_ids)))

    # Orden
    if sort == "fecha_asc":
        order_clause = Case.fecha_laudo.asc()
    elif sort == "radicado_asc":
        order_clause = Case.radicado.asc()
    else:  # default: fecha_desc
        order_clause = Case.fecha_laudo.desc()

    # Paginación
    pagination = db.paginate(
        query.order_by(order_clause),
        page=page,
        per_page=per_page,
        error_out=False,
    )
    results = pagination.items

    return render_template(
        "search.html",
        tags=all_tags,
        results=results,
        q=q,
        selected_tag_ids=selected_tag_ids,
        sort=sort,
        pagination=pagination,
        per_page=per_page,
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
      "tags": ["pacto_arbitral", "contrato_de_obra"]
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

    # Escuchar en 0.0.0.0 para acceso desde red local
    app.run(host="0.0.0.0", port=5000, debug=True)
