# 🎙️ Lector de Actas con IA

> Herramienta que compara automáticamente la transcripción de una reunión con su acta oficial usando inteligencia artificial, detectando omisiones, discrepancias y evaluando la fidelidad del documento.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Whisper](https://img.shields.io/badge/Whisper-OpenAI-orange.svg)
![Ollama](https://img.shields.io/badge/Ollama-Mistral-purple.svg)

---

## 📋 ¿Qué hace esta herramienta?

En muchas organizaciones, las actas de reuniones son documentos críticos, pero ¿qué tan fieles son a lo que realmente se dijo? Este proyecto usa IA para:

1. **Transcribir** el audio de la reunión usando Whisper de OpenAI
2. **Refinar** la transcripción con Mistral vía Ollama para mejorar coherencia
3. **Extraer** el texto del PDF del acta oficial
4. **Comparar semánticamente** ambos textos (no palabra por palabra, sino por significado)
5. **Generar un informe** detallando coincidencias, omisiones, excesos y discrepancias

### 🎯 Características principales

- ✅ **Análisis semántico inteligente**: No compara palabras literales, sino ideas y significados
- ⚡ **Sistema de caché**: Guarda transcripciones previas para evitar reprocesar
- 🎨 **Interfaz gráfica amigable**: No necesitas usar la terminal
- 💾 **Múltiples formatos de exportación**: PDF, TXT, Markdown
- 🔍 **4 modelos de Whisper**: Elige entre tiny, base, small o medium según precisión/velocidad
- 📊 **Informe completo**: Resumen, coincidencias, omisiones, excesos, discrepancias y % de fidelidad

---

## 🛠️ Requisitos previos

### 1. Python 3.8 o superior
```bash
python --version
```

### 2. FFmpeg (necesario para Whisper)

**Windows:**
- Descarga desde [ffmpeg.org](https://ffmpeg.org/download.html)
- Añade a PATH del sistema

**Linux:**
```bash
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

### 3. Ollama con modelo Mistral

**Instalar Ollama:**
- Descarga desde [ollama.ai](https://ollama.ai)
- O en Linux:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Descargar modelo Mistral:**
```bash
ollama pull mistral
```

**Verificar que funciona:**
```bash
ollama list
# Deberías ver "mistral" en la lista
```

---

## 📦 Instalación

### 1. Clona el repositorio
```bash
git clone https://github.com/TU_USUARIO/lector-actas.git
cd lector-actas
```

### 2. Instala las dependencias de Python
```bash
pip install openai-whisper pdfplumber ollama reportlab
```

**Nota:** La primera vez que ejecutes el programa, Whisper descargará automáticamente el modelo seleccionado (~500MB para "small"). Esto solo ocurre una vez.

### 3. Ejecuta el programa
```bash
python lector_actas.py
```

---

## 🚀 Uso

### Paso 1: Cargar archivos
1. Haz clic en **"Cargar Audio"** y selecciona tu archivo (MP3, WAV, M4A, OGG, FLAC)
2. Haz clic en **"Cargar PDF"** y selecciona el acta oficial

### Paso 2: Configurar
- Selecciona el modelo de Whisper:
  - **tiny**: Muy rápido, menos preciso (~1GB RAM)
  - **base**: Rápido, precisión aceptable (~1GB RAM)
  - **small**: Equilibrado ⭐ *Recomendado* (~2GB RAM)
  - **medium**: Lento, muy preciso (~5GB RAM)

### Paso 3: Comparar
- Presiona **"Comparar"**
- Espera mientras el programa:
  1. Transcribe el audio (puede tardar varios minutos)
  2. Refina la transcripción con IA
  3. Extrae texto del PDF
  4. Analiza y compara ambos documentos

### Paso 4: Guardar resultados
- **"Guardar Informe"**: Solo el análisis (PDF, TXT o MD)
- **"Guardar Todo"**: Transcripción + PDF extraído + Análisis

---

## 📁 Estructura del proyecto

```
lector-actas/
├── lector_actas.py          # Código principal
├── README.md                # Este archivo
├── ejemplos/                # Archivos de prueba
│   ├── reunion_ejemplo.mp3  # Audio de ejemplo
│   └── acta_ejemplo.pdf     # PDF de ejemplo
├── cache_transcripciones.json  # Se crea automáticamente
└── requirements.txt         # Dependencias (opcional)
```

---

## 💡 Casos de uso reales

### 1. **Auditorías internas**
Empresas que necesitan verificar que las actas reflejen fielmente lo discutido en juntas directivas.

### 2. **Transparencia gubernamental**
Ayuntamientos o instituciones públicas que deben garantizar que las actas de plenos sean precisas.

### 3. **Investigación académica**
Estudios sobre fidelidad de documentación en procesos deliberativos.

### 4. **Legal/Compliance**
Verificación de que acuerdos verbales estén correctamente documentados.

### 5. **Gestión de proyectos**
Equipos que quieren asegurar que los "meeting minutes" capturen todas las decisiones.

---

## 🎬 Cómo funciona (Explicación técnica)

### 1. Transcripción con Whisper
```python
model = whisper.load_model("small")
resultado = model.transcribe(audio_path, language="es")
texto = resultado["text"]
```
Whisper convierte el audio a texto. Es un modelo de OpenAI entrenado en 680,000 horas de audio multilingüe.

### 2. Refinamiento con Mistral
```python
resp = ollama.chat(
    model="mistral",
    messages=[{
        "role": "user",
        "content": "Reescribe este texto para que sea coherente..."
    }]
)
```
Mistral corrige errores de transcripción y mejora la coherencia sin alterar el significado.

### 3. Extracción de PDF
```python
with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        texto += page.extract_text()
```
Extrae todo el texto del PDF, página por página.

### 4. Análisis semántico
El prompt a Mistral incluye instrucciones específicas:
- No comparar palabras literales, sino **ideas**
- "tengo un coche rojo" = "poseo un automóvil rojo" = **COINCIDENCIA**
- Solo marcar discrepancia si cambia el **significado** (fechas, cifras, responsables)

### 5. Sistema de caché
```python
file_hash = hashlib.md5(audio_file).hexdigest()
cache_key = f"{file_hash}_{modelo}"
```
Guarda transcripciones usando hash MD5 del archivo. Si vuelves a procesar el mismo audio, lo lee de caché en 1 segundo.

---

## ⚡ Ventajas

| Ventaja | Descripción |
|---------|-------------|
| 🤖 **Automatización completa** | De audio a informe en minutos, sin intervención manual |
| 🧠 **Análisis semántico** | Entiende significados, no solo palabras exactas |
| 💰 **100% local y gratuito** | No usa APIs de pago, todo corre en tu PC |
| ⚡ **Caché inteligente** | Evita reprocesar audios ya transcritos |
| 📊 **Informes detallados** | No solo dice "son diferentes", explica el qué y el cómo |
| 🎨 **Interfaz amigable** | No necesitas programar para usarlo |
| 🔒 **Privacidad total** | Tus datos nunca salen de tu equipo |

---

## ⚠️ Limitaciones y consideraciones

### Técnicas
- **Requiere hardware decente**: Mínimo 8GB RAM para modelo "small", 16GB para "medium"
- **Transcripción no instantánea**: Un audio de 10 min puede tardar 2-5 min en transcribirse
- **Ollama debe estar corriendo**: El programa lo verifica, pero hay que tenerlo activo
- **Precisión de Whisper**: En audios con mucho ruido o acentos fuertes puede haber errores
- **Idioma**: Optimizado para español, otros idiomas pueden requerir ajustes

### Conceptuales
- **No es evidencia legal**: El análisis es orientativo, no sustituye revisión humana
- **Interpretación de "equivalencia"**: La IA decide qué es semánticamente igual, puede ser subjetivo
- **Depende de calidad del audio**: Grabación mala = transcripción mala = análisis limitado
- **PDF debe tener texto**: No funciona con PDF escaneado sin OCR

---

## 🔧 Solución de problemas

### ❌ "Ollama no detectado"
**Solución:**
```bash
# Verifica que Ollama esté instalado
ollama --version

# Verifica que Mistral esté descargado
ollama list

# Si no está, descárgalo
ollama pull mistral

# En algunas instalaciones, debes iniciar el servicio manualmente
ollama serve
```

### ❌ "Error al transcribir con Whisper"
**Causas comunes:**
1. FFmpeg no está instalado → Instala FFmpeg
2. Formato de audio no soportado → Convierte a MP3 o WAV
3. Archivo corrupto → Prueba con otro audio

### ❌ "No se extrajo texto del PDF"
**Solución:**
- Si el PDF es una imagen escaneada, usa un OCR primero (Adobe, Google Drive, etc.)
- Algunos PDFs tienen protección, intenta removerla

### ❌ "El programa se queda colgado"
**Posibles causas:**
- Audio muy largo (>1 hora) → Usa modelo "tiny" o divide el audio
- Poca RAM → Cierra otros programas
- Modelo "medium" en PC débil → Usa "small" o "base"

### 🧹 Limpiar caché
Si las transcripciones parecen incorrectas o antiguas:
```python
# Desde la interfaz: botón "Limpiar Caché"
# O manualmente: elimina cache_transcripciones.json
```

---

## 🔮 Mejoras futuras

- [ ] Soporte para múltiples idiomas configurables
- [ ] Integración con Google Drive para cargar archivos
- [ ] Exportar a Word (.docx) además de PDF
- [ ] Modo batch para procesar múltiples archivos
- [ ] API REST para integrar con otros sistemas
- [ ] Detección automática de idioma del audio
- [ ] Resaltado de diferencias en interfaz visual
- [ ] Soporte para otros LLMs locales (Llama, Phi, etc.)

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Si quieres mejorar este proyecto:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request


---

## 🙏 Agradecimientos

- **OpenAI Whisper**: Por el increíble modelo de transcripción
- **Mistral AI**: Por el modelo de lenguaje de código abierto
- **Ollama**: Por hacer tan fácil ejecutar LLMs localmente
- **Comunidad Python**: Por las excelentes librerías

---

## 📧 Contacto

¿Preguntas, sugerencias o bugs? Abre un issue en GitHub o contáctame en jorgegongon@gmail.com.

---

**⭐ Si este proyecto te fue útil, dale una estrella en GitHub!**
