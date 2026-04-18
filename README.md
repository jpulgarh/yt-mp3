# Claudia – Asistente IA Local con Voz

Sistema de asistente de voz que corre **completamente en tu equipo**, sin suscripciones ni APIs de pago. Usa [Ollama](https://ollama.com) como motor de lenguaje, [faster-whisper](https://github.com/SYSTRAN/faster-whisper) para reconocer tu voz y [edge-tts](https://github.com/rany2/edge-tts) para responderte en español con voz natural.

Dile **"Hey Claudia"** y convérsale: pídele música, que te explique temas, que descargue listas de YouTube, que te diga el estado de tu sistema o que practiques inglés con ella.

---

## Tabla de contenidos

1. [Requisitos](#1-requisitos)
2. [Instalación](#2-instalación)
3. [Configuración](#3-configuración)
4. [Uso](#4-uso)
5. [Módulos incluidos](#5-módulos-incluidos)
6. [Privacidad y seguridad](#6-privacidad-y-seguridad)
7. [Cómo crear un módulo nuevo](#7-cómo-crear-un-módulo-nuevo)
8. [Solución de problemas](#8-solución-de-problemas)
9. [Arquitectura del proyecto](#9-arquitectura-del-proyecto)

---

## 1. Requisitos

### Sistema operativo
- Ubuntu 20.04 / 22.04 / 24.04
- Debian 11 (Bullseye) / 12 (Bookworm)

### Hardware mínimo recomendado
| Componente | Mínimo | Recomendado |
|---|---|---|
| CPU | 4 núcleos | 8+ núcleos |
| RAM | 8 GB | 16 GB |
| Disco | 10 GB libres | 20 GB libres |
| Micrófono | Cualquier micrófono USB o integrado | — |

> **GPU Nvidia:** Si tienes una GPU Nvidia, Ollama la usará automáticamente para respuestas mucho más rápidas. No es obligatorio.

### Software base
- Python 3.10 o superior
- [Ollama](https://ollama.com) instalado y con al menos un modelo descargado
- `ffmpeg`, `mpg123` y las librerías de audio de PortAudio

---

## 2. Instalación

### Paso 1 — Dependencias del sistema

```bash
sudo apt update
sudo apt install -y ffmpeg mpg123 portaudio19-dev python3-dev python3-pip libffi-dev
```

### Paso 2 — Instalar Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Verifica que Ollama esté corriendo:

```bash
ollama serve          # déjalo corriendo en otra terminal, o como servicio del sistema
```

Descarga el modelo por defecto (gemma3:4b, ~3 GB):

```bash
ollama pull gemma3:4b
```

Otros modelos compatibles que puedes usar en su lugar:

```bash
ollama pull llama3.2       # Meta Llama 3.2 (3B)
ollama pull mistral        # Mistral 7B
ollama pull qwen2.5:3b     # Qwen 2.5 (ligero)
ollama pull phi4-mini      # Microsoft Phi-4 Mini
```

### Paso 3 — Clonar el repositorio

```bash
git clone https://github.com/jpulgarh/yt-mp3.git
cd yt-mp3
```

### Paso 4 — Entorno virtual Python (recomendado)

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Paso 5 — Instalar dependencias Python

```bash
pip install -r requirements.txt
```

> La primera vez que ejecutes el sistema, `faster-whisper` descargará automáticamente el modelo de reconocimiento de voz configurado (~150 MB para el modelo `base`). Esto solo ocurre una vez.

### Paso 6 — Crear la carpeta de música

```bash
sudo mkdir -p /media/musica
sudo chown $USER:$USER /media/musica
```

O edita `config.yaml` para apuntar a otra ruta que prefieras.

### Paso 7 — Lanzar Claudia

```bash
python main.py
```

---

## 3. Configuración

Todo el comportamiento del sistema se controla desde el archivo **`config.yaml`** en la raíz del proyecto. Puedes editarlo directamente con cualquier editor de texto, o usar el **menú de configuración interactivo** dentro de la aplicación (tecla `C`).

### Opciones principales

```yaml
system:
  wake_word: "hey claudia"    # Frase que activa la escucha
  language: "es"              # es = Español, en = Inglés
  listen_timeout: 12          # Segundos máximos de escucha tras activación
  active: true                # Micrófono activo al arrancar

llm:
  host: "http://localhost:11434"   # Ollama en este equipo
  # host: "http://192.168.1.50:11434"  # Ollama en otro equipo de la red
  model: "gemma3:4b"          # Modelo a usar
  temperature: 0.7            # Creatividad: 0.0 (exacto) → 1.0 (creativo)

tts:
  provider: "edge-tts"        # edge-tts (online) o pyttsx3 (offline)
  voice: "es-ES-ElviraNeural" # Voz para español de España
  rate: "+0%"                 # Velocidad: -20% más lento, +20% más rápido

stt:
  model: "base"               # Modelo Whisper: tiny | base | small | medium | large
  language: "es"

paths:
  music_dir: "/media/musica/" # Aquí se guardan las canciones descargadas
```

### Voces disponibles para edge-tts en español

| Código | Variante | Género |
|---|---|---|
| `es-ES-ElviraNeural` | España | Femenino |
| `es-ES-AlvaroNeural` | España | Masculino |
| `es-MX-DaliaNeural` | México | Femenino |
| `es-MX-JorgeNeural` | México | Masculino |
| `es-AR-ElenaNeural` | Argentina | Femenino |
| `es-CL-CatalinaNeural` | Chile | Femenino |

Para listar todas las voces disponibles:

```bash
python -c "import asyncio, edge_tts; asyncio.run(edge_tts.list_voices())" | grep -i spanish
```

### Usar Ollama en un servidor separado

Si tienes Ollama instalado en otro equipo de tu red local, solo cambia `llm.host`:

```yaml
llm:
  host: "http://192.168.1.50:11434"
  model: "gemma3:4b"
```

### Modo 100% offline (sin internet)

Cambia el proveedor de TTS a `pyttsx3` (calidad de voz más básica):

```yaml
tts:
  provider: "pyttsx3"
```

Instala el soporte de español para espeak:

```bash
sudo apt install espeak-ng espeak-ng-data
```

---

## 4. Uso

### Iniciar el sistema

```bash
python main.py
```

Verás una pantalla como esta:

```
╔═══════════════════════════════════════════════════════════════════╗
║         CLAUDIA – Asistente IA Local  |  Modelo: gemma3:4b       ║
╠═══════════════════════════════════════════════════════════════════╣
║  ● ACTIVO  │ Esperando 'hey claudia'...                           ║
║  Música: /media/musica/                                           ║
╠═══════════════════════════════════════════════════════════════════╣
║  ACTIVIDAD RECIENTE                                               ║
║  10:23:01  [sistema] Modelos cargados correctamente.              ║
║  10:23:05  [sistema] Escuchando 'hey claudia'...                  ║
╠═══════════════════════════════════════════════════════════════════╣
║  CPU  12.3%  RAM  45.1%  Disco 120.4GB libres                    ║
╠═══════════════════════════════════════════════════════════════════╣
║  [ESPACIO] Activar/Desactivar  [C] Configuración  [Q] Salir      ║
╚═══════════════════════════════════════════════════════════════════╝
```

### Controles del teclado

| Tecla | Acción |
|---|---|
| `ESPACIO` | Activar o desactivar el micrófono |
| `C` | Abrir menú de configuración |
| `Q` o `ESC` | Salir del programa |

En el menú de configuración, además:

| Tecla | Acción |
|---|---|
| `↑` / `↓` | Navegar entre opciones |
| `ENTER` | Editar el campo seleccionado |
| `ESC` | Volver a la pantalla principal |

### Cómo hablar con Claudia

1. Di **"Hey Claudia"** — escucharás un pitido corto que confirma que te está escuchando.
2. Habla tu comando con naturalidad, a ritmo normal.
3. Claudia procesa lo que dijiste y te responde en voz alta.

Puedes decir el comando **inmediatamente después de la frase de activación** o hacer una pausa breve:

```
"Hey Claudia, ¿cómo está mi CPU?"
"Hey Claudia, enséñame sobre la guerra del Pacífico"
"Hey Claudia, reproduce mis listas de música"
```

### Ejemplos de comandos por módulo

#### Conversación general
```
"Hey Claudia, ¿cuánto es el 30% de 2500?"
"Hey Claudia, dame una receta rápida con pollo y arroz"
"Hey Claudia, cuéntame un chiste"
```

#### Música local
```
"Hey Claudia, reproduce toda la música"
"Hey Claudia, pon la lista de rock"
"Hey Claudia, ¿qué listas tengo disponibles?"
"Hey Claudia, detén la música"
```

#### Descargar listas de YouTube
```
"Hey Claudia, descarga esta lista: https://youtube.com/playlist?list=PLxxxxx"
```
La descarga ocurre en segundo plano. Claudia te avisará cuando termine.

#### Estado del sistema
```
"Hey Claudia, ¿cómo está mi sistema?"
"Hey Claudia, ¿cuánta memoria RAM me queda?"
"Hey Claudia, ¿qué temperatura tiene el procesador?"
```

#### Modo profesor
```
"Hey Claudia, enséñame sobre la fotosíntesis"
"Hey Claudia, explícame la guerra del Pacífico"
"Hey Claudia, ¿qué es la inteligencia artificial?"
"Hey Claudia, cuéntame más sobre ese tema"  ← continúa la explicación anterior
```

#### Práctica de inglés
```
"Hey Claudia, quiero practicar inglés"
"Hey Claudia, let's talk about my hobbies"
"Hey Claudia, termina la sesión de inglés"
```

### Descargar listas de YouTube desde la línea de comandos

El descargador también funciona de manera independiente, sin necesidad de hablar:

```bash
# Uso básico
python downloader.py "https://www.youtube.com/playlist?list=PLxxxxx"

# Con carpeta de destino personalizada
python downloader.py "https://www.youtube.com/playlist?list=PLxxxxx" -o /media/musica

# CBR 320 kbps en lugar de VBR best
python downloader.py "https://www.youtube.com/playlist?list=PLxxxxx" --cbr

# Limitar descargas simultáneas (por defecto 4)
python downloader.py "https://www.youtube.com/playlist?list=PLxxxxx" -w 2
```

---

## 5. Módulos incluidos

| Módulo | Nombre interno | Descripción |
|---|---|---|
| Conversación general | `general` | Responde cualquier pregunta o conversación libre |
| Descargar YouTube | `youtube_downloader` | Descarga playlists de YouTube como MP3 |
| Reproductor de música | `music_player` | Reproduce los MP3 descargados con tu reproductor favorito |
| Monitor del sistema | `system_monitor` | Reporta CPU, RAM, temperatura, GPU y disco |
| Tutor de inglés | `english_tutor` | Práctica conversacional de inglés con correcciones |
| Profesor | `teacher` | Explica cualquier tema de forma didáctica |

Para activar o desactivar un módulo, edita `config.yaml`:

```yaml
modules:
  youtube_downloader: true
  music_player: true
  system_monitor: true
  english_tutor: false   # ← desactivado
  teacher: true
```

---

## 6. Privacidad y seguridad

### Lo que Claudia NO hace

- **No guarda conversaciones** en ningún archivo del disco.
- **No guarda grabaciones de audio** — el audio se procesa en RAM y se descarta.
- **No envía audio** a ningún servicio externo.
- **No envía datos de tu sistema** a servidores externos.
- **No crea scripts ni programas** a través del sistema de voz.
- **No accede a contraseñas**, llaves SSH, archivos del sistema operativo ni datos del navegador.
- **No modifica ni elimina** archivos fuera de la carpeta de música configurada.

### Lo que sí hace (y debes saber)

| Componente | Dónde procesa |
|---|---|
| Reconocimiento de voz (STT) | 100% local con faster-whisper |
| Inteligencia artificial (LLM) | 100% local con Ollama |
| Síntesis de voz `edge-tts` | Envía el **texto** a Microsoft para generar audio. No envía audio ni datos personales. |
| Síntesis de voz `pyttsx3` | 100% local (alternativa offline) |

> Si necesitas privacidad total de texto también, usa `tts.provider: pyttsx3` en `config.yaml`.

---

## 7. Cómo crear un módulo nuevo

Claudia está diseñada para crecer. Agregar un módulo nuevo requiere **3 pasos** y no es necesario modificar el núcleo del sistema.

### Paso 1 — Crear el archivo del módulo

Crea el archivo `claudia/modules/mi_modulo.py` heredando de `BaseModule`:

```python
# claudia/modules/mi_modulo.py

from .base import BaseModule
from ..core.brain import ask          # LLM local
from ..core.config import load as load_config  # acceso a config.yaml


class MiModulo(BaseModule):
    # Nombre único (debe coincidir con la clave en config.yaml > modules)
    name = "mi_modulo"
    description = "Descripción breve de lo que hace este módulo"

    def execute(self, action: str, params: dict) -> str:
        """
        Recibe la acción y parámetros clasificados por el router.
        Debe retornar un string con el texto de la respuesta.
        Ese texto será leído en voz alta por el sistema TTS.
        """
        if action == "hacer_algo":
            dato = params.get("dato", "")
            return f"Hice algo con: {dato}"

        if action == "consultar":
            tema = params.get("tema", "")
            respuesta = ask(
                f"Dame información sobre: {tema}",
                system_prompt="Eres un experto. Responde en español, sin markdown.",
            )
            return respuesta

        return "No reconocí ese comando."
```

**Contrato del método `execute`:**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `action` | `str` | La acción a ejecutar (la define el router según el comando hablado) |
| `params` | `dict` | Parámetros extraídos del comando (pueden estar vacíos) |
| Retorno | `str` | Texto que será leído en voz alta. Sin markdown ni viñetas. |

### Paso 2 — Registrar el módulo

Edita `claudia/modules/__init__.py` y agrega tu módulo:

```python
# claudia/modules/__init__.py

from .youtube_downloader import YouTubeDownloaderModule
from .music_player import MusicPlayerModule
from .system_monitor import SystemMonitorModule
from .english_tutor import EnglishTutorModule
from .teacher import TeacherModule
from .mi_modulo import MiModulo          # ← importar

ALL_MODULES = [
    YouTubeDownloaderModule(),
    MusicPlayerModule(),
    SystemMonitorModule(),
    EnglishTutorModule(),
    TeacherModule(),
    MiModulo(),                          # ← registrar
]

MODULE_MAP: dict = {m.name: m for m in ALL_MODULES}
```

### Paso 3 — Habilitar en la configuración

Agrega una línea en `config.yaml` bajo `modules:`:

```yaml
modules:
  youtube_downloader: true
  music_player: true
  system_monitor: true
  english_tutor: true
  teacher: true
  mi_modulo: true         # ← agregar
```

### Paso 4 — Enseñarle al router (opcional pero recomendado)

El router usa el LLM para clasificar el comando de voz en un módulo y acción. Para mejores resultados, agrega ejemplos representativos al prompt en `claudia/core/router.py`, dentro de la constante `_ROUTING_PROMPT`:

```python
# En claudia/core/router.py, dentro de _ROUTING_PROMPT:
"""
...
  mi_modulo:
    - hacer_algo {dato: str}    -> ejecuta algo con un dato
    - consultar {tema: str}     -> consulta información sobre un tema
...

"hazme algo con 'temperatura'" -> {"module":"mi_modulo","action":"hacer_algo","params":{"dato":"temperatura"}}
"consulta sobre astronomía" -> {"module":"mi_modulo","action":"consultar","params":{"tema":"astronomía"}}
"""
```

### Ejemplo completo: módulo de clima

```python
# claudia/modules/weather.py

import urllib.request
import json
from .base import BaseModule
from ..core.config import load as load_config


class WeatherModule(BaseModule):
    name = "weather"
    description = "Consulta el clima actual de cualquier ciudad usando wttr.in (sin API key)"

    def execute(self, action: str, params: dict) -> str:
        city = params.get("city", "Santiago")
        city_enc = urllib.parse.quote(city)

        try:
            url = f"https://wttr.in/{city_enc}?format=j1"
            with urllib.request.urlopen(url, timeout=5) as r:
                data = json.loads(r.read())

            current = data["current_condition"][0]
            temp_c = current["temp_C"]
            feels = current["FeelsLikeC"]
            desc = current["weatherDesc"][0]["value"]

            return (
                f"En {city} hay {temp_c} grados centígrados, "
                f"se siente como {feels}. {desc}."
            )
        except Exception:
            return f"No pude obtener el clima de {city} en este momento."
```

---

## 8. Solución de problemas

### El micrófono no funciona

```bash
# Verificar que Python detecta el micrófono
python -c "import sounddevice; print(sounddevice.query_devices())"

# Listar dispositivos de audio del sistema
arecord -l

# Probar grabación de 3 segundos
arecord -d 3 -f cd /tmp/test.wav && aplay /tmp/test.wav
```

Si tienes múltiples micrófonos, identifica el índice del dispositivo correcto y agrégalo en `config.yaml`:

```yaml
audio:
  input_device: 2    # índice del dispositivo (ver salida de sounddevice.query_devices())
```

### Ollama no responde

```bash
# Verificar que Ollama está corriendo
curl http://localhost:11434/api/tags

# Iniciar Ollama manualmente
ollama serve

# Verificar que el modelo está descargado
ollama list
```

### webrtcvad falla al instalar

```bash
sudo apt install python3-dev libffi-dev
pip install webrtcvad
```

En algunos sistemas Debian puede requerir también:

```bash
sudo apt install build-essential
```

### El habla no se reconoce bien

- Usa un modelo STT más preciso: cambia `stt.model` a `small` o `medium` en `config.yaml`.
- Ajusta la sensibilidad del detector de voz: `audio.vad_aggressiveness: 1` (más permisivo) o `3` (más estricto).
- Habla más cerca del micrófono en un ambiente sin mucho ruido de fondo.
- Verifica que `stt.language: "es"` esté configurado correctamente.

### edge-tts no habla

Verifica que tienes conexión a internet (edge-tts la requiere). Si prefieres modo offline:

```yaml
tts:
  provider: "pyttsx3"
```

```bash
pip install pyttsx3
sudo apt install espeak-ng espeak-ng-data
```

### La GPU no es detectada para Ollama

```bash
# Verificar que Ollama detecta la GPU
ollama run gemma3:4b "hola"   # debería aparecer uso de GPU en nvidia-smi
nvidia-smi
```

Si tienes GPU AMD, Ollama usa ROCm automáticamente en Linux si está instalado.

---

## 9. Arquitectura del proyecto

```
yt-mp3/
│
├── main.py                    # Punto de entrada. Interfaz TUI (curses).
├── downloader.py              # Descargador standalone de playlists YouTube.
├── config.yaml                # Configuración global editable.
├── requirements.txt           # Dependencias Python.
│
└── claudia/                   # Paquete principal del asistente.
    │
    ├── core/                  # Núcleo del sistema (no modificar para agregar funciones).
    │   ├── config.py          # Leer y escribir config.yaml.
    │   ├── brain.py           # Cliente Ollama – toda la inteligencia pasa por aquí.
    │   ├── voice.py           # TTS: edge-tts o pyttsx3. Beep de activación.
    │   ├── listener.py        # STT: faster-whisper. Graba y transcribe comandos.
    │   ├── wake_word.py       # Bucle de escucha continua para "Hey Claudia".
    │   └── router.py          # Clasifica el comando en módulo + acción + parámetros.
    │
    └── modules/               # Módulos funcionales. Aquí se agregan nuevas funciones.
        ├── base.py            # Clase base BaseModule (contrato de todos los módulos).
        ├── __init__.py        # Registro de módulos activos.
        ├── youtube_downloader.py
        ├── music_player.py
        ├── system_monitor.py
        ├── english_tutor.py
        └── teacher.py
```

### Flujo de una conversación

```
Micrófono
   │
   ▼
wake_word.py ──── ¿Contiene "hey claudia"? ──── No ──── (descarta, sigue escuchando)
   │ Sí
   ▼
listener.py ──── Graba hasta silencio ──── Transcribe con faster-whisper
   │
   ▼
router.py ──── Clasifica intención con el LLM local ──── {"module":"...", "action":"...", "params":{}}
   │
   ▼
modules/<modulo>.py ──── execute(action, params) ──── retorna texto
   │
   ▼
voice.py ──── edge-tts o pyttsx3 ──── audio reproducido por el altavoz
```

---

## Licencia

MIT — libre para uso personal y modificación.
