# Google Maps Prospect Scraper

Herramienta gratuita para recopilar negocios potenciales y crear listas de prospección.

Busca negocios públicos en Google Maps por giro y ubicación, recopila nombre, dirección,
teléfono, sitio web, calificación y número de reseñas, y entrega los resultados en Excel.
También crea una lista separada de negocios con un perfil razonable que no muestran sitio
web. No envía mensajes, no valida WhatsApp, no compra datos y no automatiza campañas.

## Descarga rápida

Descarga la versión preparada para Windows desde:

https://github.com/ramonsegh/google-maps-prospect-scraper/releases/latest

Después:

1. Extrae completamente el ZIP.
2. Ejecuta `INSTALAR_WINDOWS.bat`.
3. Al terminar, abre `EJECUTAR_SCRAPER.bat`.

## Requisitos

- Python 3.10 o superior
- Google Chrome actualizado
- Conexión a Internet

## Instalación

### Instalación automática en Windows

1. Descarga y extrae el ZIP del proyecto.
2. Haz doble clic en `INSTALAR_WINDOWS.bat`.
3. Acepta los avisos de instalación.
4. Cuando termine, abre `EJECUTAR_SCRAPER.bat`.

El instalador utiliza `winget` para preparar Python 3.13, Google Chrome y Visual Studio Code
cuando no estén instalados. Después crea `.venv` e instala las dependencias de Python.

### Instalación manual

```bash
git clone https://github.com/ramonsegh/google-maps-prospect-scraper.git
cd google-maps-prospect-scraper
python -m venv .venv
```

En Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

En Linux y macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

El archivo `.env` no contiene ninguna clave obligatoria por ahora. En Windows también
puedes duplicar `.env.example` manualmente y renombrar la copia como `.env`.

## Uso

```bash
python scraper_google_maps.py --giro "dentistas" --ubicacion "Monterrey, Nuevo León" --max 20
```

Puedes repetir `--giro` y `--ubicacion` para combinar varias búsquedas. Agrega
`--headless` si quieres ejecutar Chrome sin una ventana visible.

El scraper conserva `results/maps_urls_procesadas.csv`. Al repetir exactamente la misma
búsqueda, omite los negocios ya procesados y trabaja únicamente con los nuevos que Google
Maps muestre. Si la plataforma vuelve a entregar la misma lista, divide la ciudad en zonas:

```powershell
python scraper_google_maps.py --giro "dentistas" `
  --ubicacion "Polanco, Ciudad de México" `
  --ubicacion "Roma Norte, Ciudad de México" `
  --ubicacion "Coyoacán, Ciudad de México" `
  --max 50
```

Los archivos Excel son acumulativos: las ejecuciones nuevas se agregan y las URLs repetidas
se actualizan sin duplicarse.

## Resultados

El programa crea la carpeta `results/` y guarda:

- `maps_resultados_completo.xlsx`: todos los negocios revisados.
- `leads_maps_sin_web.xlsx`: negocios activos, sin web y con perfil bueno o regular.
- `maps_urls_procesadas.csv`: historial local para evitar procesar dos veces una ficha.

Las columnas incluyen giro y ubicación, nombre, dirección, teléfono, URL de Maps, sitio
web, calificación, reseñas, clasificación, estado y fecha. `example_output.csv` contiene
una fila completamente ficticia.

## Problemas comunes

- **Python no se reconoce:** instala Python desde python.org y activa “Add Python to PATH”.
- **Falta una dependencia:** activa el entorno y ejecuta `pip install -r requirements.txt`.
- **Chrome o driver incompatible:** actualiza Chrome; el script intenta detectar su versión.
- **Permiso de escritura:** usa una carpeta donde tu usuario pueda escribir.
- **Falta `.env`:** actualmente no es obligatorio; copia `.env.example` si lo deseas.
- **Google Maps cambió:** sus selectores pueden requerir ajustes si cambia la interfaz.

## Uso responsable

Esta herramienta se entrega con fines educativos y de prospección legítima. Debes respetar
las condiciones de uso de las plataformas consultadas y la normativa aplicable. No la uses
para spam, acoso ni recopilación abusiva de datos. El usuario es responsable del uso del código.

## Autor y contacto

- Raval Marketing Lab
- GitHub: https://github.com/ramonsegh
- TikTok: _pendiente_
- Instagram: _pendiente_
- WhatsApp o página de contacto: _pendiente_

Si esta herramienta te sirvió, puedes seguirme en TikTok. Voy a seguir publicando
herramientas gratuitas de automatización, ventas e inteligencia artificial.

## Licencia

Distribuido bajo GNU GPL v3 para mantener compatibilidad con
`undetected-chromedriver`, una dependencia GPL-3.0. Consulta `LICENSE`.
