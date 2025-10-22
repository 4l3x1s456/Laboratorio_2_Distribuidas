# sin_hilos/server.py
import socket
import csv
import json
import os

HOST = "127.0.0.1"
PORT = 12345
ARCHIVO_CSV = os.path.join(os.path.dirname(__file__), "..", "calificaciones.csv")

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


def _leer_todo():
    with open(ARCHIVO_CSV, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _escribir_todo(filas):
    with open(ARCHIVO_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["ID_Estudiante", "Nombre", "Materia", "Calificacion"]
        )
        writer.writeheader()
        writer.writerows(filas)


def _agregar_fila(id_est, nombre, materia, calif):
    with open(ARCHIVO_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([id_est, nombre, materia, calif])


# --------------------------
# CRUD SIN HILOS – CON VALIDACIÓN DE ID
# --------------------------
def agregar_calificacion(id_est, nombre, materia, calif):
    # Validar número
    try:
        float(calif)
    except ValueError:
        return {"status": "error", "mensaje": "Calificación no numérica."}

    filas = _leer_todo()

    # Validar ID duplicado
    for row in filas:
        if row["ID_Estudiante"] == id_est:
            return {"status": "error", "mensaje": "ID duplicado. El ID ya está registrado."}

    _agregar_fila(id_est, nombre, materia, calif)
    return {"status": "ok", "mensaje": f"Calificación agregada para {nombre}."}


def buscar_por_id(id_est):
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

    filas = _leer_todo()
    actualizado = False

    for row in filas:
        if row["ID_Estudiante"] == id_est:
            row["Calificacion"] = str(nueva_calif)
            actualizado = True

    if not actualizado:
        return {"status": "not_found", "mensaje": "ID no encontrado."}

    _escribir_todo(filas)
    return {"status": "ok", "mensaje": f"Calificación actualizada para ID {id_est}."}


def listar_todas():
    filas = _leer_todo()
    return {"status": "ok", "data": filas}


def eliminar_por_id(id_est):
    filas = _leer_todo()
    nuevas = []
    eliminado = False

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
# SOCKET SERVER SIN HILOS
# --------------------------
def main():
    inicializar_csv()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen(1)
        print(f"[SERVIDOR SECUENCIAL] Escuchando en {HOST}:{PORT} ...")

        try:
            while True:
                client_socket, addr = server_socket.accept()
                print(f"Cliente conectado: {addr}")

                with client_socket:
                    data = client_socket.recv(4096).decode("utf-8")
                    if data:
                        respuesta = procesar_comando(data)
                        client_socket.sendall(json.dumps(respuesta).encode("utf-8"))

                print("Cliente desconectado.")

        except KeyboardInterrupt:
            print("\nServidor detenido.")


if __name__ == "__main__":
    main()
