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

    # Árbitro o tribunal
    arbiter = db.Column(db.String(200), nullable=True)

    # Palabras clave “genéricas” (una o varias, separadas por espacios)
    keywords = db.Column(db.String(255), nullable=True)

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

    # Datos provenientes de tu JSON (adaptados a Python) + árbitro + keywords demo
    cases_data = [
        {
            "radicado": "2024 A 0052",
            "fecha_laudo": "2025-04-30",
            "title": "Leonel Chica vs. Loyalty World S.A.S.",
            "arbiter": "Árbitro único: Ana María López",
            "keywords": "consumo dolo afiliacion credito",
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
            "arbiter": "Tribunal: Carlos Restrepo, Laura Vélez, Jorge Ramírez",
            "keywords": "obra retenido pago indemnizacion",
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
            "arbiter": "Árbitro único: Beatriz Cárdenas",
            "keywords": "arrendamiento estacion_servicio ambiente clausula_penal",
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
            "arbiter": "Tribunal: Diana Ruiz, Camilo Salazar, Paula Hoyos",
            "keywords": "administracion_delegada vivienda sobrecostos cuentas",
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
            "arbiter": "Tribunal: Jorge Nieto, Andrea Pérez, Luis Martínez",
            "keywords": "seguro infidelidad estafa cobertura exclusiones",
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
            "arbiter": "Tribunal: Juliana Torres, Felipe Arango, Ricardo Mejía",
            "keywords": "arrendamiento local_comercial renovacion desahucio canon",
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
            "arbiter": "Árbitro único: Sebastián Herrera",
            "keywords": "promesa_permuta nulidad_relativa inmueble frutos",
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
    {
        "radicado": "2022 A 0063",
        "fecha_laudo": "2024-11-28",
        "title": "ORION HOLDINGS S.A.S. vs. Lleras Holdings S.A.S., Bradley H. Hinkelman, Propiedad Raíz Casacol S.A.S. y Camila Caycedo Prieto",
        "content": (
            "En el plano procesal, el laudo arbitral resalta la existencia y alcance de la cláusula "
            "compromisoria estatutaria de Lleras Holdings S.A.S. y la competencia del tribunal para "
            "conocer no solo de las controversias derivadas del contrato social, sino también de las "
            "diferencias relacionadas con el acuerdo de accionistas, en el marco de una coligación negocial. "
            "Se estudian la regularidad de la convocatoria y celebración de la asamblea, la integración de "
            "litisconsortes (incluida la participación de la usufructuaria de acciones), la reforma y "
            "admisión de la demanda, las excepciones de mérito sobre indebida acumulación de pretensiones "
            "y falta de competencia, así como la inexistencia de nulidades procesales que impidieran un "
            "pronunciamiento de fondo. El tribunal analiza además el comportamiento procesal de las partes, "
            "la admisión de la demanda reformada, la contestación con excepciones y la fijación del término "
            "del proceso conforme a la Ley 1563 de 2012.\n\n"
            "En el plano sustancial, la controversia gira en torno a la impugnación de las decisiones de la "
            "asamblea de accionistas del 14 de octubre de 2022 (Acta No. 11), mediante las cuales se modificó "
            "la composición de la junta directiva y se redujo el número de miembros de cinco (5) a cuatro (4), "
            "con impacto directo en la posibilidad de que Orion designara la mayoría de los integrantes del órgano. "
            "La convocante alega abuso del derecho al voto por parte de Bradley H. Hinkelman, Propiedad Raíz "
            "Casacol S.A.S. y Camila Caycedo, así como una estrategia para notificar en el último momento el "
            "pago del crédito de Rohan y otorgar un usufructo de acciones que permitiera configurar una mayoría "
            "artificial en la asamblea. El tribunal examina el alcance del acuerdo de accionistas, la incidencia "
            "del contrato de línea de crédito en el cómputo de votos, los requisitos del abuso del derecho al voto, "
            "y las pretensiones de nulidad/ineficacia de las decisiones sociales y de revocatoria del registro del "
            "Acta No. 11 ante la Cámara de Comercio, a la luz de la buena fe, la protección del equilibrio societario "
            "y la doctrina sobre contratos coligados."
        ),
        "path": "2022 A 0063 28-11-2024.pdf",
        "tags": [
            "clausula_compromisoria",
            "pacto_arbitral_estatutario",
            "competencia_tribunal",
            "coligacion_negocial",
            "contratos_coligados",
            "impugnacion_de_decisiones_sociales",
            "abuso_del_derecho_al_voto",
            "acuerdo_de_accionistas",
            "usufructo_de_acciones"
            ]
        },
    
    {
        "radicado": "2023 A 0055",
        "fecha_laudo": "2024-11-27",
        "title": "Alejandro García Ramos vs. Ricardo José Mejía Jaramillo, Christian Felipe Cano Bermúdez, Victoria Andrea Velásquez Negrete y Leidy Johana Gaviria Ocampo",
        "content": (
            "En el plano procesal, el laudo parte de la cláusula compromisoria incluida en la cláusula "
            "trigésima primera del contrato de arrendamiento del Apartamento 102, celebrado el 2 de marzo "
            "de 2022 entre el convocante como arrendador y los convocados como arrendatarios y deudor "
            "solidario. A partir de dicho pacto arbitral, el tribunal se constituye ante el Centro de Arbitraje de "
            "la Cámara de Comercio de Medellín, se instala, admite la demanda y su reforma, y declara su "
            "competencia en la primera audiencia de trámite conforme a la Ley 1563 de 2012. El laudo reseña "
            "la falta de contestación de la demanda y de la reforma por parte de los convocados, la inasistencia "
            "a la audiencia de conciliación (que fracasa por ausencia de la parte convocada), la práctica de "
            "pruebas documentales y de interrogatorio de parte al convocante, así como la incomparecencia de "
            "los convocados a rendir interrogatorio. También se analiza la solicitud de medida cautelar sobre un "
            "vehículo de propiedad de una de las convocadas, que no se decreta por falta de prueba y caución, "
            "y se deja constancia del control de legalidad sobre todo lo actuado, concluyendo que se cumplen "
            "los presupuestos procesales (competencia, demanda en forma, capacidad, legitimación, interés, "
            "ausencia de nulidades) para dictar un laudo de mérito.\n\n"
            "En el plano sustancial, el tribunal examina el contrato de arrendamiento de vivienda urbana, "
            "renovado automáticamente hasta marzo de 2024, y centra la controversia en el incumplimiento de "
            "los arrendatarios por el no pago de parte del canon de junio de 2023 y de los cánones de julio y "
            "agosto de 2023, así como de algunos servicios públicos. Con base en la prueba documental y en "
            "las conversaciones de WhatsApp, el laudo concluye que existe mora en el pago de dichos cánones "
            "y del servicio de acueducto veredal, pero considera acreditado que la terminación del contrato el "
            "25 de agosto de 2023 se produjo por mutuo acuerdo y no como un incumplimiento unilateral, por lo "
            "que niega las pretensiones de lucro cesante por cánones futuros. El tribunal liquida los cánones "
            "adeudados y sus intereses de mora conforme a la tasa máxima para créditos de consumo pactada "
            "en el contrato, hace efectiva la cláusula penal por tres cánones de arrendamiento al estar probado "
            "el incumplimiento, y descuenta de las sumas reconocidas el pago de tres millones de pesos "
            "realizado por el deudor solidario, aplicando las reglas de imputación de pagos del Código Civil. "
            "En consecuencia, se declara parcialmente la prosperidad de las pretensiones relacionadas con el "
            "incumplimiento y la cláusula penal, y se niegan las reclamaciones por lucro cesante y algunos "
            "servicios por falta de prueba del daño y de su cuantía."
        ),
        "path": "2023 A 0055 27-11-2024.pdf",
        "tags": [
            "clausula_compromisoria",
            "competencia_tribunal",
            "presupuestos_procesales",
            "incomparecencia_demandado",
            "medidas_cautelares",
            "contrato_de_arrendamiento",
            "incumplimiento_contractual",
            "intereses_de_mora",
            "clausula_penal",
            "lucro_cesante"
        ]
    },

    {
        "radicado": "2023 A 0041",
        "fecha_laudo": "2024-11-05",
        "title": "Juan Carlos Duque Núñez y Unión Temporal Vegachí Iluminado vs. Municipio de Vegachí",
        "content": (
            "En el plano procesal, el laudo parte de la cláusula compromisoria contenida en el Contrato "
            "de Concesión 052 del 11 de febrero de 2015 celebrado entre el Municipio de Vegachí y la "
            "Unión Temporal Vegachí Iluminado y de la convocatoria elevada por Juan Carlos Duque "
            "Núñez y la Unión Temporal ante el Centro de Arbitraje de la Cámara de Comercio de "
            "Medellín. El Tribunal describe la designación e integración de los árbitros y del secretario, "
            "la admisión de la demanda y su contestación, la audiencia de conciliación y fijación de "
            "honorarios (que fracasa), la primera audiencia de trámite en la que se declara competente "
            "y decreta pruebas, la práctica de testimonios, interrogatorios, dictamen pericial e informes, "
            "así como los alegatos de conclusión de las partes y el concepto del Ministerio Público. "
            "De manera detallada, verifica los presupuestos procesales de capacidad, demanda en "
            "forma, competencia arbitral, legitimación en la causa y ausencia de nulidades, discute la "
            "capacidad procesal de la Unión Temporal a la luz de la jurisprudencia del Consejo de "
            "Estado sobre consorcios y uniones temporales y concluye que la misma conserva "
            "capacidad para comparecer y reclamar la liquidación o restituciones del contrato de "
            "concesión, desatendiendo la solicitud de inhibición formulada por la Agente del Ministerio "
            "Público por supuesta desaparición de la Unión Temporal. Igualmente constata que la "
            "demanda se presentó dentro del término de caducidad aplicable a controversias "
            "contractuales administrativas.\n\n"
            "En el plano sustancial, el Tribunal analiza la controversia en torno al Contrato de "
            "Concesión 052 de 2015 para la prestación del servicio de alumbrado público en Vegachí. "
            "Las pretensiones principales y subsidiarias buscan la liquidación judicial del contrato, el "
            "reconocimiento de la reversión de los activos, el pago de saldos insolutos por la "
            "prestación del servicio, el reconocimiento de una inversión no amortizada superior a mil "
            "setecientos millones de pesos, así como intereses de mora o, en subsidio, la indexación, "
            "y, en escenarios alternativos, las restituciones mutuas derivadas de la nulidad del "
            "contrato. El Municipio propone excepciones relativas a la nulidad absoluta del contrato "
            "de concesión, la falta de jurisdicción del Tribunal frente a ciertas pretensiones, el "
            "incumplimiento del concesionario y la improcedencia de la liquidación y de las "
            "restituciones mutuas por falta de prueba del beneficio para la entidad. El laudo estudia la "
            "figura de la terminación unilateral del contrato estatal por ilegalidad, la diferencia con la "
            "nulidad absoluta, la competencia del Tribunal para declarar oficiosamente esta nulidad y, "
            "finalmente, concluye que el contrato de concesión está viciado de nulidad absoluta, entre "
            "otros motivos, por la nulidad de un acto administrativo base y por objeto ilícito. A partir "
            "de allí examina los efectos de la nulidad en el caso concreto, la procedencia y alcance de "
            "las restituciones mutuas y el eventual reconocimiento de las inversiones realizadas frente "
            "al beneficio demostrado para el Municipio de Vegachí."
        ),
        "path": "2023 A 0041 05-11-2024.pdf",
        "tags": [
            "clausula_compromisoria",
            "competencia_tribunal",
            "capacidad_procesal_union_temporal",
            "legitimacion_en_la_causa",
            "contrato_de_concesion",
            "terminacion_unilateral_por_ilegalidad",
            "nulidad_absoluta",
            "efectos_de_la_nulidad",
            "restitucion_de_prestaciones",
            "liquidacion_judicial_contrato",
            "servicio_de_alumbrado_publico"
        ]
    },

    {
        "radicado": "2024 A 0008",
        "fecha_laudo": "2024-10-04",
        "title": "Álvaro de Jesús Vargas Posada vs. Agrominera Porce S.A.S., Raúl de Jesús Ruiz Cuartas, Alonso Piedrahíta Aristizábal, Luis Orlando Corrales Valencia y Jairo Antonio Zea Atehortúa",
        "content": (
            "En el plano procesal, el laudo reseña la existencia del pacto arbitral estatutario contenido en el "
            "artículo 49 de los estatutos de Agrominera Porce S.A.S., que somete a arbitraje las controversias "
            "entre accionistas y entre éstos y la sociedad. Con base en dicha cláusula se convoca el tribunal "
            "ante el Centro de Arbitraje de la Cámara de Comercio de Medellín, se realiza el sorteo y "
            "designación de la árbitro única y del secretario, se inadmite y luego se admite la demanda tras su "
            "subsanación, y los convocados contestan formulando excepciones de mérito. El Tribunal fija "
            "honorarios y gastos, celebra la primera audiencia de trámite en la que declara su competencia, "
            "decreta y practica una amplia actividad probatoria (documental, testimonios, interrogatorios, "
            "exhibición de documentos y pruebas decretadas de oficio) y realiza el control de legalidad del "
            "artículo 132 del CGP, concluyendo que se encuentran cumplidos los presupuestos procesales de "
            "capacidad, demanda en forma, competencia, legitimación y ausencia de nulidades, así como la "
            "oportunidad de la acción, al tratarse de una acción de nulidad por abuso del derecho de voto "
            "regida por el término de prescripción de cinco años del artículo 235 de la Ley 222 de 1995, y no "
            "por la caducidad de la acción de impugnación del artículo 191 del Código de Comercio.\n\n"
            "En el plano sustancial, el Tribunal analiza la controversia societaria surgida en torno a la "
            "exclusión del accionista Álvaro de Jesús Vargas Posada de Agrominera Porce S.A.S., decidida "
            "en la asamblea extraordinaria del 29 de octubre de 2022 (Acta 37). Se estudia el contexto del "
            "título minero 6912, la estructura accionaria de la sociedad, las disputas entre el convocante y los "
            "demás socios, las reuniones previas, las actuaciones ante la Superintendencia de Sociedades y "
            "las acciones de tutela relacionadas con el derecho de petición y de acceso a la información "
            "societaria. El Tribunal concluye que, más allá del alegado abuso de mayoría, en la asamblea "
            "que decidió la exclusión se vulneraron garantías esenciales de convocatoria y participación, al "
            "celebrarse la reunión sin convocar al accionista afectado y sin computar su participación para el "
            "quórum, lo que configura un presupuesto de ineficacia de las decisiones sociales. En esa línea, "
            "reconoce de oficio la ineficacia de las determinaciones adoptadas en el Acta 37, incluyendo la "
            "exclusión del accionista, y descarta la caducidad o extemporaneidad de la demanda; al mismo "
            "tiempo, articula la figura del abuso del derecho de voto prevista en el artículo 43 de la Ley 1258 "
            "de 2008 con la protección del debido proceso societario, el derecho de información del socio y la "
            "necesidad de inscribir adecuadamente las decisiones que afectan la condición de accionista."
        ),
        "path": "2024 A 0008 04-10-2024.pdf",
        "tags": [
            "clausula_compromisoria",
            "pacto_arbitral_estatutario",
            "competencia_tribunal",
            "presupuestos_procesales",
            "accion_de_abuso_del_derecho_de_voto",
            "impugnacion_de_decisiones_sociales",
            "ineficacia_de_decisiones_sociales",
            "exclusion_de_accionista",
            "derecho_de_peticion",
            "tutela_derecho_de_informacion",
            "prescripcion_accion_societaria"
        ]
    }, 

    {
        "radicado": "2023 A 0018",
        "fecha_laudo": "2024-06-06",
        "title": "BRYAN DAVID CASTRO SOSA vs. KING RECORDS S.A.S.",
        "content": (
            "En el plano procesal, el laudo reseña la existencia de la cláusula compromisoria "
            "contenida en el contrato de management y representación artística celebrado entre "
            "BRYAN DAVID CASTRO SOSA (Ryan Castro) y KING RECORDS S.A.S., así como su posterior "
            "modificación por acuerdo de los apoderados para someter el conflicto al Centro de "
            "Conciliación, Arbitraje y Amigable Composición de la Cámara de Comercio de Medellín. "
            "Se describe la presentación y subsanación de la demanda, la designación de un tribunal "
            "de tres árbitros, la audiencia de instalación, la inadmisión y posterior admisión de la "
            "demanda, el recurso de reposición de la convocada contra el auto admisorio, y la acción "
            "de tutela promovida ante la jurisdicción ordinaria contra decisiones del Tribunal, que fue "
            "rechazada por el Tribunal Superior y la Corte Suprema. También se detallan la primera "
            "audiencia de trámite donde el tribunal declara su competencia, el decreto y práctica de "
            "una extensa actividad probatoria (documentos, interrogatorios de parte, múltiples "
            "testimonios, exhibición de documentos y oficios), las discusiones sobre la procedencia "
            "de oficios conforme al artículo 173 del CGP, el cierre del período probatorio, la audiencia "
            "de alegatos de conclusión y el análisis de las tachas de testigos a la luz del artículo 211 del "
            "CGP, concluyendo que se cumplen los presupuestos procesales de competencia, demanda "
            "en forma, capacidad, legitimación y ausencia de nulidades para emitir un laudo de mérito.\n\n"
            "En el plano sustancial, el tribunal enmarca la controversia en el contrato de management "
            "y representación artística celebrado en 2020, calificado como un contrato de mandato "
            "típico, bilateral, oneroso y de tracto sucesivo, por medio del cual KING RECORDS asumió "
            "obligaciones de medios y no de resultado para gestionar la carrera artística de Ryan "
            "Castro en la industria del entretenimiento. El laudo desglosa las obligaciones específicas "
            "de la convocada (promoción profesional, gestión de shows, negocios, imagen, auditoría, "
            "ética empresarial, etc.) y las obligaciones de exclusividad del artista, así como el estándar "
            "de diligencia profesional pactado. A partir de las pretensiones del convocante —que "
            "buscaba la declaración de incumplimiento de KING RECORDS, la resolución del contrato, "
            "la condena a una cláusula penal de USD 2.000.000, la notificación a agregadoras digitales "
            "y el reconocimiento de titularidad plena de derechos de propiedad intelectual y regalías— "
            "y de las excepciones de mérito de la convocada (falta de causa, temeridad, precisión de "
            "hechos y alegación de incumplimiento del propio artista), el tribunal analiza si KING "
            "RECORDS incumplió sus obligaciones de gestión, auditoría, ética y acompañamiento, y "
            "si procede la cláusula penal, la resolución del contrato y las reclamaciones relacionadas "
            "con masters, marcas, imagen y regalías digitales. El laudo estudia el alcance real del "
            "contrato de management frente a la explotación de fonogramas y derechos de autor, el "
            "carácter de obligaciones de medio, la reciprocidad de incumplimientos, la procedencia "
            "del juramento estimatorio y la liquidación de eventuales perjuicios, adoptando una "
            "posición sobre la prosperidad total o parcial de las pretensiones y la configuración de la "
            "cláusula penal y demás consecuencias económicas del conflicto."
        ),
        "path": "2023 A 0018 06-06-2024.pdf",
        "tags": [
            "clausula_compromisoria",
            "competencia_tribunal",
            "presupuestos_procesales",
            "tacha_de_testigo",
            "medidas_cautelares",
            "contrato_de_management",
            "representacion_artistica",
            "incumplimiento_contractual",
            "clausula_penal",
            "propiedad_intelectual",
            "derechos_de_autor",
            "intereses_de_mora"
        ]
    }, 

    {
        "radicado": "2023 A 0012",
        "fecha_laudo": "2024-05-15",
        "title": "GRUPO G8 PROYECTOS S.A.S. vs. JUAN CAMILO LONDOÑO PIEDRAHITA",
        "content": (
            "En el plano procesal, el laudo relata la conformación del tribunal arbitral en derecho ante el "
            "Centro de Arbitraje y Conciliación de la Cámara de Comercio de Medellín, con árbitro único, "
            "a partir de la cláusula compromisoria décima primera del contrato civil de obra MS126 para la "
            "construcción de una vivienda en la parcelación Monte Sereno en El Retiro (Antioquia). Se "
            "describen la presentación y subsanación de la demanda principal, la contestación con "
            "excepciones de mérito, la admisión de la demanda de reconvención y su contestación, así "
            "como los traslados de excepciones y de las objeciones al juramento estimatorio. El Tribunal "
            "deja constancia de la correcta designación y aceptación del árbitro único y de la secretaria, "
            "de la celebración de la audiencia de instalación y de la primera audiencia de trámite en la "
            "cual se declara competente para conocer tanto la demanda como la reconvención. Se detalla "
            "una amplia actividad probatoria: documentales, interrogatorios de parte, múltiples testimonios, "
            "dictamen pericial técnico sobre la casa 126, oficios y documentos remitidos por la aseguradora, "
            "así como la práctica y posterior prescindencia de una inspección judicial al inmueble. El laudo "
            "recoge igualmente la solicitud y decreto de una medida cautelar de inscripción de demanda "
            "sobre el inmueble, los controles de legalidad periódicos previstos en el artículo 132 del CGP, "
            "las audiencias de alegatos de conclusión y la verificación final de los presupuestos procesales "
            "de competencia, demanda en forma, capacidad, legitimación, inexistencia de nulidades y "
            "oportunidad de la acción, concluyendo que se encuentran dados para emitir una decisión de mérito.\n\n"
            "En el plano sustancial, la controversia se centra en el contrato civil de obra MS126 celebrado el "
            "9 de junio de 2020, mediante el cual G8 se obligó, bajo la modalidad de precio global fijo, a "
            "construir una vivienda de 249 m² a cambio de un precio repartido en varios hitos de pago, "
            "incluyendo un saldo final de COP $92.300.000 sujeto a la \"recepción a entera satisfacción\" del "
            "contratante. G8 demanda la nulidad de esa condición por considerarla meramente potestativa, "
            "pide que se entienda reemplazada por la simple recepción material del inmueble y reclama el "
            "pago del saldo del precio, de obras adicionales por COP $1.855.788, intereses moratorios sobre "
            "las sumas adeudadas y la cláusula penal del 20% del valor del contrato. El convocado opone "
            "excepciones como contrato no cumplido, incumplimiento de G8 y temeridad, sosteniendo que la "
            "obra fue entregada con defectos graves (humedades, problemas estructurales, acabados "
            "deficientes) que comprometían la habitabilidad, y formula demanda de reconvención para que "
            "se declare el incumplimiento de la contratista, se le condene al reembolso de cuantiosos gastos "
            "de reparación y adecuación del inmueble (base granular, pisos, pintura, cambio total del cielo "
            "raso y de la estructura de aluminio y ventanería), así como al pago de la cláusula penal pactada. "
            "El Tribunal califica y encuadra el negocio como contrato de obra civil típico regulado por los "
            "artículos 2053 y ss. del Código Civil, analiza la validez del pacto de \"recepción a entera "
            "satisfacción\" frente a la figura de la condición meramente potestativa, el estándar de calidad y "
            "habitabilidad exigible al contratista, la distribución de riesgos, la carga de la prueba sobre los "
            "vicios constructivos, la procedencia de la cláusula penal y de los intereses moratorios, así como "
            "el alcance de las pretensiones indemnizatorias de ambas partes a la luz de las pruebas y del "
            "juramento estimatorio."
        ),
        "path": "2023 A 0012 15-05-2024.pdf",
        "tags": [
            "clausula_compromisoria",
            "competencia_tribunal",
            "presupuestos_procesales",
            "demanda_de_reconvencion",
            "medidas_cautelares",
            "juramento_estimatorio",
            "contrato_de_obra",
            "contrato_civil_de_obra",
            "condicion_meramente_potestativa",
            "incumplimiento_contractual",
            "vicios_constructivos",
            "habitabilidad_inmueble",
            "clausula_penal",
            "intereses_de_mora"
        ]
    }, 

    {
        "radicado": "2023 A 0012",
        "fecha_laudo": "2024-05-15",
        "title": "GRUPO G8 PROYECTOS S.A.S. vs. JUAN CAMILO LONDOÑO PIEDRAHITA",
        "content": (
            "En el plano procesal, el laudo relata la conformación del tribunal arbitral en derecho ante el "
            "Centro de Arbitraje y Conciliación de la Cámara de Comercio de Medellín, con árbitro único, "
            "a partir de la cláusula compromisoria décima primera del contrato civil de obra MS126 para la "
            "construcción de una vivienda en la parcelación Monte Sereno en El Retiro (Antioquia). Se "
            "describen la presentación y subsanación de la demanda principal, la contestación con "
            "excepciones de mérito, la admisión de la demanda de reconvención y su contestación, así "
            "como los traslados de excepciones y de las objeciones al juramento estimatorio. El Tribunal "
            "deja constancia de la correcta designación y aceptación del árbitro único y de la secretaria, "
            "de la celebración de la audiencia de instalación y de la primera audiencia de trámite en la "
            "cual se declara competente para conocer tanto la demanda como la reconvención. Se detalla "
            "una amplia actividad probatoria: documentales, interrogatorios de parte, múltiples testimonios, "
            "dictamen pericial técnico sobre la casa 126, oficios y documentos remitidos por la aseguradora, "
            "así como la práctica y posterior prescindencia de una inspección judicial al inmueble. El laudo "
            "recoge igualmente la solicitud y decreto de una medida cautelar de inscripción de demanda "
            "sobre el inmueble, los controles de legalidad periódicos previstos en el artículo 132 del CGP, "
            "las audiencias de alegatos de conclusión y la verificación final de los presupuestos procesales "
            "de competencia, demanda en forma, capacidad, legitimación, inexistencia de nulidades y "
            "oportunidad de la acción, concluyendo que se encuentran dados para emitir una decisión de mérito.\n\n"
            "En el plano sustancial, la controversia se centra en el contrato civil de obra MS126 celebrado el "
            "9 de junio de 2020, mediante el cual G8 se obligó, bajo la modalidad de precio global fijo, a "
            "construir una vivienda de 249 m² a cambio de un precio repartido en varios hitos de pago, "
            "incluyendo un saldo final de COP $92.300.000 sujeto a la \"recepción a entera satisfacción\" del "
            "contratante. G8 demanda la nulidad de esa condición por considerarla meramente potestativa, "
            "pide que se entienda reemplazada por la simple recepción material del inmueble y reclama el "
            "pago del saldo del precio, de obras adicionales por COP $1.855.788, intereses moratorios sobre "
            "las sumas adeudadas y la cláusula penal del 20% del valor del contrato. El convocado opone "
            "excepciones como contrato no cumplido, incumplimiento de G8 y temeridad, sosteniendo que la "
            "obra fue entregada con defectos graves (humedades, problemas estructurales, acabados "
            "deficientes) que comprometían la habitabilidad, y formula demanda de reconvención para que "
            "se declare el incumplimiento de la contratista, se le condene al reembolso de cuantiosos gastos "
            "de reparación y adecuación del inmueble (base granular, pisos, pintura, cambio total del cielo "
            "raso y de la estructura de aluminio y ventanería), así como al pago de la cláusula penal pactada. "
            "El Tribunal califica y encuadra el negocio como contrato de obra civil típico regulado por los "
            "artículos 2053 y ss. del Código Civil, analiza la validez del pacto de \"recepción a entera "
            "satisfacción\" frente a la figura de la condición meramente potestativa, el estándar de calidad y "
            "habitabilidad exigible al contratista, la distribución de riesgos, la carga de la prueba sobre los "
            "vicios constructivos, la procedencia de la cláusula penal y de los intereses moratorios, así como "
            "el alcance de las pretensiones indemnizatorias de ambas partes a la luz de las pruebas y del "
            "juramento estimatorio."
        ),
        "path": "2023 A 0012 15-05-2024.pdf",
        "tags": [
            "clausula_compromisoria",
            "competencia_tribunal",
            "presupuestos_procesales",
            "demanda_de_reconvencion",
            "medidas_cautelares",
            "juramento_estimatorio",
            "contrato_de_obra",
            "contrato_civil_de_obra",
            "condicion_meramente_potestativa",
            "incumplimiento_contractual",
            "vicios_constructivos",
            "habitabilidad_inmueble",
            "clausula_penal",
            "intereses_de_mora"
        ]
    }, 

    {
            "radicado": "2022 A 0062",
            "fecha_laudo": "2024-03-14",
            "title": "Conjunto Residencial Entre Palmas de San Diego P.H. vs. Mantenimiento, Reformas y Construcción de Colombia S.A.S. (Marrecol S.A.S.)",
            "arbiter": "Daniel Jiménez Pastor",
            "keywords": "contrato_obra, impermeabilizacion, garantia_convencional",
            "content": (
                "En el plano procesal, el laudo verifica de manera detallada los presupuestos procesales "
                "de capacidad, demanda en forma, competencia del tribunal y ausencia de nulidades, a partir "
                "de la cláusula compromisoria del contrato de obra para trabajos de impermeabilización en la "
                "Torre 3 del Conjunto Residencial Entre Palmas de San Diego. Se reseña la presentación de la "
                "demanda, su inadmisión y subsanación, la contestación con excepciones de mérito y objeción "
                "al juramento estimatorio, el incidente de nulidad por indebida notificación, la audiencia de "
                "conciliación fallida, la fijación de gastos y honorarios, el decreto y práctica de pruebas "
                "documentales, testimoniales y exhibición de documentos, así como el cierre de la etapa probatoria "
                "y la audiencia de alegatos. El tribunal concluye que el trámite se surtió conforme a la Ley 1563 "
                "de 2012 y al Reglamento del Centro de Arbitraje de la Cámara de Comercio de Medellín, sin que se "
                "configure causal de nulidad.\n\n"
                "En el plano sustancial, el tribunal analiza el contrato de obra civil por precios unitarios para "
                "trabajos de impermeabilización y la cláusula de garantía convencional de cinco años en impermeabilización "
                "y dos años en morteros y enchapes. A la luz de los artículos 2053, 2056, 2060 y 2061 del Código Civil y de "
                "la jurisprudencia sobre responsabilidad del constructor, estudia si Marrecol incumplió las obligaciones "
                "propias de un contrato de obra y si existe responsabilidad civil contractual por los daños en los "
                "apartamentos 2611 y 2612. El tribunal considera probadas las excepciones de inexistencia de responsabilidad "
                "contractual y falta de prueba de incumplimiento respecto de las primeras pretensiones, por lo que niega las "
                "reclamaciones indemnizatorias ligadas a vicios de construcción y filtraciones. Sin embargo, declara que la "
                "convocada incumplió la obligación de atender la garantía convencional y, como consecuencia, ordena reintegrar "
                "a la copropiedad la suma de $1.121.005,59 más intereses moratorios a la tasa máxima autorizada, absteniéndose "
                "de imponer sanciones procesales del artículo 206 del CGP y de condenar en costas."
            ),
            "path": "2022 A 0062 14-03-2024.pdf",
            "tags": [
                # procesales
                "clausula_compromisoria",
                "presupuestos_procesales",
                "competencia_tribunal",
                "excepciones_de_merito",
                "juramento_estimatorio",
                "saneamiento_procesal",
                # sustanciales
                "contrato_de_obra",
                "impermeabilizacion",
                "garantia_convencional",
                "responsabilidad_civil_contractual",
                "perjuicios_por_filtraciones",
                "obligacion_de_resultado",
                "reintegro_de_pagos"
            ],
        }
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
            arbiter=item.get("arbiter"),
            keywords=item.get("keywords"),
            tags=tag_objects,
        )
        db.session.add(case)

    db.session.commit()


# --- Ruta de búsqueda (tags + keyword + árbitro + fechas) ---

@app.route("/", methods=["GET"])
def search():
    q = (request.args.get("q") or "").strip()
    selected_tags_raw = request.args.getlist("tag")  # checkboxes: name="tag"
    sort = request.args.get("sort", "fecha_desc")
    page = request.args.get("page", 1, type=int)
    per_page = 5

    # Nuevos filtros
    keyword_filter = (request.args.get("keyword") or "").strip()
    arbiter_filter = (request.args.get("arbiter") or "").strip()
    date_from_str = (request.args.get("date_from") or "").strip()
    date_to_str = (request.args.get("date_to") or "").strip()

    # Parsear IDs de tags seleccionados
    selected_tag_ids = []
    for t in selected_tags_raw:
        try:
            selected_tag_ids.append(int(t))
        except ValueError:
            pass

    all_tags = Tag.query.order_by(Tag.name.asc()).all()

    query = Case.query

    # Búsqueda por palabra clave general: radicado, título, contenido, etiqueta, árbitro, keywords
    if q:
        pattern = f"%{q}%"
        query = (
            query.outerjoin(Case.tags)
            .filter(
                or_(
                    Case.title.ilike(pattern),
                    Case.content.ilike(pattern),
                    Case.radicado.ilike(pattern),
                    Case.arbiter.ilike(pattern),
                    Case.keywords.ilike(pattern),
                    Tag.name.ilike(pattern),
                )
            )
            .distinct()
        )

    # Filtro por tags (facetas)
    if selected_tag_ids:
        query = query.filter(Case.tags.any(Tag.id.in_(selected_tag_ids)))

    # Filtro por palabra clave temática (una palabra, pero si meten más igual funciona)
    if keyword_filter:
        kw_pattern = f"%{keyword_filter}%"
        query = query.filter(Case.keywords.ilike(kw_pattern))

    # Filtro por árbitro / tribunal
    if arbiter_filter:
        arb_pattern = f"%{arbiter_filter}%"
        query = query.filter(Case.arbiter.ilike(arb_pattern))

    # Filtro por rango de fechas
    date_from = None
    date_to = None
    if date_from_str:
        try:
            date_from = datetime.strptime(date_from_str, "%Y-%m-%d").date()
        except ValueError:
            date_from = None
    if date_to_str:
        try:
            date_to = datetime.strptime(date_to_str, "%Y-%m-%d").date()
        except ValueError:
            date_to = None

    if date_from:
        query = query.filter(Case.fecha_laudo >= date_from)
    if date_to:
        query = query.filter(Case.fecha_laudo <= date_to)

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
        keyword_filter=keyword_filter,
        arbiter_filter=arbiter_filter,
        date_from=date_from_str,
        date_to=date_to_str,
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
      "arbiter": "Árbitro único: Nombre",
      "keywords": "consumo nulidad contrato",
      "tags": ["pacto_arbitral", "contrato_de_obra"]
    }
    """
    data = request.get_json(silent=True) or {}

    radicado = (data.get("radicado") or "").strip()
    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()
    doc_filename = (data.get("doc_filename") or data.get("path") or "").strip()
    arbiter = (data.get("arbiter") or "").strip()
    keywords = (data.get("keywords") or "").strip()
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
        arbiter=arbiter,
        keywords=keywords,
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
                "arbiter": new_case.arbiter,
                "keywords": new_case.keywords,
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
