# nrcs_server/server.py
import socket
import csv
import json
import os

HOST = "127.0.0.1"
PORT = 12346
ARCHIVO_NRC = os.path.join(os.path.dirname(__file__), "..", "nrcs.csv")

def inicializar_nrcs():
    os.makedirs(os.path.dirname(ARCHIVO_NRC), exist_ok=True)
    if not os.path.exists(ARCHIVO_NRC):
        with open(ARCHIVO_NRC, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["NRC", "Materia"])
            writer.writerow(["MAT101", "Matemáticas I"])
            writer.writerow(["PRO201", "Programación II"])
            writer.writerow(["ARQ301", "Arquitectura de Software"])

def buscar_nrc(nrc: str):
    nrc = nrc.strip().upper()
    with open(ARCHIVO_NRC, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["NRC"].strip().upper() == nrc:
                return {"status": "ok", "data": row}
    return {"status": "not_found", "mensaje": "NRC no existe."}

def procesar(comando: str):
    partes = comando.strip().split("|")
    if len(partes) == 2 and partes[0] == "BUSCAR_NRC":
        return buscar_nrc(partes[1])
    elif partes[0] == "LISTAR_NRC":
        with open(ARCHIVO_NRC, "r", encoding="utf-8") as f:
            return {"status": "ok", "data": list(csv.DictReader(f))}
    return {"status": "error", "mensaje": "Comando inválido."}

def main():
    inicializar_nrcs()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        print(f"[NRC SERVER] Escuchando en {HOST}:{PORT} ...")
        try:
            while True:
                client_socket, addr = server_socket.accept()
                with client_socket:
                    data = client_socket.recv(4096).decode("utf-8")
                    print(f"[NRC SERVER] Recibido: {data}")
                    if data:
                        resp = procesar(data)
                        client_socket.sendall(json.dumps(resp).encode("utf-8"))
        except KeyboardInterrupt:
            print("\n[NRC SERVER] Detenido.")

if __name__ == "__main__":
    main()
