import csv

# Inicialización de variables y listas
tiempo = 0
tamanioMaximo = 450
listaNuevos = []
listaListos = []
listaListosYSuspendidos = []
listaEjecutando = []
listaTerminados = []
listaParticiones = []

nroParticiones = 1
sumaTiempoEspera = 0
sumaTiempoRetorno = 0
cantidadTerminados = 0
huboCambios = False


class Proceso:
    def __init__(self, id, tiempo_arribo, tiempo_irrupcion, tamanio):

        self.id = id
        self.tiempo_arribo = tiempo_arribo
        self.tiempo_irrupcion = tiempo_irrupcion
        self.tiempo_restante = tiempo_irrupcion
        self.tamanio = tamanio
        self.tiempo_espera = 0
        self.tiempo_finalizacion = 0



class Particion:
    def __init__(self, id, tamanio, inicio):

        self.id = id
        self.tamanio = tamanio
        self.proceso_asignado = None
        self.inicio = inicio
        self.estado = "Libre"



listaParticiones.append(Particion(1, tamanioMaximo, 0))  # Inicialmente, hay una partición libre de tamaño máximo


def recorrer_lista_particiones_bestFit(listaAuxiliar):

    global huboCambios, nroParticiones

    for proceso in listaAuxiliar[:]:

        if proceso.tiempo_arribo > tiempo:
            continue

        mejor_particion = None

        for particion in listaParticiones:
            if particion.estado == "Libre" and particion.tamanio >= proceso.tamanio:
                if mejor_particion is None or particion.tamanio < mejor_particion.tamanio:
                    mejor_particion = particion

        #print(f"\nEvaluando P{proceso.id}")
        #print(f"Tiempo de arribo: {proceso.tiempo_arribo}")
        #print(f"Tiempo actual: {tiempo}")

        for particion in listaParticiones:
            print(f"Partición {particion.id}: "
                f"{particion.tamanio} - {particion.estado}")

       
        # Calcular la cantidad total de procesos admitidos
        cantidad_procesos = (
            len(listaListos)
            + len(listaListosYSuspendidos)
            + len(listaEjecutando)
        )

        print(f"Cantidad de procesos admitidos: {cantidad_procesos}")

        # Si viene de Nuevos, verificar el límite
        if listaAuxiliar is listaNuevos:
            if cantidad_procesos >= 5:
                print("Se alcanzó el límite de procesos.")
                break

        print(f"Evaluando P{proceso.id}")
        print(f"Cantidad de procesos admitidos: {cantidad_procesos}")
        print(f"¿Encontró partición?: {mejor_particion is not None}")

        if mejor_particion is not None:

            # Asignar memoria
            mejor_particion.proceso_asignado = proceso
            mejor_particion.estado = "Ocupada"

            tamanioOriginal = mejor_particion.tamanio

            if tamanioOriginal > proceso.tamanio:
                nroParticiones += 1

                nueva_particion = Particion(
                    nroParticiones,
                    tamanioOriginal - proceso.tamanio,
                    mejor_particion.inicio + proceso.tamanio
                )

                indice = listaParticiones.index(mejor_particion)
                listaParticiones.insert(indice + 1, nueva_particion)


            mejor_particion.tamanio = proceso.tamanio


            # Pasa a Listos, venga de Nuevos o Suspendidos
            listaListos.append(proceso)


            listaAuxiliar.remove(proceso)

            huboCambios = True

        else:
            # Solamente los procesos nuevos pasan a suspendidos
            print(f"P{proceso.id} no encuentra memoria disponible.")

            if listaAuxiliar is listaNuevos:
                listaListosYSuspendidos.append(proceso)
                listaAuxiliar.remove(proceso)
                huboCambios = True



def buscar_proceso_menor_tiempo_irrupcion():
    global listaListos

    menor_tiempo = float('inf')
    indice_menor = -1

    if len(listaListos) > 0:
        for i in range(len(listaListos)):
            if listaListos[i].tiempo_irrupcion < menor_tiempo:
                menor_tiempo = listaListos[i].tiempo_irrupcion
                indice_menor = i

        if indice_menor != -1:

            # Mover el proceso con menor tiempo de irrupción al inicio de la lista
            proceso_menor = listaListos.pop(indice_menor)
            listaListos.insert(0, proceso_menor)


def asignar_procesos_cpu():

    global huboCambios
    if len(listaEjecutando) == 0 and len(listaListos) > 0:
        buscar_proceso_menor_tiempo_irrupcion()
        proceso_a_ejecutar = listaListos.pop(0)
        listaEjecutando.append(proceso_a_ejecutar)
        huboCambios = True

    elif len(listaEjecutando) > 0 and len(listaListos) > 0:
        current_proceso = listaEjecutando[0]
        buscar_proceso_menor_tiempo_irrupcion()

        if listaListos[0].tiempo_irrupcion < current_proceso.tiempo_restante:
            
            listaListos.append(current_proceso)
            listaEjecutando[0] = listaListos.pop(0) 

        huboCambios = True


def mostrar_listas():
    print("\n" + "=" * 60)
    print(f"ESTADO DEL SIMULADOR - TIEMPO: {tiempo}")
    print("=" * 60)

    print("\nNUEVOS:")
    for proceso in listaNuevos:
        print(f"P{proceso.id}", end=" | ")

    print("\n\nLISTOS:")
    for proceso in listaListos:
        print(f"P{proceso.id}", end=" | ")


    print("\n\nLISTOS Y SUSPENDIDOS:")

    for proceso in listaListosYSuspendidos:
        print(f"P{proceso.id}", end=" | ")



    print("\n\nEJECUTANDO:")

    for proceso in listaEjecutando:
        print(f"P{proceso.id} (Restante: {proceso.tiempo_restante})", end=" | ")


    print("\n\nTERMINADOS:")
    for proceso in listaTerminados:
        print(f"P{proceso.id}", end=" | ")

    print("\n" + "=" * 60)



def mostrar_particiones():

    print("\nPARTICIONES:")

    for particion in listaParticiones:

        if particion.proceso_asignado is not None:
            proceso = particion.proceso_asignado.id

        else:
            proceso = "-"



        print(f"Partición {particion.id} | "
              f"Tamaño: {particion.tamanio} | "
              f"Estado: {particion.estado} | "
              f"Proceso: {proceso}")


#Carga de procesos desde un archivo CSV



with open('procesos.csv', 'r', encoding='utf-8', newline='') as archivo_csv:

    lector_csv = csv.reader(archivo_csv, delimiter=';')

    next(lector_csv)      

    for fila in lector_csv:

            if len(listaNuevos) >= 10:
                print("Error: Se ha alcanzado el límite de 10 procesos.")
                break

            try:

                id = int(fila[0])
                tiempo_arribo = int(fila[1])
                tiempo_irrupcion = int(fila[2])
                tamanio = int(fila[3])

            except (ValueError, IndexError):
                print("Error: Fila inválida. Se omitirá este proceso.")
                continue

            if id < 0:
                print(f"Error: El ID del proceso es negativo. Se omitirá este proceso.")
                continue



            if tiempo_arribo < 0:
                print(f"Error: El tiempo de arribo del proceso con ID {id} es negativo. Se omitirá este proceso.")
                continue


            if tiempo_irrupcion < 0:
                print(f"Error: El tiempo de irrupción del proceso con ID {id} es negativo. Se omitirá este proceso.")
                continue        

            if tamanio < 0 or tamanio > 450:
                print(f"Error: El tamaño del proceso con ID {id} es negativo o mayor a 450. Se omitirá este proceso.")
                continue


            proceso = Proceso(id, tiempo_arribo, tiempo_irrupcion, tamanio)
            listaNuevos.append(proceso)



if len(listaNuevos) == 0:
    print("No se han cargado procesos válidos. El simulador no puede continuar.")
    exit()


print("Procesos cargados correctamente:")
print("ID\tTiempo Arribo\tTiempo Irrupción\tTamaño")


for proceso in listaNuevos:

    print(f"{proceso.id}\t{proceso.tiempo_arribo}\t\t{proceso.tiempo_irrupcion}\t\t\t{proceso.tamanio}")



#ciclo Principal del simulador

while len(listaListos) > 0 or len(listaNuevos) > 0 or len(listaEjecutando) > 0 or len(listaListosYSuspendidos) > 0:    


    # Asignar procesos a particiones usando Best Fit
    recorrer_lista_particiones_bestFit(listaNuevos)
    recorrer_lista_particiones_bestFit(listaListosYSuspendidos)


    # Ejecutar procesos en ejecución
    for proceso in listaEjecutando[:]:  # Usar una copia de la lista para evitar problemas al eliminar elementos
        proceso.tiempo_restante -= 1

        if proceso.tiempo_restante <= 0:
            proceso.tiempo_finalizacion = tiempo + 1
            listaTerminados.append(proceso)
            listaEjecutando.remove(proceso)

            # Liberar la partición ocupada
            for particion in listaParticiones:
                if particion.proceso_asignado == proceso:
                    particion.proceso_asignado = None
                    particion.estado = "Libre"
                    indice_particion = listaParticiones.index(particion)

                    # Fusionar con la anterior
                    if indice_particion > 0 and listaParticiones[indice_particion - 1].estado == "Libre":
                        particion_anterior = listaParticiones[indice_particion - 1]
                        particion_anterior.tamanio += particion.tamanio
                        listaParticiones.remove(particion)
                        particion = particion_anterior
                        indice_particion -= 1

                    # Fusionar con la siguiente
                    if indice_particion < len(listaParticiones) - 1 and listaParticiones[indice_particion + 1].estado == "Libre":
                        particion_siguiente = listaParticiones[indice_particion + 1]
                        particion.tamanio += particion_siguiente.tamanio
                        listaParticiones.remove(particion_siguiente)

                    break

            huboCambios = True
            
    recorrer_lista_particiones_bestFit(listaNuevos)
    asignar_procesos_cpu()

    # Incrementar el tiempo del simulador    

    if huboCambios:
        mostrar_listas()
        mostrar_particiones()

    else:      

        print("\n" + "=" * 60)
        print(f"ESTADO DEL SIMULADOR - TIEMPO: {tiempo}")
        print("=" * 60)
        print("\nNo hubo cambios en este ciclo.")

    tiempo += 1
    huboCambios = False

    input("\nPresioná ENTER para continuar...")