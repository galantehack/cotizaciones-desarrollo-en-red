from flask import Flask, render_template, request, redirect, url_for, jsonify
import re
import locale # poner los valores en pesos colombianos  
import mysql.connector
from datetime import datetime
from flask_wtf import CSRFProtect
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


@app.route("/subtotales", methods=["GET", "POST"]) 
def subtotales():
   


    # Consulta SQL para sumar los precios por indicador de todos los proyectos
    cursor.execute("""
        SELECT Indicador, SUM(Precio_total) 
        FROM cotizacion 
        GROUP BY Indicador
    """)

    subtotales = cursor.fetchall()
    locale.setlocale(locale.LC_ALL, 'es_CO.UTF-8')  # 'es_CO.UTF-8' para Colombia
    subtotales_formateados = [
        (indicador, locale.currency(precio_total, grouping=True)) 
        for indicador, precio_total in subtotales
    ]
    
    print(subtotales_formateados)
    cursor.close()
  

    return render_template("cotizacion.html", subtotales=subtotales_formateados)





@app.route('/obtener_articulos', methods=['POST'])
def obtener_articulos():
    # Obtener la categoría desde la solicitud JSON
    data = request.get_json()
    categoria = data.get('categoria')

    # Validar la categoría
    if not categoria:
        return jsonify([])  # Retornar una lista vacía si no se proporciona una categoría

    # Obtener los artículos que pertenecen a la categoría seleccionada
    cursor.execute("""
        SELECT * FROM articulo WHERE categoria = %s
    """, (categoria,))
    articulos = cursor.fetchall()

    # Convertir los artículos en formato JSON
    return jsonify(articulos)


@app.route('/llenar_indicador', methods=["GET", "POST"])
def llenar_indicador():
    proyecto_actual = request.args.get("proyecto_actual", "")  # Asegúrate de que contiene el nombre del proyecto
    print(f"Nombre del proyecto actual: {proyecto_actual}")

    cursor.execute("""
        SELECT 
            i.id AS indicador_id,
            i.indicador_nombre,
            i.indicador_descripcion,
            i.indicador_actividad,
            p.proyecto_codigo
          
        FROM 
            proyecto p
        JOIN 
            indicador i ON p.proyecto_codigo = i.proyecto_codigo
        WHERE 
            p.proyecto_nombre = %s
    """, (proyecto_actual,))
    
    indicadores = cursor.fetchall()
    print(indicadores)  # Verificar si hay resultados
    
    # Convertir los resultados a una lista de diccionarios
    resultado = []
    for indicador in indicadores:
        resultado.append({
            'indicador_id': indicador[0],
            'indicador_nombre': indicador[1],
            'indicador_descripcion': indicador[2],
            'indicador_actividad': indicador[3],
            'proyecto_codigo': indicador[4]
            
        })
    
    # Devolver los resultados en formato JSON
    return jsonify(resultado)


@app.route("/llenar_actividad", methods=["GET", "POST"])
def llenar_actividad():
    indicador_id = request.args.get("indicador_id", "")  # Asegúrate de que contiene el nombre del proyecto
    print(f"Nombre del proyecto actual: {indicador_id}")

    cursor.execute("""
        SELECT 
            i.indicador_actividad
        FROM 
            indicador i
        WHERE 
            i.id = %s
        """, (indicador_id,))
    actividad = cursor.fetchone()
    if actividad:
        return jsonify({
            'indicador_actividad': actividad[0]
        })
    else:
        return jsonify({'indicador_actividad': ''})
    

        


@app.route('/dashboard', methods=["GET", "POST"])
def dashboard():
     # Obtener la fecha y hora actual
      current_time = datetime.now().strftime("%H:%M:%S")
      current_date = datetime.now().strftime("%Y-%m-%d")
      cursor.execute("SELECT COUNT(*)  FROM  articulo ")
      cantidadArticulo = cursor.fetchone()[0]
      cursor.execute("SELECT COUNT(*)  FROM  proveedores ")
      cantidadProveedores = cursor.fetchone()[0]
      cursor.execute("SELECT COUNT(*)  FROM  proyecto ")
      cantidadProyectos = cursor.fetchone()[0]
      cursor.execute("SELECT COUNT(*)  FROM  cotizacion ")
      cantidadCotizaciones = cursor.fetchone()[0]
      
      return render_template("dashboard.html", time=current_time, date=current_date, cantidadArticulo=cantidadArticulo, cantidadProveedores=cantidadProveedores, cantidadProyectos=cantidadProyectos, cantidadCotizaciones=cantidadCotizaciones  )

  
   
   # return render_template('dashboard.html')

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
       
        
        cursor.execute("INSERT INTO articulo (codigo, nombre, descripcion, categoria, unidad_medida, precio, iva, fecha, proveedores) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                       ( nombre, descripcion, categoria, unidad_medida, precio, iva, fecha, proveedores))
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
        proyecto_codigo = request.form["proyecto_codigo"]
        cursor.execute("INSERT INTO indicador (indicador_nombre, indicador_descripcion, indicador_actividad,proyecto_codigo) VALUES (%s, %s, %s, %s)", 
                       (indicador_nombre, indicador_descripcion, indicador_actividad, proyecto_codigo))
        db.commit()
        return redirect(url_for("indicador"))

   
    cursor.execute("SELECT * FROM indicador")
    indicador = cursor.fetchall()
    return render_template('indicador.html', indicador=indicador)

#cotizacion
@app.route('/cotizacion', methods=["GET", "POST"])
def cotizacion():
    categorias = get_enum_values("articulo", "categoria")
    if request.method == "POST":
        Proyecto = request.form.get("Proyecto")
        Indicador = request.form.get("Indicador")
        Actividad = request.form.get("Actividad")
        Articulo = request.form.get("Articulo")
        Cantidad = request.form.get("Cantidad")
        Precio_unidad = request.form.get("Precio_unidad")
        iva = request.form.get("iva")
        proyecto_codigo = request.form.get("proyecto_codigo")

        # Manejar valores vacíos
        try:
            Cantidad = float(Cantidad) if Cantidad else 0
            Precio_unidad = float(Precio_unidad) if Precio_unidad else 0
            iva = float(iva) if iva else 0
        except ValueError:
            Cantidad, Precio_unidad, iva = 0, 0, 0

        Precio_total = Cantidad * Precio_unidad
        iva_total = Cantidad * iva

        cursor.execute("INSERT INTO cotizacion (Proyecto, Indicador, Actividad, Articulo, Cantidad, Precio_unidad, Precio_total, iva, iva_total, proyecto_codigo) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                       (Proyecto, Indicador, Actividad, Articulo, Cantidad, Precio_unidad, Precio_total, iva, iva_total,  proyecto_codigo, ))
        db.commit()
        return redirect(url_for("cotizacion", proyecto_actual=Proyecto))

    proyecto_actual = request.args.get("proyecto_actual", "")
    
    cursor.execute("SELECT * FROM cotizacion WHERE Proyecto = %s ORDER BY Indicador", (proyecto_actual,))
    cotizacion = cursor.fetchall()
    
    cursor.execute("SELECT * FROM proyecto")
    proyecto = cursor.fetchall()
    
    
    
    cursor.execute("SELECT * FROM articulo")
    articulo = cursor.fetchall()
    
    cursor.execute("""
        SELECT 
            p.nit,
            p.nombre AS proveedor_nombre,
            p.telefono,
            p.correo,
            p.ubicacion AS ciudad,
            p.fecha AS proveedor_fecha,
            a.codigo,
            a.nombre AS articulo_nombre,
            a.descripcion,
            a.categoria,
            a.unidad_medida,
            a.precio,
            a.iva,
            a.fecha AS articulo_fecha
        FROM 
            proveedores p
        JOIN 
            articulo a 
        ON 
            p.nombre = a.proveedores;
    """)
    articulos = cursor.fetchall()
    
    locale.setlocale(locale.LC_ALL, 'es_CO.UTF-8')  # 'es_CO.UTF-8' para Colombia
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
    total = locale.currency(total, grouping=True)
    totalI= locale.currency(totalI, grouping=True)
    totalP= locale.currency(totalP, grouping=True)
    
    cursor.execute("""
        SELECT Indicador, SUM(Precio_total) 
        FROM cotizacion 
        WHERE Proyecto = %s 
        GROUP BY Indicador
    """, (proyecto_actual,))

    subtotales = cursor.fetchall()
    locale.setlocale(locale.LC_ALL, 'es_CO.UTF-8')  # 'es_CO.UTF-8' para Colombia
    subtotales_formateados = [
        (indicador, locale.currency(precio_total, grouping=True)) 
        for indicador, precio_total in subtotales
    ]
    
    print(subtotales_formateados)
    
    
    return render_template('cotizacion.html', proyecto=proyecto,  articulo=articulo, cotizacion=cotizacion, total=total, proyecto_actual=proyecto_actual, totalP=totalP, totalI=totalI, articulos=articulos, categorias=categorias, subtotales=subtotales_formateados)



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
    locale.setlocale(locale.LC_ALL, 'es_CO.UTF-8')  # 'es_CO.UTF-8' para Colombia # Calcular totalP y totalI de forma segura
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
        
    total_proyecto = locale.currency(total_proyecto, grouping=True)
    totalI= locale.currency(totalI, grouping=True)
    totalP= locale.currency(totalP, grouping=True)

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