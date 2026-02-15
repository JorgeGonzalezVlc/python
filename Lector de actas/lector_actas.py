# lector_actas.py
# Requisitos:
#   pip install openai-whisper pdfplumber ollama reportlab
#   ffmpeg en PATH
#   ollama instalado y con modelo mistral descargado: ollama pull mistral

import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import whisper
import pdfplumber
import ollama
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
import hashlib
import json
import os
from datetime import datetime

# ---------- Variables ----------
ruta_audio = None
ruta_pdf = None
CACHE_FILE = "cache_transcripciones.json"

# ---------- Funciones de Caché ----------
def get_cache():
    """Carga el caché de transcripciones si existe"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_cache(cache):
    """Guarda el caché de transcripciones"""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f)
    except:
        pass

def get_file_hash(filepath):
    """Genera un hash MD5 del archivo para usar como clave de caché"""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None

# ---------- Funciones de verificación ----------
def verificar_ollama():
    """Verifica que Ollama esté instalado y corriendo"""
    try:
        ollama.list()
        return True
    except Exception as e:
        messagebox.showerror(
            "Ollama no detectado",
            "Ollama no está corriendo o no está instalado.\n\n"
            "Pasos:\n"
            "1. Instala Ollama desde: https://ollama.ai\n"
            "2. Ejecuta en terminal: ollama pull mistral\n"
            "3. Asegúrate de que Ollama esté corriendo\n\n"
            f"Error: {str(e)}"
        )
        return False

# ---------- Funciones de carga ----------
def cargar_audio():
    global ruta_audio
    try:
        temp = filedialog.askopenfilename(
            title="Seleccionar archivo de audio",
            filetypes=[
                ("Archivos de audio", "*.mp3 *.wav *.m4a *.ogg *.flac"),
                ("Todos los archivos", "*.*")
            ]
        )
        if temp:
            ruta_audio = temp
            nombre_archivo = os.path.basename(ruta_audio)
            lbl_audio.config(text=f"✓ Audio cargado:\n{nombre_archivo}")
    except Exception as e:
        messagebox.showerror("Error", f"Error al cargar audio:\n{e}")

def cargar_pdf():
    global ruta_pdf
    try:
        temp = filedialog.askopenfilename(
            title="Seleccionar archivo PDF",
            filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")]
        )
        if temp:
            ruta_pdf = temp
            nombre_archivo = os.path.basename(ruta_pdf)
            lbl_pdf.config(text=f"✓ PDF cargado:\n{nombre_archivo}")
    except Exception as e:
        messagebox.showerror("Error", f"Error al cargar PDF:\n{e}")

# ---------- Funciones de procesamiento ----------
def limpiar_transcripcion(texto_audio):
    """
    Usa Mistral para dar coherencia gramatical y estilística a la transcripción,
    manteniendo el significado sin inventar contenido.
    """
    prompt = f"""
Eres un asistente experto en procesamiento de lenguaje.
Tienes la siguiente transcripción automática de un audio (puede contener errores, frases inconexas o redundancias).

Tu tarea:
1. Reescribe el texto para que sea coherente y gramaticalmente correcto.
2. Mantén el SIGNIFICADO original, no inventes contenido.
3. No resumas, solo organiza y corrige.

Texto:
{texto_audio}
"""
    try:
        resp = ollama.chat(
            model="mistral",
            messages=[{"role": "user", "content": prompt}]
        )
        return resp["message"]["content"].strip()
    except Exception as e:
        print(f"Error en limpieza: {e}")
        return texto_audio  # fallback si Ollama falla

def analizar_con_mistral(texto_audio, texto_pdf):
    """
    Llama al modelo Mistral con Ollama para comparar transcripción y acta.
    El análisis es semántico: compara ideas aunque estén expresadas de forma distinta.
    """
    prompt = f"""
Eres un experto en análisis semántico. 
Tu tarea es COMPARAR dos textos: la TRANSCRIPCIÓN de una reunión y el ACTA escrita.

Muy importante:
- No compares palabras literales, compara IDEAS y SIGNIFICADOS.
- Considera equivalentes frases con distinta redacción si expresan lo mismo.
  Ejemplo: "poseo un coche rojo" = "tengo un coche rojo" = "mi coche es rojo".
- Si un fragmento es solo un cambio de estilo pero con mismo sentido, cuenta como COINCIDENCIA.
- Si una idea aparece en uno y no en el otro, márcalo como OMISIÓN o EXCESO.
- Señala DISCREPANCIAS solo cuando el sentido cambie (ej: cantidad, condición, fecha, persona responsable).

TRANSCRIPCIÓN:
{texto_audio}

ACTA:
{texto_pdf}

Devuélveme un informe en español con estas secciones claras:
1) Resumen breve de la reunión (máx 6 líneas).
2) Resumen breve del acta (máx 6 líneas).
3) Coincidencias clave (ideas presentes en ambos).
4) Omisiones (ideas en la reunión que no aparecen en el acta).
5) Excesos (ideas en el acta que no aparecen en la reunión).
6) Discrepancias (cuando lo que se dice NO es lo mismo: cifras, fechas, condiciones, responsables).
7) Conclusión: grado de fidelidad del acta (porcentaje estimado y justificación breve).
"""
    try:
        resp = ollama.chat(
            model="mistral",
            messages=[{"role": "user", "content": prompt}]
        )
        return resp["message"]["content"]
    except Exception as e:
        return f"❌ Error al usar Mistral: {e}"

def transcribir_con_cache(ruta_audio, modelo="small", progress_callback=None):
    """
    Transcribe el audio usando Whisper, con sistema de caché
    para evitar re-procesar el mismo archivo.
    """
    file_hash = get_file_hash(ruta_audio)
    
    if file_hash:
        cache = get_cache()
        cache_key = f"{file_hash}_{modelo}"
        
        # Si está en caché, usar esa transcripción
        if cache_key in cache:
            if progress_callback:
                progress_callback("✓ Transcripción encontrada en caché")
            return cache[cache_key]
    
    # Si no está en caché, transcribir
    if progress_callback:
        progress_callback(f"Transcribiendo con Whisper (modelo: {modelo})...")
    
    model = whisper.load_model(modelo)
    res = model.transcribe(ruta_audio, language="es")
    texto = res.get("text", "").strip()
    
    # Guardar en caché
    if file_hash and texto:
        cache = get_cache()
        cache[cache_key] = texto
        save_cache(cache)
    
    return texto

def comparar():
    """Función principal que ejecuta todo el proceso de comparación"""
    if not ruta_audio or not ruta_pdf:
        messagebox.showerror("Error", "Debes cargar un archivo de audio y un PDF antes de comparar.")
        return
    
    # Verificar que Ollama esté disponible
    if not verificar_ollama():
        return

    # Crear label de progreso
    progress_label = tk.Label(ventana, text="", bg="#bbe6fa", fg="#000", font=("Arial", 10, "bold"))
    progress_label.pack(before=frame_textos, pady=5)
    
    def actualizar_progreso(mensaje):
        progress_label.config(text=mensaje)
        ventana.update()
    
    try:
        # Limpiar áreas
        salida_audio.delete("1.0", tk.END)
        salida_pdf.delete("1.0", tk.END)
        salida_analisis.delete("1.0", tk.END)
        
        # Deshabilitar botones durante el proceso
        btn_comparar.config(state="disabled")
        btn_audio.config(state="disabled")
        btn_pdf.config(state="disabled")

        # 1) Transcripción con Whisper
        actualizar_progreso("⏳ 1/4: Transcribiendo audio con Whisper...")
        modelo_whisper = modelo_var.get()
        texto_audio = transcribir_con_cache(ruta_audio, modelo_whisper, actualizar_progreso)

        # 2) Limpieza con Mistral
        actualizar_progreso("⏳ 2/4: Refinando transcripción con IA...")
        texto_audio = limpiar_transcripcion(texto_audio)

        # Mostrar transcripción procesada
        salida_audio.insert(tk.END, texto_audio if texto_audio else "(Sin texto o no se pudo transcribir)")

        # 3) Lectura del PDF
        actualizar_progreso("⏳ 3/4: Extrayendo texto del PDF...")
        texto_pdf = ""
        with pdfplumber.open(ruta_pdf) as pdf:
            for p in pdf.pages:
                t = p.extract_text()
                if t:
                    texto_pdf += t + "\n\n"
        texto_pdf = texto_pdf.strip()
        salida_pdf.insert(tk.END, texto_pdf if texto_pdf else "(No se extrajo texto del PDF)")

        # 4) Análisis con Mistral (Ollama)
        actualizar_progreso("⏳ 4/4: Generando análisis con IA...")
        analysis = analizar_con_mistral(texto_audio, texto_pdf)

        salida_analisis.insert(tk.END, analysis)

        # Activar botones de guardado
        btn_guardar_informe.config(state="normal")
        btn_guardar_todo.config(state="normal")
        
        actualizar_progreso("✅ ¡Proceso completado exitosamente!")

    except Exception as e:
        messagebox.showerror("Error en el proceso", f"Ocurrió un error:\n\n{str(e)}")
        actualizar_progreso("❌ Error en el proceso")
    
    finally:
        # Re-habilitar botones
        btn_comparar.config(state="normal")
        btn_audio.config(state="normal")
        btn_pdf.config(state="normal")
        # Eliminar label de progreso después de 3 segundos
        ventana.after(3000, progress_label.destroy)

# ---------- Funciones de guardado ----------
def guardar_informe():
    """Guarda solo el análisis en formato PDF mejorado"""
    texto = salida_analisis.get("1.0", tk.END).strip()
    if not texto:
        messagebox.showerror("Error", "No hay informe para guardar.")
        return

    ruta = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[
            ("PDF files", "*.pdf"),
            ("Text files", "*.txt"),
            ("Markdown files", "*.md")
        ],
        title="Guardar informe como..."
    )
    if not ruta:
        return

    try:
        extension = os.path.splitext(ruta)[1].lower()
        
        if extension == '.pdf':
            # Guardar como PDF con mejor formato
            doc = SimpleDocTemplate(ruta, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Título
            titulo = Paragraph("Análisis de Reunión vs Acta", styles['Title'])
            story.append(titulo)
            story.append(Spacer(1, 12))
            
            # Fecha
            fecha = Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal'])
            story.append(fecha)
            story.append(Spacer(1, 20))
            
            # Contenido
            for linea in texto.split("\n"):
                if linea.strip():
                    p = Paragraph(linea.replace('<', '&lt;').replace('>', '&gt;'), styles['Normal'])
                    story.append(p)
                    story.append(Spacer(1, 6))
            
            doc.build(story)
        else:
            # Guardar como texto o markdown
            with open(ruta, 'w', encoding='utf-8') as f:
                f.write(f"# Análisis de Reunión vs Acta\n")
                f.write(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")
                f.write("---\n\n")
                f.write(texto)
        
        messagebox.showinfo("Éxito", f"Informe guardado en:\n{ruta}")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo guardar el informe:\n{e}")

def guardar_todo():
    """Guarda transcripción, PDF extraído y análisis en una carpeta"""
    if not salida_analisis.get("1.0", tk.END).strip():
        messagebox.showerror("Error", "No hay datos para guardar. Primero ejecuta la comparación.")
        return
    
    directorio = filedialog.askdirectory(title="Selecciona carpeta para guardar todos los archivos")
    if not directorio:
        return
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Guardar transcripción
        trans_path = os.path.join(directorio, f"transcripcion_{timestamp}.txt")
        with open(trans_path, "w", encoding="utf-8") as f:
            f.write("=== TRANSCRIPCIÓN DEL AUDIO (REFINADA CON IA) ===\n\n")
            f.write(salida_audio.get("1.0", tk.END))
        
        # 2. Guardar texto del PDF
        pdf_path = os.path.join(directorio, f"pdf_extraido_{timestamp}.txt")
        with open(pdf_path, "w", encoding="utf-8") as f:
            f.write("=== CONTENIDO EXTRAÍDO DEL PDF ===\n\n")
            f.write(salida_pdf.get("1.0", tk.END))
        
        # 3. Guardar análisis como PDF
        analisis_path = os.path.join(directorio, f"analisis_{timestamp}.pdf")
        doc = SimpleDocTemplate(analisis_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        titulo = Paragraph("Análisis de Reunión vs Acta", styles['Title'])
        story.append(titulo)
        story.append(Spacer(1, 12))
        
        fecha = Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal'])
        story.append(fecha)
        story.append(Spacer(1, 20))
        
        texto_analisis = salida_analisis.get("1.0", tk.END).strip()
        for linea in texto_analisis.split("\n"):
            if linea.strip():
                p = Paragraph(linea.replace('<', '&lt;').replace('>', '&gt;'), styles['Normal'])
                story.append(p)
                story.append(Spacer(1, 6))
        
        doc.build(story)
        
        messagebox.showinfo(
            "✓ Guardado exitoso", 
            f"Se guardaron 3 archivos en:\n{directorio}\n\n"
            f"• transcripcion_{timestamp}.txt\n"
            f"• pdf_extraido_{timestamp}.txt\n"
            f"• analisis_{timestamp}.pdf"
        )
    except Exception as e:
        messagebox.showerror("Error", f"Error al guardar archivos:\n{e}")

def limpiar_cache():
    """Elimina el archivo de caché de transcripciones"""
    try:
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
            messagebox.showinfo("Caché limpiado", "Se eliminó el caché de transcripciones.")
        else:
            messagebox.showinfo("Caché limpiado", "No había caché para eliminar.")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo limpiar el caché:\n{e}")

# ---------- Interfaz gráfica ----------
ventana = tk.Tk()
ventana.title("Comparador Reunión vs Acta con IA")
ventana.geometry("1200x850")
ventana.configure(bg="#bbe6fa")

# Barra superior
frame_superior = tk.Frame(ventana, bg="#bbe6fa")
frame_superior.pack(pady=15, fill="x")

# Botón y label audio
frame_audio_top = tk.Frame(frame_superior, bg="#bbe6fa")
frame_audio_top.pack(side="left", padx=20)
btn_audio = tk.Button(frame_audio_top, text="📁 Cargar Audio", command=cargar_audio,
                      bg="#6de1e9", fg="black", font=("Arial", 12, "bold"), padx=20, pady=10)
btn_audio.pack()
lbl_audio = tk.Label(frame_audio_top, text="No se ha cargado audio", bg="#bbe6fa", fg="black",
                     wraplength=250, justify="center", anchor="center", font=("Arial", 9))
lbl_audio.pack(pady=5, fill="x")

# Botón y label PDF
frame_pdf_top = tk.Frame(frame_superior, bg="#bbe6fa")
frame_pdf_top.pack(side="left", padx=20)
btn_pdf = tk.Button(frame_pdf_top, text="📁 Cargar PDF", command=cargar_pdf,
                    bg="#6de1e9", fg="black", font=("Arial", 12, "bold"), padx=20, pady=10)
btn_pdf.pack()
lbl_pdf = tk.Label(frame_pdf_top, text="No se ha cargado PDF", bg="#bbe6fa", fg="black",
                   wraplength=250, justify="center", anchor="center", font=("Arial", 9))
lbl_pdf.pack(pady=5, fill="x")

# Selector de modelo Whisper
frame_modelo = tk.Frame(frame_superior, bg="#bbe6fa")
frame_modelo.pack(side="left", padx=20)
tk.Label(frame_modelo, text="Modelo Whisper:", bg="#bbe6fa", font=("Arial", 10)).pack()
modelo_var = tk.StringVar(value="small")
modelo_dropdown = tk.OptionMenu(frame_modelo, modelo_var, "tiny", "base", "small", "medium")
modelo_dropdown.config(bg="#6de1e9", font=("Arial", 9))
modelo_dropdown.pack()

# Botón comparar
btn_comparar = tk.Button(frame_superior, text="🔍 Comparar", command=comparar,
                         bg="#6de1e9", fg="black", font=("Arial", 14, "bold"), padx=30, pady=12)
btn_comparar.pack(side="left", padx=15)

# Botones de guardado
frame_botones_guardar = tk.Frame(frame_superior, bg="#bbe6fa")
frame_botones_guardar.pack(side="right", padx=10)

btn_guardar_informe = tk.Button(frame_botones_guardar, text="💾 Guardar Informe", 
                                command=guardar_informe,
                                bg="#6de1e9", fg="black", font=("Arial", 10, "bold"),
                                padx=15, pady=8, state="disabled")
btn_guardar_informe.pack(side="top", pady=2)

btn_guardar_todo = tk.Button(frame_botones_guardar, text="📦 Guardar Todo", 
                            command=guardar_todo,
                            bg="#6de1e9", fg="black", font=("Arial", 10, "bold"),
                            padx=15, pady=8, state="disabled")
btn_guardar_todo.pack(side="top", pady=2)

btn_limpiar_cache = tk.Button(frame_botones_guardar, text="🗑️ Limpiar Caché", 
                              command=limpiar_cache,
                              bg="#ffb366", fg="black", font=("Arial", 9),
                              padx=10, pady=5)
btn_limpiar_cache.pack(side="top", pady=2)

# Zona central (transcripción y PDF)
frame_textos = tk.Frame(ventana, bg="#bbe6fa")
frame_textos.pack(fill="both", expand=True, padx=15, pady=10)

# Transcripción (refinada con IA)
frame_left = tk.Frame(frame_textos, bg="#bbe6fa")
frame_left.pack(side="left", fill="both", expand=True, padx=8)
tk.Label(frame_left, text="🎤 Transcripción del audio (refinada con IA)", 
         bg="#bbe6fa", font=("Arial", 12, "bold")).pack()
salida_audio = scrolledtext.ScrolledText(frame_left, wrap="word", font=("Arial", 10))
salida_audio.pack(fill="both", expand=True)

# PDF
frame_right = tk.Frame(frame_textos, bg="#bbe6fa")
frame_right.pack(side="left", fill="both", expand=True, padx=8)
tk.Label(frame_right, text="📄 Contenido del PDF", 
         bg="#bbe6fa", font=("Arial", 12, "bold")).pack()
salida_pdf = scrolledtext.ScrolledText(frame_right, wrap="word", font=("Arial", 10))
salida_pdf.pack(fill="both", expand=True)

# Análisis IA abajo
frame_bottom = tk.Frame(ventana, bg="#bbe6fa")
frame_bottom.pack(fill="both", expand=True, padx=15, pady=10)
tk.Label(frame_bottom, text="🧠 Análisis IA (Mistral vía Ollama)", 
         bg="#bbe6fa", font=("Arial", 12, "bold")).pack()

salida_analisis = scrolledtext.ScrolledText(frame_bottom, wrap="word", font=("Arial", 10), height=15)
salida_analisis.pack(fill="both", expand=True, pady=(0,10))

# Info footer
footer = tk.Label(ventana, 
                 text="💡 Tip: El caché guarda transcripciones previas para ahorrar tiempo. Límpialo si modificas archivos.",
                 bg="#bbe6fa", fg="#333", font=("Arial", 8), wraplength=1100)
footer.pack(pady=5)

ventana.mainloop()
