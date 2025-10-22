# con_hilos/server.py
import socket
import csv
import json
import os
import threading

HOST = "127.0.0.1"
PORT = 12345
ARCHIVO_CSV = os.path.join(os.path.dirname(__file__), "..", "calificaciones.csv")
LOCK = threading.Lock()

COMANDOS_VALIDOS = {"AGREGAR", "BUSCAR", "ACTUALIZAR", "LISTAR", "ELIMINAR"}

# --------------------------
# INICIALIZAR CSV LOCAL
# --------------------------
def inicializar_csv():
    os.makedirs(os.path.dirname(ARCHIVO_CSV), exist_ok=True)
    if not os.path.exists(ARCHIVO_CSV):
        with open(ARCHIVO_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID_Estudiante", "Nombre", "Materia", "Calificacion"])

def _agregar_fila(id_est, nombre, materia, calif):
    with open(ARCHIVO_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([id_est, nombre, materia, calif])

def _leer_todo():
    with open(ARCHIVO_CSV, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def _escribir_todo(filas):
    with open(ARCHIVO_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["ID_Estudiante", "Nombre", "Materia", "Calificacion"])
        writer.writeheader()
        writer.writerows(filas)

# --------------------------
# VALIDACIÓN CON MICROSERVICIO NRC
# --------------------------
NRC_HOST = "127.0.0.1"
NRC_PORT = 12346

def consultar_nrc(nrc: str):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((NRC_HOST, NRC_PORT))
            s.sendall(f"BUSCAR_NRC|{nrc}".encode("utf-8"))
            data = s.recv(8192).decode("utf-8")
        return json.loads(data)
    except Exception:
        return {"status": "error", "mensaje": "Error consultando NRC"}

# --------------------------
# CRUD CON VALIDACIÓN NRC Y VALIDACIÓN ID
# --------------------------
def agregar_calificacion(id_est, nombre, materia, calif):
    # Validación calificación numérica
    try:
        float(calif)
    except ValueError:
        return {"status": "error", "mensaje": "Calificación no numérica."}

    # Validar NRC primero
    r = consultar_nrc(materia)
    if r.get("status") != "ok":
        return {"status": "error", "mensaje": "NRC no válido."}

    # Validar ID duplicado
    with LOCK:
        filas = _leer_todo()
        for row in filas:
            if row["ID_Estudiante"] == id_est:
                return {"status": "error", "mensaje": "ID duplicado. El ID ya está registrado."}

        _agregar_fila(id_est, nombre, materia, calif)

    return {"status": "ok", "mensaje": f"Calificación agregada para {nombre}."}

def buscar_por_id(id_est):
    with LOCK:
        filas = _leer_todo()
    for row in filas:
        if row["ID_Estudiante"] == id_est:
            return {"status": "ok", "data": row}
    return {"status": "not_found", "mensaje": "ID no encontrado."}

def actualizar_calificacion(id_est, nueva_calif):
    try:
        float(nueva_calif)
    except ValueError:
        return {"status": "error", "mensaje": "Nueva calificación no numérica."}

    with LOCK:
        filas = _leer_todo()
        actualizado = False
        for row in filas:
            if row["ID_Estudiante"] == id_est:
                materia_registro = row["Materia"]
                r = consultar_nrc(materia_registro)
                if r.get("status") != "ok":
                    return {"status": "error", "mensaje": "NRC no válido."}

                row["Calificacion"] = str(nueva_calif)
                actualizado = True

        if not actualizado:
            return {"status": "not_found", "mensaje": "ID no encontrado."}

        _escribir_todo(filas)

    return {"status": "ok", "mensaje": f"Calificación actualizada para ID {id_est}."}

def listar_todas():
    with LOCK:
        filas = _leer_todo()
    return {"status": "ok", "data": filas}

def eliminar_por_id(id_est):
    eliminado = False
    with LOCK:
        filas = _leer_todo()
        nuevas = []
        for row in filas:
            if row["ID_Estudiante"] == id_est:
                eliminado = True
            else:
                nuevas.append(row)

        if not eliminado:
            return {"status": "not_found", "mensaje": "ID no encontrado."}

        _escribir_todo(nuevas)

    return {"status": "ok", "mensaje": f"Registro eliminado para ID {id_est}."}

# --------------------------
# ROUTER
# --------------------------
def procesar_comando(comando: str):
    partes = comando.strip().split("|")
    op = partes[0].upper() if partes else ""
    if op not in COMANDOS_VALIDOS:
        return {"status": "error", "mensaje": "Comando inválido."}

    if op == "AGREGAR" and len(partes) == 5:
        return agregar_calificacion(partes[1], partes[2], partes[3], partes[4])
    elif op == "BUSCAR" and len(partes) == 2:
        return buscar_por_id(partes[1])
    elif op == "ACTUALIZAR" and len(partes) == 3:
        return actualizar_calificacion(partes[1], partes[2])
    elif op == "LISTAR":
        return listar_todas()
    elif op == "ELIMINAR" and len(partes) == 2:
        return eliminar_por_id(partes[1])
    else:
        return {"status": "error", "mensaje": "Parámetros incorrectos."}

# --------------------------
# SOCKET SERVER CON HILOS
# --------------------------
def manejar_cliente(client_socket, addr):
    nombre_hilo = threading.current_thread().name
    print(f"[HILO {nombre_hilo}] Cliente conectado {addr}")
    try:
        data = client_socket.recv(4096).decode("utf-8")
        if data:
            resp = procesar_comando(data)
            client_socket.sendall(json.dumps(resp).encode("utf-8"))
    except Exception as e:
        print(f"[HILO {nombre_hilo}] Error: {e}")
    finally:
        client_socket.close()
        print(f"[HILO {nombre_hilo}] Cliente {addr} desconectado")

def main():
    inicializar_csv()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        print(f"[SERVIDOR CONCURRENTE] Escuchando en {HOST}:{PORT} ...")
        try:
            while True:
                client_socket, addr = server_socket.accept()
                hilo = threading.Thread(target=manejar_cliente, args=(client_socket, addr), daemon=True)
                hilo.start()
        except KeyboardInterrupt:
            print("\nServidor detenido.")

if __name__ == "__main__":
    main()
