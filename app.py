from flask import Flask, request, jsonify, send_file, make_response, render_template_string
from flask_cors import CORS
from weasyprint import HTML
import xml.etree.ElementTree as ET
from datetime import datetime
import qrcode, base64
from io import BytesIO
import os

app = Flask(__name__)

# Límite de subida (ajustá si necesitás)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB

# CORS: en producción, seteá ALLOWED_ORIGINS="https://tudominio.com,https://www.tudominio.com"
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*")
origins = [o.strip() for o in ALLOWED_ORIGINS.split(",")] if ALLOWED_ORIGINS != "*" else "*"
CORS(app, resources={r"/api/*": {"origins": origins}})

# ==========
#  PLANTILLA (tu HTML original)
# ==========
HTML_TEMPLATE = r'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <style>
 @page {
        size: A4;
        margin: 13mm 10mm 5mm 5mm;
    }

        body { font-family: Arial, sans-serif; font-size: 8pt; margin: 0; padding: 0; }
        .container { width: 100%; padding: 2mm 5mm; }
        .header { display: flex; justify-content: space-between; margin-bottom: 10px; }
        .left-header { width: 60%; }
        .right-header { width: 35%; text-align: right; }
        .company-name { font-size: 14pt; font-weight: bold; margin-bottom: 5px; }
        .document-title { font-size: 8pt; font-weight: bold; text-align: center; margin: 15px 0; }
        .section { margin-bottom: 10px; }
        .two-columns { display: flex; justify-content: space-between; }
        .column { width: 48%; }
        .bordered { border: 1px solid black; padding: 5px; }
        .table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        .table th, .table td { border: 1px solid black; padding: 5px; text-align: left; }
        .table th { background-color: #f2f2f2; }
        .text-right { text-align: right !important; }
        .text-center { text-align: center; }
        .total-row { font-weight: bold; }
        .footer { margin-top: 20px; font-size: 8pt; text-align: center; }
        .qr-code { text-align: center; margin-top: 1px; }
        .signature { margin-top: 50px; display: flex; justify-content: space-around; }
    </style>
</head>
<body>
    <div class="container">
        <div class="document-title">KUDE DE DOCUMENTO TRIBUTARIO ELECTRÓNICO</div>
        
       <div class="two-columns bordered">
            <div class="column">
                <div class="company-name">{{ empresa.razon_social }}</div>
                <div>Dirección: {{ empresa.direccion }}</div>
                <div>Ciudad: {{ empresa.ciudad }} - {{ empresa.departamento }}</div>
                <div>Teléfono: {{ empresa.telefono }}</div>
                <div>Correo Electrónico: {{ empresa.email }}</div>
                <div>Actividad Económica: {{ empresa.actividad_economica }}</div>
                {% for act in empresa.actividades_adicionales %}
                <div>{{ act }}</div>
                {% endfor %}
            </div>
            
            <div class="column">
                <div>RUC: {{ empresa.ruc }}-{{ empresa.dv }}</div>
                <div>Timbrado Nro: {{ timbrado.numero }}</div>
                <div>Fecha de Inicio de Vigencia: {{ timbrado.fecha_inicio }}</div>
                <div style="text-align: center; margin-top: 10px;">
    <div style="font-size: 14pt; font-weight: bold;">{{ documento.tipo }}</div>
    <div style="font-size: 12pt; font-weight: bold;">{{ documento.numero }}</div>
</div>
            </div>
        </div>
        
        <div class="two-columns bordered" style="margin-top: 15px;">
            <div class="column">
                <div>RUC: {{ cliente.ruc }}-{{ cliente.dv }}</div>
                <div>Nombre o Razón Social: {{ cliente.razon_social }}</div>
                <div>Dirección: {{ cliente.direccion }}</div>
                <div>Ciudad: {{ cliente.ciudad }}</div>
                <div>Teléfono: {{ cliente.telefono }}</div>
            </div>
            
            <div class="column">
                <div>Fecha de Emisión: {{ documento.fecha_emision }}</div>
                <div>Condición de Venta: {{ documento.condicion_venta }}</div>
                <div>Moneda: {{ documento.moneda }}</div>
                <div>Tipo de transacción: {{ documento.tipo_transaccion }}</div>
            </div>
        </div>


        
<table class="table">
    <thead>
      <tr>
    <th style="text-align: center;">Código</th>
    <th style="text-align: center;" colspan="3">Descripción</th>
    <th style="text-align: center;">Unidad de Medida</th>
    <th style="text-align: center;">Cantidad</th>
    <th style="text-align: center;">Precio Unitario</th>
    <th style="text-align: center;">Exentas</th>
    <th style="text-align: center;">5%</th>
    <th style="text-align: center;">10%</th>
</tr>
    </thead>
    <tbody>
        {% for item in items %}
        <tr>
            <td>{{ item.codigo }}</td>
            <td colspan="3" style="width: 40%; min-width: 40%; word-break: break-word;">{{ item.descripcion }}</td>
            <td>{{ item.unidad_medida }}</td>
            <td class="text-right">{{ item.cantidad }}</td>
            <td class="text-right">{{ item.precio_unitario }}</td>
            <td class="text-right">{{ item.exentas }}</td>
            <td class="text-right">{{ item.iva5 }}</td>
            <td class="text-right">{{ item.iva10 }}</td>
        </tr>
        {% endfor %}

        <tr class="total-row">
            <td rowspan="6" colspan="3" style="text-align: center; vertical-align: top; width: 45mm; min-width: 45mm;">
    {% if documento.qr_code %}
    <img src="{{ documento.qr_code }}" alt="QR Code" style="width: 100%; height: auto; margin-top: 5px;">
    {% endif %}
</td>
            <td class="text-right" colspan="4">Subtotal:</td>
            <td class="text-right">{{ totales.exentas }}</td>
            <td class="text-right">{{ totales.iva5 }}</td>
            <td class="text-right">{{ totales.iva10 }}</td>
        </tr>
        <tr class="total-row">
            <td colspan="6" class="text-right">Redondeo:</td>
            <td class="text-right" colspan="1">{{ totales.redondeo }}</td>
        </tr>
        <tr class="total-row">
            <td colspan="6" class="text-right">Total de la Operación:</td>
            <td class="text-right" colspan="1">{{ totales.total_operacion }}</td>
        </tr>
        <tr class="total-row">
            <td colspan="6" class="text-right">Total en Guaraníes:</td>
            <td class="text-right" colspan="1">{{ totales.total_guaranies }}</td>
        </tr>
    <tr>
    <td style="font-weight: bold; padding: 2px 4px; line-height: 1;">Liquidación de IVA:</td>
    <td style="font-weight: bold; padding: 2px 4px; line-height: 1; border-right: none;">(5%):</td>
    <td class="text-right" style="padding: 2px 4px; line-height: 1; border-left: none;">{{ liquidacion_iva.iva5 }}</td>
    <td style="font-weight: bold; padding: 2px 4px; line-height: 1; border-right: none;">(10%):</td>
    <td class="text-right" style="padding: 2px 4px; line-height: 1; border-left: none;">{{ liquidacion_iva.iva10 }}</td>
    <td style="font-weight: bold; padding: 2px 4px; line-height: 1; border-right: none;">Total IVA:</td>
    <td class="text-right" style="padding: 2px 4px; line-height: 1; border-left: none;">{{ liquidacion_iva.total }}</td>
</tr>

<tr>
    <td colspan="7" style="font-size: 7pt; padding: 4px; line-height: 1.2;">
        <div>Consulte la validez de este DTE con el número de CDC impreso abajo en: <br>
        <strong>https://ekuatia.set.gov.py/consultas</strong></div>
        <div style="font-size: 13pt; font-weight: bold; margin-top: 2px;">CDC: {{ documento.cdc_formateado }}</div>
            </td>
</tr>
    </tbody>
</table>
      
              
        <div class="footer">
                   <div>ESTE DOCUMENTO ES UNA REPRESENTACIÓN GRÁFICA DE UN DOCUMENTO ELECTRÓNICO (XML)</div>
<div>Si su documento electrónico presenta algun error, podrá solicitar la modificación dentro de las 72 horas siguientes de la emisión de este
comprobante.</div>
        </div>
        
              
            </div>
</body>
</html>
'''

# ==========
#  FUNCIONES AUXILIARES
# ==========

def generate_qr_image(data: str | None):
    """Genera imagen QR embebida en base64 (data URI) o None si no hay dato."""
    if not data:
        return None
    qr = qrcode.QRCode(box_size=3, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    img_str = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_str}"

def parse_xml_stream(file_stream):
    """
    Versión en memoria de tu parse_xml original.
    Lee desde file-like (request.files['xml'].stream) y devuelve el dict con todas
    las claves que espera la plantilla: empresa, cliente, timbrado, documento, items, totales, liquidacion_iva.
    """
    ns = {'ns': 'http://ekuatia.set.gov.py/sifen/xsd'}
    tree = ET.parse(file_stream)
    root = tree.getroot()

    def get_text(tag, parent=root):
        element = parent.find(f'.//ns:{tag}', ns)
        return element.text if element is not None and element.text is not None else ''

    # Empresa emisora
    empresa = {
        'razon_social': get_text('dNomEmi'),
        'ruc': get_text('dRucEm'),
        'dv': get_text('dDVEmi'),
        'direccion': f"{get_text('dDirEmi')} {get_text('dNumCas')}".strip(),
        'ciudad': get_text('dDesCiuEmi'),
        'departamento': get_text('dDesDepEmi'),
        'telefono': get_text('dTelEmi'),
        'email': get_text('dEmailE'),
        'actividad_economica': get_text('dDesActEco'),
        'actividades_adicionales': [act.findtext('ns:dDesActEco', default='', namespaces=ns) 
                                    for act in root.findall('.//ns:gActEco', ns)[1:]]
    }

    # Cliente receptor
    cliente = {
        'razon_social': get_text('dNomRec'),
        'ruc': get_text('dRucRec'),
        'dv': get_text('dDVRec'),
        'direccion': f"{get_text('dDirRec')} {get_text('dNumCasRec')}".strip(),
        'ciudad': get_text('dDesCiuRec'),
        'telefono': get_text('dTelRec')
    }

    # Timbrado
    fe_ini_t = get_text('dFeIniT')
    try:
        fe_ini_fmt = datetime.strptime(fe_ini_t, '%Y-%m-%d').strftime('%d/%m/%Y') if fe_ini_t else ''
    except Exception:
        fe_ini_fmt = fe_ini_t  # si viene en otro formato, deja como está

    timbrado = {
        'numero': get_text('dNumTim'),
        'fecha_inicio': fe_ini_fmt
    }

    # Documento
    de = root.find('.//ns:DE', ns)
    cdc = de.attrib['Id'] if de is not None and 'Id' in de.attrib else ''
    # Formatea CDC en grupos de 4 sin asumir longitud fija
    cdc_formateado = '-'.join([cdc[i:i+4] for i in range(0, len(cdc), 4)]) if cdc else ''

    fe_emi = get_text('dFeEmiDE')
    try:
        fe_emi_fmt = datetime.strptime(fe_emi, '%Y-%m-%dT%H:%M:%S').strftime('%d/%m/%Y %H:%M:%S') if fe_emi else ''
    except Exception:
        fe_emi_fmt = fe_emi

    documento = {
        'tipo': get_text('dDesTiDE'),
        'numero': f"{get_text('dEst')}-{get_text('dPunExp')}-{get_text('dNumDoc')}",
        'fecha_emision': fe_emi_fmt,
        'condicion_venta': get_text('dDCondOpe'),
        'moneda': get_text('dDesMoneOpe'),
        'tipo_transaccion': get_text('dDesTipTra'),
        'cdc': cdc,
        'cdc_formateado': cdc_formateado,
        'qr_code': generate_qr_image(get_text('dCarQR'))
    }

    # Items
    def fmt0(n):
        try:
            return f"{float(n):,.0f}".replace(",", ".")
        except Exception:
            try:
                return f"{float(str(n).replace('.','').replace(',','.')):,.0f}".replace(",", ".")
            except Exception:
                return "0"

    items = []
    for item in root.findall('.//ns:gCamItem', ns):
        iva = item.find('ns:gCamIVA', ns)
        def t(tg, pr=None):
            if pr is None:
                return ''
            el = pr.find(f'ns:{tg}', ns)
            return el.text if el is not None and el.text is not None else ''
        tasa_iva = t('dTasaIVA', iva)
        base_grav = float(t('dBasGravIVA', iva) or 0)
        liq_iva = float(t('dLiqIVAItem', iva) or 0)
        base_exe = float(t('dBasExe', iva) or 0)
        total_gravado = base_grav + liq_iva

        exentas = cinco = diez = 0.0
        if tasa_iva == '10':
            diez = total_gravado
        elif tasa_iva == '5':
            cinco = total_gravado
        else:
            exentas = base_exe

        items.append({
            'codigo': get_text('dCodInt', item),
            'descripcion': get_text('dDesProSer', item),
            'unidad_medida': get_text('dDesUniMed', item),
            'cantidad': get_text('dCantProSer', item),
            'precio_unitario': fmt0(get_text('dPUniProSer', item) or 0),
            'valor_venta': fmt0(get_text('dTotBruOpeItem', item) or 0),
            'exentas': fmt0(exentas),
            'iva5': fmt0(cinco),
            'iva10': fmt0(diez)
        })

    # Totales
    def parse_int_str(numstr):
        # Convierte "1.234.567" a float 1234567.0 de forma segura
        try:
            return float(str(numstr).replace(".", "").replace(",", "."))
        except Exception:
            return 0.0

    total_exentas = sum(parse_int_str(i['exentas']) for i in items)
    total_cinco   = sum(parse_int_str(i['iva5']) for i in items)
    total_diez    = sum(parse_int_str(i['iva10']) for i in items)

    def g(tag, default='0'):
        v = get_text(tag)
        return v if v not in (None, '') else default

    totales = {
        'subtotal': fmt0(g('dTotOpe')),
        'exentas': fmt0(total_exentas),
        'iva5': fmt0(total_cinco),
        'iva10': fmt0(total_diez),
        'redondeo': fmt0(g('dRedon')),
        'total_operacion': fmt0(g('dTotOpe')),
        'total_guaranies': fmt0(g('dTotGralOpe'))
    }

    # Liquidación de IVA
    liquidacion_iva = {
        'iva5': fmt0(g('dIVA5')),
        'iva10': fmt0(g('dIVA10')),
        'total': fmt0(g('dTotIVA'))
    }

    return {
        'empresa': empresa,
        'cliente': cliente,
        'timbrado': timbrado,
        'documento': documento,
        'items': items,
        'totales': totales,
        'liquidacion_iva': liquidacion_iva
    }

# ==========
#  ENDPOINTS
# ==========

@app.post("/api/kude")
def kude():
    if 'xml' not in request.files:
        return jsonify({"error": "Falta archivo XML"}), 400
    f = request.files['xml']
    if not f.filename.lower().endswith('.xml'):
        return jsonify({"error": "Formato inválido, suba un .xml"}), 400

    try:
        datos = parse_xml_stream(f.stream)
        html_rendered = render_template_string(HTML_TEMPLATE, **datos)

        pdf_buf = BytesIO()
        HTML(string=html_rendered).write_pdf(pdf_buf)
        pdf_buf.seek(0)

        # Descarga directa
        return send_file(pdf_buf,
                         mimetype="application/pdf",
                         as_attachment=True,
                         download_name="kude.pdf")
    except Exception as e:
        # Log mínimo en respuesta (en prod podrías ocultar detalles)
        return jsonify({"error": str(e)}), 500

@app.get("/healthz")
def healthz():
    return {"ok": True}

if __name__ == "__main__":
    # Para correr localmente: python app.py
    app.run(host="0.0.0.0", port=5000)
