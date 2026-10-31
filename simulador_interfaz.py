import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


class Proceso:
    def __init__(self, id, tiempo_arribo, tiempo_irrupcion, tamanio):
        self.id = id
        self.tiempo_arribo = tiempo_arribo
        self.tiempo_irrupcion = tiempo_irrupcion
        self.tiempo_restante = tiempo_irrupcion
        self.tamanio = tamanio
        self.tiempo_espera = 0
        self.tiempo_finalizacion = 0
        self.tiempo_retorno = 0


class Particion:
    def __init__(self, id, tamanio, inicio):
        self.id = id
        self.tamanio = tamanio
        self.proceso_asignado = None
        self.inicio = inicio
        self.estado = "Libre"


class Simulador:
    """Contiene la misma lógica del simulador de consola, organizada por ciclos."""

    def __init__(self, procesos):
        self.tiempo = 0
        self.tamanioMaximo = 450
        self.listaNuevos = list(procesos)
        self.listaListos = []
        self.listaListosYSuspendidos = []
        self.listaEjecutando = []
        self.listaTerminados = []
        self.listaParticiones = [Particion(1, self.tamanioMaximo, 0)]
        self.nroParticiones = 1
        self.huboCambios = False
        self.finalizado = False

    def recorrer_lista_particiones_bestFit(self, listaAuxiliar):
        for proceso in listaAuxiliar[:]:
            if proceso.tiempo_arribo > self.tiempo:
                continue

            mejor_particion = None
            for particion in self.listaParticiones:
                if particion.estado == "Libre" and particion.tamanio >= proceso.tamanio:
                    if mejor_particion is None or particion.tamanio < mejor_particion.tamanio:
                        mejor_particion = particion

            cantidad_procesos = (
                len(self.listaListos)
                + len(self.listaListosYSuspendidos)
                + len(self.listaEjecutando)
            )

            if listaAuxiliar is self.listaNuevos and cantidad_procesos >= 5:
                break

            if mejor_particion is not None:
                mejor_particion.proceso_asignado = proceso
                mejor_particion.estado = "Ocupada"
                tamanioOriginal = mejor_particion.tamanio

                if tamanioOriginal > proceso.tamanio:
                    self.nroParticiones += 1
                    nueva_particion = Particion(
                        self.nroParticiones,
                        tamanioOriginal - proceso.tamanio,
                        mejor_particion.inicio + proceso.tamanio
                    )
                    indice = self.listaParticiones.index(mejor_particion)
                    self.listaParticiones.insert(indice + 1, nueva_particion)

                mejor_particion.tamanio = proceso.tamanio
                self.listaListos.append(proceso)
                listaAuxiliar.remove(proceso)
                self.huboCambios = True
            else:
                if listaAuxiliar is self.listaNuevos:
                    self.listaListosYSuspendidos.append(proceso)
                    listaAuxiliar.remove(proceso)
                    self.huboCambios = True

    def buscar_proceso_menor_tiempo_irrupcion(self):
        menor_tiempo = float("inf")
        indice_menor = -1

        if len(self.listaListos) > 0:
            for i in range(len(self.listaListos)):
                if self.listaListos[i].tiempo_restante < menor_tiempo:
                    menor_tiempo = self.listaListos[i].tiempo_restante
                    indice_menor = i

            if indice_menor != -1:
                proceso_menor = self.listaListos.pop(indice_menor)
                self.listaListos.insert(0, proceso_menor)

    def asignar_procesos_cpu(self):
        if len(self.listaEjecutando) == 0 and len(self.listaListos) > 0:
            self.buscar_proceso_menor_tiempo_irrupcion()
            proceso_a_ejecutar = self.listaListos.pop(0)
            self.listaEjecutando.append(proceso_a_ejecutar)
            self.huboCambios = True

        elif len(self.listaEjecutando) > 0 and len(self.listaListos) > 0:
            current_proceso = self.listaEjecutando[0]
            self.buscar_proceso_menor_tiempo_irrupcion()

            if self.listaListos[0].tiempo_restante < current_proceso.tiempo_restante:
                self.listaListos.append(current_proceso)
                self.listaEjecutando[0] = self.listaListos.pop(0)
                self.huboCambios = True

    def liberar_particion(self, proceso):
        for particion in self.listaParticiones:
            if particion.proceso_asignado == proceso:
                particion.proceso_asignado = None
                particion.estado = "Libre"
                indice_particion = self.listaParticiones.index(particion)

                # Fusionar con la partición anterior si está libre.
                if indice_particion > 0 and self.listaParticiones[indice_particion - 1].estado == "Libre":
                    particion_anterior = self.listaParticiones[indice_particion - 1]
                    particion_anterior.tamanio += particion.tamanio
                    self.listaParticiones.remove(particion)
                    particion = particion_anterior
                    indice_particion -= 1

                # Fusionar con la partición siguiente si está libre.
                if (indice_particion < len(self.listaParticiones) - 1
                        and self.listaParticiones[indice_particion + 1].estado == "Libre"):
                    particion_siguiente = self.listaParticiones[indice_particion + 1]
                    particion.tamanio += particion_siguiente.tamanio
                    self.listaParticiones.remove(particion_siguiente)
                break

    def siguiente_ciclo(self):
        if self.finalizado:
            return

        self.huboCambios = False

        self.recorrer_lista_particiones_bestFit(self.listaNuevos)
        self.recorrer_lista_particiones_bestFit(self.listaListosYSuspendidos)

        for proceso in self.listaEjecutando[:]:
            proceso.tiempo_restante -= 1

            if proceso.tiempo_restante <= 0:
                proceso.tiempo_finalizacion = self.tiempo + 1
                proceso.tiempo_retorno = proceso.tiempo_finalizacion - proceso.tiempo_arribo
                proceso.tiempo_espera = proceso.tiempo_retorno - proceso.tiempo_irrupcion

                self.listaTerminados.append(proceso)
                self.listaEjecutando.remove(proceso)
                self.liberar_particion(proceso)
                self.huboCambios = True

        self.recorrer_lista_particiones_bestFit(self.listaNuevos)
        self.asignar_procesos_cpu()

        self.tiempo += 1

        if not (self.listaListos or self.listaNuevos or self.listaEjecutando or self.listaListosYSuspendidos):
            self.finalizado = True


def cargar_procesos(ruta):
    procesos = []
    errores = []

    with open(ruta, "r", encoding="utf-8-sig", newline="") as archivo_csv:
        lector_csv = csv.reader(archivo_csv, delimiter=";")
        next(lector_csv, None)

        for numero_fila, fila in enumerate(lector_csv, start=2):
            if len(procesos) >= 10:
                errores.append("Se alcanzó el límite de 10 procesos.")
                break

            try:
                id = int(fila[0])
                tiempo_arribo = int(fila[1])
                tiempo_irrupcion = int(fila[2])
                tamanio = int(fila[3])
            except (ValueError, IndexError):
                errores.append(f"Fila {numero_fila}: datos inválidos; se omitió.")
                continue

            if id < 0:
                errores.append(f"Fila {numero_fila}: ID negativo; se omitió.")
                continue
            if tiempo_arribo < 0:
                errores.append(f"Fila {numero_fila}: tiempo de arribo negativo; se omitió.")
                continue
            if tiempo_irrupcion < 0:
                errores.append(f"Fila {numero_fila}: tiempo de irrupción negativo; se omitió.")
                continue
            if tamanio < 0 or tamanio > 450:
                errores.append(f"Fila {numero_fila}: tamaño fuera del rango 0-450; se omitió.")
                continue

            procesos.append(Proceso(id, tiempo_arribo, tiempo_irrupcion, tamanio))

    if not procesos:
        raise ValueError("No se encontraron procesos válidos en el CSV.")

    return procesos, errores


class InterfazSimulador:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador de gestión de memoria y CPU")
        self.root.geometry("1120x790")
        self.root.minsize(950, 650)

        self.simulador = None
        self.after_id = None
        self.velocidad = tk.IntVar(value=900)
        self.archivo_actual = None

        self.crear_interfaz()
        self.seleccionar_archivo()

    def crear_interfaz(self):
        contenedor = ttk.Frame(self.root, padding=12)
        contenedor.pack(fill="both", expand=True)

        encabezado = ttk.Frame(contenedor)
        encabezado.pack(fill="x", pady=(0, 10))

        ttk.Label(encabezado, text="SIMULADOR DE PROCESOS",
                  font=("Segoe UI", 17, "bold")).pack(side="left")
        self.lbl_tiempo = ttk.Label(encabezado, text="Tiempo: —",
                                    font=("Segoe UI", 13, "bold"))
        self.lbl_tiempo.pack(side="right")

        controles = ttk.LabelFrame(contenedor, text="Controles", padding=8)
        controles.pack(fill="x", pady=(0, 10))

        ttk.Button(controles, text="Cargar CSV", command=self.seleccionar_archivo).pack(side="left", padx=4)
        self.btn_siguiente = ttk.Button(controles, text="Siguiente ciclo",
                                        command=self.avanzar, state="disabled")
        self.btn_siguiente.pack(side="left", padx=4)
        self.btn_iniciar = ttk.Button(controles, text="Iniciar", command=self.iniciar,
                                      state="disabled")
        self.btn_iniciar.pack(side="left", padx=4)
        self.btn_pausar = ttk.Button(controles, text="Pausar", command=self.pausar,
                                     state="disabled")
        self.btn_pausar.pack(side="left", padx=4)
        self.btn_reiniciar = ttk.Button(controles, text="Reiniciar", command=self.reiniciar,
                                        state="disabled")
        self.btn_reiniciar.pack(side="left", padx=4)

        ttk.Label(controles, text="Velocidad:").pack(side="left", padx=(18, 4))
        ttk.Scale(controles, from_=150, to=2000, variable=self.velocidad,
                  orient="horizontal", length=150).pack(side="left")
        self.lbl_archivo = ttk.Label(controles, text="Ningún archivo cargado")
        self.lbl_archivo.pack(side="right", padx=5)

        paneles = ttk.Frame(contenedor)
        paneles.pack(fill="both", expand=True)

        estados = ttk.LabelFrame(paneles, text="Estados de los procesos", padding=8)
        estados.pack(side="left", fill="both", expand=True, padx=(0, 6))

        self.arboles = {}
        nombres = [
            ("Nuevos", "NUEVOS"),
            ("Listos", "LISTOS"),
            ("Listos y suspendidos", "LISTOS Y SUSPENDIDOS"),
            ("Ejecutando", "EJECUTANDO"),
            ("Terminados", "TERMINADOS"),
        ]
        for clave, titulo in nombres:
            grupo = ttk.LabelFrame(estados, text=titulo, padding=5)
            grupo.pack(fill="x", pady=4)
            columnas = ("id", "restante", "memoria")
            arbol = ttk.Treeview(grupo, columns=columnas, show="headings", height=3)
            arbol.heading("id", text="Proceso")
            arbol.heading("restante", text="Tiempo restante")
            arbol.heading("memoria", text="Tamaño")
            arbol.column("id", width=85, anchor="center")
            arbol.column("restante", width=120, anchor="center")
            arbol.column("memoria", width=90, anchor="center")
            arbol.pack(fill="x")
            self.arboles[clave] = arbol

        derecha = ttk.Frame(paneles)
        derecha.pack(side="left", fill="both", expand=True, padx=(6, 0))

        cpu = ttk.LabelFrame(derecha, text="CPU", padding=10)
        cpu.pack(fill="x", pady=(0, 8))
        self.lbl_cpu = ttk.Label(cpu, text="Sin proceso ejecutándose",
                                 font=("Segoe UI", 12, "bold"))
        self.lbl_cpu.pack(anchor="w")

        memoria = ttk.LabelFrame(derecha, text="Distribución de memoria", padding=10)
        memoria.pack(fill="both", expand=True)
        self.canvas_memoria = tk.Canvas(
            memoria, height=150, background="#17191d",
            highlightthickness=0
        )
        self.canvas_memoria.pack(fill="x", expand=True)
        self.canvas_memoria.bind("<Configure>", lambda event: self.dibujar_memoria())
        ttk.Label(memoria, text="Azul: ocupada     Gris: libre",
                  font=("Segoe UI", 9)).pack(anchor="w", pady=(5, 0))
        self.lbl_memoria = ttk.Label(memoria, text="Memoria libre: 450 | Ocupada: 0")
        self.lbl_memoria.pack(anchor="w", pady=(5, 0))

        informe = ttk.LabelFrame(contenedor, text="Informe final", padding=8)
        informe.pack(fill="x", pady=(10, 0))
        cols = ("proceso", "arribo", "finalizacion", "retorno", "espera")
        self.tabla_informe = ttk.Treeview(informe, columns=cols, show="headings", height=4)
        titulos_inf = {
            "proceso": "Proceso", "arribo": "Arribo", "finalizacion": "Finalización",
            "retorno": "Retorno", "espera": "Espera"
        }
        for col in cols:
            self.tabla_informe.heading(col, text=titulos_inf[col])
            self.tabla_informe.column(col, width=110, anchor="center")
        self.tabla_informe.pack(fill="x")
        self.lbl_estadisticas = ttk.Label(informe, text="El informe estará disponible al finalizar.")
        self.lbl_estadisticas.pack(anchor="w", pady=(6, 0))

        self.lbl_estado = ttk.Label(contenedor, text="Cargá un archivo CSV para comenzar.",
                                   relief="sunken", anchor="w")
        self.lbl_estado.pack(fill="x", pady=(8, 0))

    def seleccionar_archivo(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo de procesos",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")]
        )
        if not ruta:
            return
        try:
            procesos, errores = cargar_procesos(ruta)
        except (OSError, ValueError, csv.Error) as error:
            messagebox.showerror("Error al cargar", str(error))
            return

        self.pausar()
        self.simulador = Simulador(procesos)
        self.archivo_actual = ruta
        self.lbl_archivo.config(text=ruta.split("/")[-1].split("\\")[-1])
        self.habilitar_controles()
        self.actualizar_vista()
        mensaje = f"Se cargaron {len(procesos)} procesos."
        if errores:
            mensaje += " " + " ".join(errores)
        self.lbl_estado.config(text=mensaje)
        if errores:
            messagebox.showwarning("Archivo cargado con observaciones", mensaje)

    def habilitar_controles(self):
        self.btn_siguiente.config(state="normal")
        self.btn_iniciar.config(state="normal")
        self.btn_reiniciar.config(state="normal")
        self.btn_pausar.config(state="disabled")

    def actualizar_vista(self):
        if self.simulador is None:
            return
        s = self.simulador
        self.lbl_tiempo.config(text=f"Tiempo: {s.tiempo}")

        listas = {
            "Nuevos": s.listaNuevos,
            "Listos": s.listaListos,
            "Listos y suspendidos": s.listaListosYSuspendidos,
            "Ejecutando": s.listaEjecutando,
            "Terminados": s.listaTerminados,
        }
        for nombre, procesos in listas.items():
            arbol = self.arboles[nombre]
            arbol.delete(*arbol.get_children())
            for p in procesos:
                restante = p.tiempo_restante if nombre != "Terminados" else "—"
                arbol.insert("", "end", values=(f"P{p.id}", restante, p.tamanio))

        if s.listaEjecutando:
            p = s.listaEjecutando[0]
            self.lbl_cpu.config(text=f"P{p.id}  |  Tiempo restante: {p.tiempo_restante}  |  Memoria: {p.tamanio}")
        else:
            self.lbl_cpu.config(text="CPU libre")

        memoria_libre = sum(part.tamanio for part in s.listaParticiones if part.estado == "Libre")
        memoria_ocupada = sum(part.tamanio for part in s.listaParticiones if part.estado != "Libre")
        self.lbl_memoria.config(
            text=f"Memoria libre: {memoria_libre} KB | Ocupada: {memoria_ocupada} KB | Total: {memoria_libre + memoria_ocupada} KB"
        )
        self.dibujar_memoria()

        if s.finalizado:
            self.mostrar_informe()
            self.btn_siguiente.config(state="disabled")
            self.btn_iniciar.config(state="disabled")
            self.btn_pausar.config(state="disabled")
            self.lbl_estado.config(text="Simulación finalizada.")
        else:
            self.btn_siguiente.config(state="normal")
            self.btn_iniciar.config(state="normal")

    def dibujar_memoria(self):
        if self.simulador is None or not hasattr(self, "canvas_memoria"):
            return
        canvas = self.canvas_memoria
        canvas.delete("all")
        ancho = max(canvas.winfo_width(), 300)
        alto = max(canvas.winfo_height(), 110)
        margen = 8
        espacio = 4
        ancho_util = ancho - margen * 2 - espacio * (len(self.simulador.listaParticiones) - 1)
        x = margen
        y1, y2 = 12, min(alto - 28, 92)

        for part in self.simulador.listaParticiones:
            w = max(2, ancho_util * part.tamanio / self.simulador.tamanioMaximo)
            ocupada = part.estado != "Libre"
            color = "#2878b9" if ocupada else "#cfd4da"
            color_texto = "white" if ocupada else "#263238"
            x2 = x + w
            canvas.create_rectangle(x, y1, x2, y2, fill=color, outline=color, width=1)
            if w >= 42:
                proceso = f"P{part.proceso_asignado.id}" if ocupada else "Libre"
                canvas.create_text((x + x2) / 2, y1 + 27, text=proceso,
                                   fill=color_texto, font=("Segoe UI", 10, "bold"))
                canvas.create_text((x + x2) / 2, y1 + 51, text=f"{part.tamanio} KB",
                                   fill=color_texto, font=("Segoe UI", 9))
            elif w >= 20:
                canvas.create_text((x + x2) / 2, (y1 + y2) / 2,
                                   text=f"{part.tamanio}", fill=color_texto,
                                   font=("Segoe UI", 8, "bold"))
            canvas.create_text((x + x2) / 2, y2 + 13, text=f"#{part.id}",
                               fill="#d5d9df", font=("Segoe UI", 8))
            x = x2 + espacio

    def avanzar(self):
        if self.simulador is None or self.simulador.finalizado:
            return
        self.simulador.siguiente_ciclo()
        self.actualizar_vista()

    def iniciar(self):
        if self.simulador is None or self.simulador.finalizado or self.after_id is not None:
            return
        self.btn_iniciar.config(state="disabled")
        self.btn_pausar.config(state="normal")
        self.btn_siguiente.config(state="disabled")
        self.ejecutar_automatico()

    def ejecutar_automatico(self):
        if self.simulador is None or self.simulador.finalizado:
            self.pausar()
            return
        self.simulador.siguiente_ciclo()
        self.actualizar_vista()
        if not self.simulador.finalizado:
            self.after_id = self.root.after(max(50, int(self.velocidad.get())), self.ejecutar_automatico)
        else:
            self.after_id = None
            self.pausar()

    def pausar(self):
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        if self.simulador is not None and not self.simulador.finalizado:
            self.btn_iniciar.config(state="normal")
            self.btn_siguiente.config(state="normal")
            self.btn_pausar.config(state="disabled")

    def reiniciar(self):
        if not self.archivo_actual:
            return
        self.pausar()
        try:
            procesos, errores = cargar_procesos(self.archivo_actual)
            self.simulador = Simulador(procesos)
            self.actualizar_vista()
            self.lbl_estado.config(text="Simulación reiniciada.")
            self.lbl_estadisticas.config(text="El informe estará disponible al finalizar.")
            self.tabla_informe.delete(*self.tabla_informe.get_children())
            self.habilitar_controles()
        except Exception as error:
            messagebox.showerror("Error", str(error))

    def mostrar_informe(self):
        s = self.simulador
        self.tabla_informe.delete(*self.tabla_informe.get_children())
        procesos = sorted(s.listaTerminados, key=lambda p: p.id)
        suma_espera = 0
        suma_retorno = 0
        for p in procesos:
            self.tabla_informe.insert(
                "", "end",
                values=(f"P{p.id}", p.tiempo_arribo, p.tiempo_finalizacion,
                        p.tiempo_retorno, p.tiempo_espera)
            )
            suma_espera += p.tiempo_espera
            suma_retorno += p.tiempo_retorno

        cantidad = len(procesos)
        if cantidad > 0:
            promedio_espera = suma_espera / cantidad
            promedio_retorno = suma_retorno / cantidad
            rendimiento = cantidad / s.tiempo if s.tiempo > 0 else 0
            self.lbl_estadisticas.config(
                text=(f"Espera promedio: {promedio_espera:.2f}    "
                      f"Retorno promedio: {promedio_retorno:.2f}    "
                      f"Rendimiento: {rendimiento:.2f} procesos/unidad de tiempo")
            )
        else:
            self.lbl_estadisticas.config(text="No hay procesos terminados para calcular estadísticas.")


if __name__ == "__main__":
    root = tk.Tk()
    app = InterfazSimulador(root)
    root.mainloop()
