# yt-mp3 — YouTube Playlist MP3 Downloader

Script en Python para descargar playlists, Radio/Mix y videos sueltos de YouTube como **archivos MP3** de alta calidad, con metadatos (título, artista, carátula) y soporte de reanudación.

---

## Tabla de contenidos

1. [Características](#1-características)
2. [Requisitos](#2-requisitos)
3. [Instalación](#3-instalación)
4. [Uso](#4-uso)
5. [Opciones](#5-opciones)
6. [Notas sobre Radio/Mix (listas `RD...`)](#6-notas-sobre-radiomix-listas-rd)
7. [Solución de problemas](#7-solución-de-problemas)

---

## 1. Características

- Descarga playlists completas (`PL...`), Radio/Mix (`RD...`) y videos individuales.
- MP3 en **VBR best** (~245 kbps) por defecto, opcional **CBR 320 kbps**.
- Metadatos ID3 embebidos y **carátula** del video como arte de álbum.
- Descargas en paralelo configurables.
- **Reanudación automática**: si una canción ya existe, la salta.
- Deduplicación de entradas repetidas en los mixes.
- Límite configurable para Radio/Mix (YouTube los genera infinitamente).

---

## 2. Requisitos

- Python 3.10 o superior
- `ffmpeg` disponible en el `PATH`

### Instalar dependencias del sistema

Debian / Ubuntu:

```bash
sudo apt update
sudo apt install -y ffmpeg python3-pip
```

macOS (Homebrew):

```bash
brew install ffmpeg
```

---

## 3. Instalación

```bash
git clone https://github.com/jpulgarh/yt-mp3.git
cd yt-mp3
```

Entorno virtual (recomendado):

```bash
python3 -m venv venv
source venv/bin/activate
```

Instalar dependencias Python:

```bash
pip install -r requirements.txt
```

---

## 4. Uso

```bash
python downloader.py <url> [opciones]
```

### Ejemplos

Playlist normal:

```bash
python downloader.py "https://www.youtube.com/playlist?list=PLxxxxx"
```

Radio/Mix con límite de 25 canciones:

```bash
python downloader.py "https://www.youtube.com/watch?v=VIDEO_ID&list=RDxxx" --mix-limit 25
```

Guardar en una carpeta específica con CBR 320 kbps:

```bash
python downloader.py "https://www.youtube.com/playlist?list=PLxxxxx" -o ~/Music --cbr
```

Limitar a 2 descargas simultáneas:

```bash
python downloader.py "https://www.youtube.com/playlist?list=PLxxxxx" -w 2
```

Cada playlist se guarda en su propia subcarpeta con el nombre sanitizado de la lista. Los archivos siguen el formato `NNN - Título.mp3`.

---

## 5. Opciones

| Flag | Descripción | Default |
|---|---|---|
| `url` | URL de la playlist, mix o video de YouTube | *(requerido)* |
| `-w`, `--workers N` | Descargas simultáneas | `4` |
| `-o`, `--output DIR` | Carpeta de destino | directorio actual |
| `--cbr` | Usar CBR 320 kbps en lugar de VBR best | VBR |
| `--mix-limit N` | Límite de canciones para Radio/Mix | `50` |

---

## 6. Notas sobre Radio/Mix (listas `RD...`)

YouTube genera los mixes (`RD`, `RDEM`, `RDMIX`, `RDCLAK`, etc.) de forma **infinita** a partir de un video semilla. Por eso:

- Debes incluir el parámetro `v=` original en la URL para que YouTube pueda resolver el mix.
- El script aplica automáticamente un límite (`--mix-limit`, por defecto 50) para que la descarga no crezca sin parar.
- Si el pre-fetch de la lista no devuelve entradas, el script cae a una descarga directa con el mismo límite.

---

## 7. Solución de problemas

### `ffmpeg not found`

Instala `ffmpeg` y asegúrate de que esté en el `PATH`:

```bash
which ffmpeg   # debe devolver una ruta
```

### `ERROR: Sign in to confirm you're not a bot`

YouTube marcó tu IP. Actualiza `yt-dlp` a la última versión:

```bash
pip install -U yt-dlp
```

### La carátula no se embebe

`mutagen` es requerido para MP3. Si lo instalaste antes pero sigue fallando, reinstálalo:

```bash
pip install --upgrade --force-reinstall mutagen
```

### La lista aparece vacía o privada

- Verifica que la URL es accesible desde una ventana en incógnito (sin sesión).
- Los videos privados o borrados no se pueden descargar.
- Si es un mix y trae `v=...&list=RD...`, no elimines el parámetro `v=`.

---

## Licencia

MIT — libre para uso personal y modificación.
