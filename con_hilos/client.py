# con_hilos/client.py
# Igual UX que el cliente secuencial
import os
import socket
import json

HOST = "127.0.0.1"
PORT = 12345

def enviar_comando(comando: str):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(comando.encode("utf-8"))
        data = s.recv(65536).decode("utf-8")
    return json.loads(data)

def menu():
    os.system("cls")
    print("\n--- Menú de Calificaciones (Concurrente) ---")
    print("1. Agregar calificación")
    print("2. Buscar por ID")
    print("3. Actualizar calificación")
    print("4. Listar todas")
    print("5. Eliminar por ID")
    print("6. Salir")
    return input("Elija opción: ").strip()

def main():
    while True:
        opcion = menu()
        if opcion == "1":
            os.system("cls")
            id_est = input("ID: ").strip()
            nombre = input("Nombre: ").strip()
            materia = input("Materia (NRC): ").strip()
            calif = input("Calificación [0-20]: ").strip()
            res = enviar_comando(f"AGREGAR|{id_est}|{nombre}|{materia}|{calif}")
            print(res.get("mensaje", res.get("status")))
            os.system("pause")
        elif opcion == "2":
            os.system("cls")
            id_est = input("ID: ").strip()
            res = enviar_comando(f"BUSCAR|{id_est}")
            if res.get("status") == "ok":
                d = res["data"]
                print(f"ID={d['ID_Estudiante']}, Nombre={d['Nombre']}, Materia={d['Materia']}, Calificación={d['Calificacion']}")
            else:
                print(res.get("mensaje", res.get("status")))
            os.system("pause")
        elif opcion == "3":
            os.system("cls")
            id_est = input("ID: ").strip()
            nueva = input("Nueva calificación: ").strip()
            res = enviar_comando(f"ACTUALIZAR|{id_est}|{nueva}")
            print(res.get("mensaje", res.get("status")))
            os.system("pause")
        elif opcion == "4":
            os.system("cls")
            res = enviar_comando("LISTAR")
            if res.get("status") == "ok":
                filas = res.get("data", [])
                if not filas:
                    print("(sin registros)")
                for row in filas:
                    print(row)
            else:
                print(res.get("mensaje", res.get("status")))
            os.system("pause")
        elif opcion == "5":
            os.system("cls")
            id_est = input("ID: ").strip()
            res = enviar_comando(f"ELIMINAR|{id_est}")
            print(res.get("mensaje", res.get("status")))
            os.system("pause")
        elif opcion == "6":
            break
        else:
            print("Opción inválida")
            os.system("pause")

if __name__ == "__main__":
    main()
