from flask import Flask, render_template, request, redirect, url_for, jsonify
import re
import mysql.connector
app = Flask(__name__)



# Configuración de la base de datos
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="cotizaciones"
)
cursor = db.cursor()

app.secret_key ="miclave" 


#para obtener los valores de una columna de tipo ENUM en una tabla
def get_enum_values(articulo, categoria):   #toma dos argumentos  articulo: el nombre de la tabla en la base de datos.categoria: el nombre de la columna de tipo ENUM dentro de la tabla.
    cursor.execute(f"SHOW COLUMNS FROM {articulo} LIKE '{categoria}'") #está diseñada para obtener la definición de una columna específica en una tabla, lo que es útil para trabajar con columnas ENUM y extraer sus valores posibles dinámicamente.
    result = cursor.fetchone() # guarda los resultados de la consulta 
    enum_values = re.findall(r"'(.*?)'", result[1])#Esta línea utiliza una expresión regular para buscar y extraer todos los valores posibles del ENUM. La expresión regular r"'(.*?)'" busca todas las cadenas de caracteres que están entre comillas simples dentro de result[1]. re.findall devuelve una lista con todas las coincidencias encontradas.
    return enum_values#Finalmente, la función devuelve la lista de valores extraídos del ENUM.


def get_product_code(categoria):
    # Define rangos de códigos de producto según la categoría
    category_ranges = {
        'Mano de obra calificada': range(7000, 7999),
        'Mano de obra no calificada': range(7000, 7999),
        'Materiales': range(2002, 3001),  #pendiente
        'Servicios domiciliarios': range(12000, 12999),
        'Terrenos': range(10000, 10999),
        'Edificios': range(10000, 10999),
        'Maquinaria y Equipo': range(10000, 10999),
        'Mantenimiento maquinaria y equipo': range(12000, 12999),
        'Transporte': range(12000, 12999),
        'Servicios de venta y de distribución': range(12000, 12999),
        'Servicios de alojamiento comidas y bebidas': range(212000, 12999),
        'Servicios financieros y conexos': range(12000, 12999),
        'Servicios de leasing': range(12000, 12999),
        'Servicios inmobiliarios': range(12000, 12999),
        'Servicios prestados a las empresas y servicios de producción': range(12000, 12999),
        'Servicios para la comunidad, sociales y personales': range(12000, 12999),
        'Gastos imprevistos': range(11000, 11999),
        'Adquisición de activos financieros': range(11000, 11999),
        'Disminución de pasivos': range(11000, 11999),
        'Impuestos, pagos de derechos, contribuciones, multas y sanciones': range(11000, 11999),
        'Transferencias corrientes y de capital': range(11000, 11999), 
        # Añadir más categorías y rangos según sea necesario
    }
    # Obtener el rango correspondiente a la categoría
    code_range = category_ranges.get(categoria, None)
    if code_range is None:
        raise ValueError("Categoría no válida")
    
    # Buscar el siguiente código disponible en el rango
    cursor.execute("SELECT codigo FROM articulo WHERE codigo BETWEEN %s AND %s", (code_range.start, code_range.stop))
    used_codes = {row[0] for row in cursor.fetchall()}
    for code in code_range:
        if code not in used_codes:
            return code
    raise ValueError("No hay códigos disponibles en el rango para esta categoría")

#proveedores, agregar y visualizar
@app.route('/proveedores', methods=["GET", "POST"])
def proveedores():
    if request.method == "POST":
        nit = request.form["nit"] 
        nombre = request.form["nombre"]
        telefono = request.form["telefono"]
        correo = request.form["correo"]
        ubicacion = request.form["ubicacion"]
        fecha = request.form["fecha"]
       
        cursor.execute("INSERT INTO proveedores (nit, nombre, telefono, correo, ubicacion, fecha) VALUES (%s, %s, %s, %s, %s, %s)", 
                       (nit, nombre, telefono, correo, ubicacion, fecha))
        db.commit()
        return redirect(url_for("proveedores"))

   
    cursor.execute("SELECT * FROM proveedores") # para visualizar los datos en tabla
    proveedores = cursor.fetchall()
    return render_template('proveedores.html', proveedores=proveedores)


#agregar un articulo nuevo y visualizarlos
@app.route('/articulo', methods=["GET", "POST"])
def articulo():
    if request.method == "POST": 
        nombre = request.form["nombre"]
        descripcion = request.form["descripcion"]
        categoria = request.form["categoria"]
        unidad_medida = request.form["unidad_medida"]
        precio = request.form["precio"]
        iva = request.form["iva"]
        fecha = request.form["fecha"]
        proveedores = request.form["proveedores"]
        try:
            codigo = get_product_code(categoria)
        except ValueError as e:
            return str(e), 400
        
        cursor.execute("INSERT INTO articulo (codigo, nombre, descripcion, categoria, unidad_medida, precio, iva, fecha, proveedores) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                       (codigo, nombre, descripcion, categoria, unidad_medida, precio, iva, fecha, proveedores))
        db.commit()
        return redirect(url_for("articulo"))

    categoria = get_enum_values("articulo", "categoria")#se llama la funcion arriba definida para los enum
    cursor.execute("SELECT * FROM articulo") # para visualizar los datos en tabla
    articulo = cursor.fetchall()
    cursor.execute("SELECT * FROM proveedores") # para visualizar los datos en tabla
    proveedores = cursor.fetchall()
    return render_template('articulo.html', categoria=categoria, articulo=articulo, proveedores=proveedores)

#agregar y visualizar los proyectos
@app.route('/proyecto', methods=["GET", "POST"])
def proyecto():
    if request.method == "POST": 
        proyecto_codigo = request.form["proyecto_codigo"]
        proyecto_nombre = request.form["proyecto_nombre"]
        proyecto_descripcion = request.form["proyecto_descripcion"]
       
        cursor.execute("INSERT INTO proyecto (proyecto_codigo, proyecto_nombre, proyecto_descripcion) VALUES (%s, %s, %s)", 
                       (proyecto_codigo, proyecto_nombre, proyecto_descripcion))
        db.commit()
        return redirect(url_for("proyecto"))

    cursor.execute("SELECT * FROM proyecto")
    proyecto = cursor.fetchall()
    return render_template('proyecto.html', proyecto=proyecto)
   

   
# agregar y visualizar los indicadores
@app.route('/indicador', methods=["GET", "POST"])
def indicador():
    if request.method == "POST": 
        indicador_nombre = request.form["indicador_nombre"]
        indicador_descripcion = request.form["indicador_descripcion"]
        indicador_actividad = request.form["indicador_actividad"]
        cursor.execute("INSERT INTO indicador (indicador_nombre, indicador_descripcion, indicador_actividad) VALUES (%s, %s, %s)", 
                       (indicador_nombre, indicador_descripcion, indicador_actividad))
        db.commit()
        return redirect(url_for("indicador"))

   
    cursor.execute("SELECT * FROM indicador")
    indicador = cursor.fetchall()
    return render_template('indicador.html', indicador=indicador)

#cotizacion
@app.route('/cotizacion', methods=["GET", "POST"])
def cotizacion():
    if request.method == "POST":
        Proyecto = request.form.get("Proyecto")
        Indicador = request.form.get("Indicador")
        Actividad = request.form.get("Actividad")
        Articulo = request.form.get("Articulo")
        Cantidad = request.form.get("Cantidad")
        Precio_unidad = request.form.get("Precio_unidad")
        iva = request.form.get("iva")

        # Manejar valores vacíos
        try:
            Cantidad = float(Cantidad) if Cantidad else 0
            Precio_unidad = float(Precio_unidad) if Precio_unidad else 0
            iva = float(iva) if iva else 0
        except ValueError:
            Cantidad, Precio_unidad, iva = 0, 0, 0

        Precio_total = Cantidad * Precio_unidad
        iva_total = Cantidad * iva

        cursor.execute("INSERT INTO cotizacion (Proyecto, Indicador, Actividad, Articulo, Cantidad, Precio_unidad, Precio_total, iva, iva_total) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                       (Proyecto, Indicador, Actividad, Articulo, Cantidad, Precio_unidad, Precio_total, iva, iva_total))
        db.commit()
        return redirect(url_for("cotizacion", proyecto_actual=Proyecto))

    proyecto_actual = request.args.get("proyecto_actual", "")
    cursor.execute("SELECT * FROM cotizacion WHERE Proyecto = %s", (proyecto_actual,))
    cotizacion = cursor.fetchall()
    cursor.execute("SELECT * FROM proyecto")
    proyecto = cursor.fetchall()
    cursor.execute("SELECT * FROM indicador")
    indicador = cursor.fetchall()
    cursor.execute("SELECT * FROM articulo")
    articulo = cursor.fetchall()

    totalP = 0
    totalI = 0

    # Calcular totalP y totalI de forma segura
    for item in cotizacion:
        try:
            totalP += float(item[6])
            totalI += float(item[8])
        except (ValueError, IndexError):
            continue

    total = totalP + totalI

    return render_template('cotizacion.html', proyecto=proyecto, indicador=indicador, articulo=articulo, cotizacion=cotizacion, total=total, proyecto_actual=proyecto_actual, totalP=totalP, totalI=totalI)





#visualizar las cotizaciones por proyecto seleccionado
@app.route('/')
def index():
    # Obtener proyectos disponibles desde la base de datos
    cursor.execute('SELECT DISTINCT Proyecto FROM cotizacion')
    proyectos = cursor.fetchall()
    return render_template('index.html', proyectos=proyectos)

@app.route('/cotizacion2', methods=['POST'])
def mostrar_cotizacion():
    if request.method == 'POST':
        proyecto = request.form['proyecto']
        if proyecto:
            return redirect(url_for('mostrar_cotizacion_por_proyecto', proyecto=proyecto))
        else:
            return redirect(url_for('index'))

@app.route('/cotizacion2/<proyecto>')
def mostrar_cotizacion_por_proyecto(proyecto):
    # Obtener cotizaciones específicas por proyecto desde la base de datos
    cursor.execute('SELECT * FROM cotizacion WHERE Proyecto = %s', (proyecto,))
    items = cursor.fetchall()

    # Calcular el total del proyecto de forma segura
    total_proyecto = 0
    totalP = 0
    totalI = 0
    for item in items:
        try:
             total_proyecto += float(item[6]) + float(item[8])
             totalP += float(item[6])
             totalI += float(item[8])
        except (ValueError, IndexError):
            continue
        
   

   

    # Obtener proyectos disponibles desde la base de datos para el dropdown
    cursor.execute('SELECT DISTINCT Proyecto FROM cotizacion')
    proyectos = cursor.fetchall()

    # Renderizar la plantilla con los datos obtenidos
    return render_template('index.html', proyectos=proyectos, items=items, total_proyecto=total_proyecto, proyecto=proyecto, totalP=totalP, totalI=totalI)



#borrar articulo
@app.route('/borrar/<int:codigo>')
def borrar(codigo):
    cursor.execute("DELETE FROM articulo WHERE codigo = %s" ,(codigo,))
    db.commit() 
    return redirect(url_for('articulo'))

#borrar indicador o categoria 
@app.route('/borrar_indicador/<int:id>')
def borrar_indicador(id):
    cursor.execute("DELETE FROM indicador WHERE id = %s" ,(id,))
    db.commit() 
    return redirect(url_for('indicador'))

@app.route('/borrar_cotizacion/<Proyecto>')
def borrar_cotizacion(Proyecto):
    cursor.execute("DELETE FROM cotizacion WHERE Proyecto = %s" ,(Proyecto,))
    db.commit() 
    return redirect(url_for('cotizacion'))

@app.route('/borrar_proyecto/<proyecto_codigo>')
def borrar_proyecto(proyecto_codigo):
    cursor.execute("DELETE FROM proyecto WHERE proyecto_codigo = %s" ,(proyecto_codigo,))
    db.commit() 
    return redirect(url_for('proyecto'))
  



if __name__ == '__main__':
    app.run(debug=True)