import argparse
import re
import time
import urllib.parse
import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.common.exceptions import SessionNotCreatedException, TimeoutException
from selenium.webdriver.common.by import By


_UC_CHROME_DEL = uc.Chrome.__del__


def _silenciar_error_cierre_uc(self):
    try:
        _UC_CHROME_DEL(self)
    except OSError:
        pass


uc.Chrome.__del__ = _silenciar_error_cierre_uc


# ---------- CONFIG RAPIDA ----------
GIROS = [
    "dentistas",
]

UBICACIONES = [
    "Ciudad de México, México",
]

MAX_RESULTADOS_POR_BUSQUEDA = 100
MAX_SCROLLS_POR_BUSQUEDA = 8
AUTOSAVE_CADA = 5
MODO_HEADLESS = False
CHROME_VERSION_MAIN = None  # Ejemplo: 149. Dejalo en None para autodetectar.

RATING_BUEN_PERFIL = 4.3
RESENAS_BUEN_PERFIL = 20
RATING_PERFIL_REGULAR = 3.8
RESENAS_PERFIL_REGULAR = 5

DIRECTORIO_PROYECTO = Path(__file__).resolve().parent
DIRECTORIO_RESULTADOS = DIRECTORIO_PROYECTO / "results"
RUTA_RESULTADOS = DIRECTORIO_RESULTADOS / "maps_resultados_completo.xlsx"
RUTA_LEADS_SIN_WEB = DIRECTORIO_RESULTADOS / "leads_maps_sin_web.xlsx"
RUTA_HISTORIAL_PROCESADOS = DIRECTORIO_RESULTADOS / "maps_urls_procesadas.csv"
# ------------------------------------


def normalizar(texto: str) -> str:
    if not isinstance(texto, str):
        return ""
    texto = texto.lower()
    texto = "".join(
        c for c in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(c)
    )
    return " ".join(texto.split())


def crear_opciones_uc():
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--lang=es-MX")

    if MODO_HEADLESS:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

    return options


def crear_opciones_selenium():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--lang=es-MX")

    if MODO_HEADLESS:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

    return options


def crear_driver():
    version_main = CHROME_VERSION_MAIN or detectar_version_chrome()
    try:
        if version_main:
            print(f"Chrome detectado: version principal {version_main}")
            return uc.Chrome(options=crear_opciones_uc(), version_main=version_main)
        return uc.Chrome(options=crear_opciones_uc())
    except (RuntimeError, SessionNotCreatedException) as error:
        version_main = extraer_version_chrome_del_error(str(error))
        if version_main:
            print(f"Reintentando con Chrome version principal {version_main}")
            try:
                return uc.Chrome(options=crear_opciones_uc(), version_main=version_main)
            except Exception as retry_error:
                print(f"undetected_chromedriver fallo otra vez: {retry_error}")

        print("Probando fallback con Selenium Chrome normal.")
        return webdriver.Chrome(options=crear_opciones_selenium())


def detectar_version_chrome():
    """Detecta la version principal de Chrome en Windows desde el registro."""
    try:
        import winreg
    except ImportError:
        return None

    rutas = [
        (winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Google\Chrome\BLBeacon"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Google\Chrome\BLBeacon"),
    ]

    for hive, ruta in rutas:
        try:
            with winreg.OpenKey(hive, ruta) as key:
                version, _ = winreg.QueryValueEx(key, "version")
                return int(str(version).split(".")[0])
        except Exception:
            pass

    return None


def extraer_version_chrome_del_error(mensaje: str):
    match = re.search(r"Current browser version is (\d+)\.", mensaje)
    if not match:
        return None
    return int(match.group(1))


def construir_url_busqueda(giro: str, ubicacion: str) -> str:
    query = f"{giro} en {ubicacion}"
    return "https://www.google.com/maps/search/" + urllib.parse.quote(query)


def numero_desde_texto(texto: str):
    if not texto:
        return None
    limpio = re.sub(r"[^\d]", "", str(texto))
    if not limpio:
        return None
    try:
        return int(limpio)
    except ValueError:
        return None


def extraer_rating_resenas(texto: str):
    if not texto:
        return None, None

    texto_limpio = " ".join(str(texto).split())
    texto_normalizado = normalizar(texto_limpio)
    rating = None
    resenas = None

    rating_match = re.search(
        r"(?:ratingValue|calificacion|calificación)?\s*:?\s*\b([1-5][,.]\d)\b",
        texto_limpio,
        flags=re.IGNORECASE,
    )
    if rating_match:
        try:
            rating = float(rating_match.group(1).replace(",", "."))
        except ValueError:
            rating = None

    patrones_resenas = [
        r"[1-5][,.]\d[^\d\n]{0,30}\(\s*([\d.,\s]+)\s*\)",
        r"[1-5][,.]\d(?:\s*(?:estrellas?|stars?|★+))*\s+([\d.,]+)\s+(?:opiniones|resenas|reseñas|reviews)\b",
        r"(?:opiniones|resenas|reseñas|reviews)\s*:?\s*([\d.,\s]+)\b",
        r"(?<![,.])\b([\d][\d.,\s]*)\s+(?:opiniones|resenas|reseñas|reviews)\b",
        r"reviewCount\s*:?\s*([\d.,\s]+)\b",
    ]
    for patron in patrones_resenas:
        match = re.search(patron, texto_normalizado, flags=re.IGNORECASE)
        if match:
            resenas = numero_desde_texto(match.group(1))
            if resenas is not None:
                break

    return rating, resenas


def clasificar_perfil(rating, resenas) -> str:
    if rating is None or resenas is None:
        return "SIN_DATOS"
    if rating >= RATING_BUEN_PERFIL and resenas >= RESENAS_BUEN_PERFIL:
        return "BUEN_PERFIL"
    if rating >= RATING_PERFIL_REGULAR and resenas >= RESENAS_PERFIL_REGULAR:
        return "PERFIL_REGULAR"
    return "PERFIL_BAJO"


def limpiar_telefono(texto: str) -> str:
    if not texto:
        return ""
    digitos = "".join(c for c in str(texto) if c.isdigit())
    if len(digitos) >= 10:
        return digitos[-10:]
    return digitos


def url_canonica_maps(url: str) -> str:
    if not url:
        return ""
    return str(url).split("?")[0].rstrip("/")


def texto_elemento(elemento) -> str:
    try:
        return elemento.text.strip()
    except Exception:
        return ""


def obtener_feed(driver):
    feeds = driver.find_elements(By.CSS_SELECTOR, 'div[role="feed"]')
    if feeds:
        return feeds[0]
    return None


def recolectar_urls_resultados(driver, giro: str, ubicacion: str):
    url = construir_url_busqueda(giro, ubicacion)
    print(f"\nBuscando: {giro} en {ubicacion}")

    try:
        driver.get(url)
    except TimeoutException:
        print("Timeout cargando Google Maps.")
        return []

    time.sleep(4)

    resultados = {}
    scrolls_sin_nuevos = 0

    for _ in range(MAX_SCROLLS_POR_BUSQUEDA):
        links = driver.find_elements(By.CSS_SELECTOR, "a.hfpxzc")
        antes = len(resultados)

        for link in links:
            href = link.get_attribute("href") or ""
            nombre = link.get_attribute("aria-label") or texto_elemento(link)
            if not href or "/maps/place/" not in href:
                continue
            resultados[href] = {
                "giro_busqueda": giro,
                "ubicacion_busqueda": ubicacion,
                "maps_nombre_lista": nombre,
                "maps_url": href,
            }
            if len(resultados) >= MAX_RESULTADOS_POR_BUSQUEDA:
                break

        print(f"  Resultados detectados: {len(resultados)}")
        if len(resultados) >= MAX_RESULTADOS_POR_BUSQUEDA:
            break

        feed = obtener_feed(driver)
        if feed:
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", feed)
        elif links:
            driver.execute_script("arguments[0].scrollIntoView({block: 'end'});", links[-1])

        time.sleep(2)

        if len(resultados) == antes:
            scrolls_sin_nuevos += 1
            if scrolls_sin_nuevos >= 2:
                break
        else:
            scrolls_sin_nuevos = 0

    return list(resultados.values())


def buscar_texto_por_selectores(driver, selectores):
    for selector in selectores:
        try:
            elementos = driver.find_elements(By.CSS_SELECTOR, selector)
            for elemento in elementos:
                texto = texto_elemento(elemento)
                if texto:
                    return texto
        except Exception:
            pass
    return ""


def buscar_atributo_por_selectores(driver, selectores, atributo):
    for selector in selectores:
        try:
            elementos = driver.find_elements(By.CSS_SELECTOR, selector)
            for elemento in elementos:
                valor = elemento.get_attribute(atributo)
                if valor:
                    return valor.strip()
        except Exception:
            pass
    return ""


def recolectar_texto_ficha(driver) -> str:
    partes = []

    for selector in ['div[role="main"]', "body"]:
        try:
            texto = driver.find_element(By.CSS_SELECTOR, selector).text
            if texto:
                partes.append(texto)
                break
        except Exception:
            pass

    for selector in [
        "[aria-label]",
        'meta[itemprop="ratingValue"]',
        'meta[itemprop="reviewCount"]',
    ]:
        try:
            for elemento in driver.find_elements(By.CSS_SELECTOR, selector):
                itemprop = elemento.get_attribute("itemprop") or ""
                for atributo in ("aria-label", "content"):
                    valor = elemento.get_attribute(atributo)
                    if valor:
                        if itemprop:
                            partes.append(f"{itemprop}: {valor}")
                        else:
                            partes.append(valor)
        except Exception:
            pass

    return "\n".join(partes)


def limpiar_valor_contacto(valor: str) -> str:
    if not valor:
        return ""

    valor = str(valor).strip()
    valor = re.sub(r"^phone:(?:tel:)?", "", valor, flags=re.IGNORECASE)
    valor = re.sub(
        r"^(?:telefono|teléfono|phone|direccion|dirección|address)\s*:\s*",
        "",
        valor,
        flags=re.IGNORECASE,
    )
    return valor.strip()


def buscar_valor_contacto(driver, selectores):
    for selector in selectores:
        try:
            elementos = driver.find_elements(By.CSS_SELECTOR, selector)
            for elemento in elementos:
                for atributo in ("text", "aria-label", "data-item-id"):
                    if atributo == "text":
                        valor = texto_elemento(elemento)
                    else:
                        valor = elemento.get_attribute(atributo)

                    valor = limpiar_valor_contacto(valor)
                    if valor:
                        return valor
        except Exception:
            pass
    return ""


def extraer_ficha(driver, base: dict) -> dict:
    driver.get(base["maps_url"])
    time.sleep(3)

    texto_pagina = recolectar_texto_ficha(driver)

    nombre = buscar_texto_por_selectores(driver, ["h1.DUwDvf", "h1"])
    if not nombre:
        nombre = base.get("maps_nombre_lista", "")

    website = buscar_atributo_por_selectores(
        driver,
        [
            'a[data-item-id="authority"]',
            'a[data-item-id^="authority"]',
            'a[aria-label*="Sitio web"]',
            'a[aria-label*="Website"]',
        ],
        "href",
    )

    telefono = buscar_valor_contacto(
        driver,
        [
            'button[data-item-id^="phone:"]',
            'button[aria-label*="Teléfono"]',
            'button[aria-label*="Telefono"]',
            'button[aria-label*="Phone"]',
        ],
    )

    direccion = buscar_valor_contacto(
        driver,
        [
            'button[data-item-id="address"]',
            'button[aria-label*="Dirección"]',
            'button[aria-label*="Direccion"]',
            'button[aria-label*="Address"]',
        ],
    )

    rating, resenas = extraer_rating_resenas(texto_pagina)
    cerrado = bool(
        re.search(
            r"cerrado permanentemente|permanently closed",
            normalizar(texto_pagina),
            flags=re.IGNORECASE,
        )
    )
    perfil = clasificar_perfil(rating, resenas)
    tiene_web = bool(website)
    lead_sin_web = (not cerrado) and (not tiene_web) and perfil in {
        "BUEN_PERFIL",
        "PERFIL_REGULAR",
    }

    return {
        **base,
        "maps_nombre": nombre,
        "maps_direccion": direccion,
        "maps_telefono": telefono,
        "telefono_10_digitos": limpiar_telefono(telefono),
        "maps_website": website,
        "maps_tiene_web": tiene_web,
        "maps_rating": rating,
        "maps_resenas": resenas,
        "maps_perfil_calidad": perfil,
        "maps_cerrado": cerrado,
        "maps_lead_sin_web": lead_sin_web,
        "fecha_scrapeo": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def deduplicar_por_url(registros):
    vistos = set()
    unicos = []
    for registro in registros:
        url = url_canonica_maps(registro.get("maps_url", ""))
        if not url or url in vistos:
            continue
        vistos.add(url)
        unicos.append(registro)
    return unicos


def cargar_urls_procesadas():
    urls = set()

    if RUTA_HISTORIAL_PROCESADOS.exists():
        try:
            df = pd.read_csv(RUTA_HISTORIAL_PROCESADOS, dtype=str)
            if "maps_url_canonica" in df.columns:
                serie = df["maps_url_canonica"]
            elif "maps_url" in df.columns:
                serie = df["maps_url"]
            else:
                serie = pd.Series(dtype=str)

            urls.update(
                url_canonica_maps(url)
                for url in serie.dropna()
                if url_canonica_maps(url)
            )
        except Exception:
            pass

    if RUTA_RESULTADOS.exists():
        try:
            df = pd.read_excel(RUTA_RESULTADOS, dtype=str)
            if "maps_url" in df.columns:
                urls.update(
                    url_canonica_maps(url)
                    for url in df["maps_url"].dropna()
                    if url_canonica_maps(url)
                )
        except Exception:
            pass

    return urls


def filtrar_urls_ya_procesadas(registros, urls_procesadas):
    nuevos = []
    omitidos = 0

    for registro in registros:
        url = url_canonica_maps(registro.get("maps_url", ""))
        if url and url in urls_procesadas:
            omitidos += 1
            continue
        nuevos.append(registro)

    return nuevos, omitidos


def guardar_historial_procesados(registros):
    if not registros:
        return

    columnas = [
        "maps_url_canonica",
        "giro_busqueda",
        "ubicacion_busqueda",
        "maps_url",
        "maps_nombre",
        "maps_telefono",
        "telefono_10_digitos",
        "maps_tiene_web",
        "maps_rating",
        "maps_resenas",
        "maps_perfil_calidad",
        "maps_lead_sin_web",
        "fecha_scrapeo",
    ]

    filas = []
    for registro in registros:
        url = url_canonica_maps(registro.get("maps_url", ""))
        if not url:
            continue
        fila = {col: registro.get(col, "") for col in columnas}
        fila["maps_url_canonica"] = url
        filas.append(fila)

    if not filas:
        return

    df_nuevo = pd.DataFrame(filas, columns=columnas)
    if RUTA_HISTORIAL_PROCESADOS.exists():
        try:
            df_actual = pd.read_csv(RUTA_HISTORIAL_PROCESADOS, dtype=str)
            df_nuevo = pd.concat([df_actual, df_nuevo], ignore_index=True)
        except Exception:
            pass

    df_nuevo = df_nuevo.drop_duplicates(subset=["maps_url_canonica"], keep="last")
    df_nuevo.to_csv(RUTA_HISTORIAL_PROCESADOS, index=False, encoding="utf-8-sig")


def guardar_resultados(registros):
    if not registros:
        return

    df_nuevo = pd.DataFrame(registros)
    if RUTA_RESULTADOS.exists():
        try:
            df_anterior = pd.read_excel(RUTA_RESULTADOS)
            df = pd.concat([df_anterior, df_nuevo], ignore_index=True)
        except Exception as error:
            print(f"Aviso: no se pudo leer el Excel anterior: {error}")
            df = df_nuevo
    else:
        df = df_nuevo

    df = df.drop_duplicates(subset=["maps_url"], keep="last")
    df.to_excel(RUTA_RESULTADOS, index=False)

    leads = df[df["maps_lead_sin_web"] == True].copy()
    orden_leads = [
        "giro_busqueda",
        "ubicacion_busqueda",
        "maps_nombre",
        "maps_telefono",
        "telefono_10_digitos",
        "maps_rating",
        "maps_resenas",
        "maps_perfil_calidad",
        "maps_direccion",
        "maps_url",
        "maps_website",
        "fecha_scrapeo",
    ]
    columnas = [col for col in orden_leads if col in leads.columns]
    leads[columnas].to_excel(RUTA_LEADS_SIN_WEB, index=False)


def parsear_args():
    parser = argparse.ArgumentParser(
        description="Scraper directo de Google Maps para detectar negocios con buen perfil y sin web."
    )
    parser.add_argument(
        "--ubicacion",
        action="append",
        help="Ubicacion a buscar. Puedes repetirlo: --ubicacion \"Celaya, Guanajuato\"",
    )
    parser.add_argument(
        "--giro",
        action="append",
        help="Giro a buscar. Puedes repetirlo: --giro dentistas --giro barberias",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=None,
        help="Maximo de resultados por busqueda.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Corre Chrome sin ventana visible.",
    )
    return parser.parse_args()


def main():
    global MAX_RESULTADOS_POR_BUSQUEDA, MODO_HEADLESS

    args = parsear_args()
    DIRECTORIO_RESULTADOS.mkdir(parents=True, exist_ok=True)
    giros = args.giro or GIROS
    ubicaciones = args.ubicacion or UBICACIONES
    if args.max:
        MAX_RESULTADOS_POR_BUSQUEDA = args.max
    if args.headless:
        MODO_HEADLESS = True

    print("Scraper directo Google Maps")
    print("Giros:", ", ".join(giros))
    print("Ubicaciones:", ", ".join(ubicaciones))
    print("Salida completa:", RUTA_RESULTADOS)
    print("Leads sin web:", RUTA_LEADS_SIN_WEB)
    print("Historial procesados:", RUTA_HISTORIAL_PROCESADOS)

    urls_procesadas = cargar_urls_procesadas()
    if urls_procesadas:
        print(f"URLs ya procesadas en historial: {len(urls_procesadas)}")

    driver = crear_driver()
    driver.set_page_load_timeout(30)
    registros = []
    historial_pendiente = []

    try:
        candidatos = []
        for giro in giros:
            for ubicacion in ubicaciones:
                candidatos.extend(recolectar_urls_resultados(driver, giro, ubicacion))

        candidatos = deduplicar_por_url(candidatos)
        total_unicos = len(candidatos)
        candidatos, omitidos = filtrar_urls_ya_procesadas(candidatos, urls_procesadas)
        print(f"\nFichas unicas detectadas: {total_unicos}")
        print(f"Fichas omitidas por historial: {omitidos}")
        print(f"Fichas nuevas por revisar: {len(candidatos)}")
        if omitidos and len(candidatos) <= 1:
            print(
                "Aviso: Google Maps devolvio casi la misma lista de la ejecucion "
                "anterior. Usa varias ubicaciones, como hacia el scraper original."
            )

        for idx, candidato in enumerate(candidatos, start=1):
            try:
                ficha = extraer_ficha(driver, candidato)
                registros.append(ficha)
                historial_pendiente.append(ficha)
                urls_procesadas.add(url_canonica_maps(ficha.get("maps_url", "")))
                etiqueta = "LEAD SIN WEB" if ficha["maps_lead_sin_web"] else "descartado"
                print(
                    f"[{idx}/{len(candidatos)}] {etiqueta}: "
                    f"{ficha['maps_nombre']} | {ficha['maps_rating']} "
                    f"({ficha['maps_resenas']}) | web={ficha['maps_tiene_web']}"
                )
            except Exception as error:
                registros.append({
                    **candidato,
                    "maps_error": str(error),
                    "maps_lead_sin_web": False,
                    "fecha_scrapeo": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
                print(f"[{idx}/{len(candidatos)}] Error revisando ficha: {error}")

            if idx % AUTOSAVE_CADA == 0:
                guardar_resultados(registros)
                guardar_historial_procesados(historial_pendiente)
                historial_pendiente = []
                print("Autosave listo.")

            time.sleep(1.5)

    finally:
        try:
            driver.quit()
        except Exception:
            pass

    guardar_resultados(registros)
    guardar_historial_procesados(historial_pendiente)
    leads = sum(1 for r in registros if r.get("maps_lead_sin_web"))
    print("\nProceso terminado.")
    print(f"Registros revisados en esta ejecucion: {len(registros)}")
    print(f"Resultados acumulados: {RUTA_RESULTADOS}")
    print(f"Leads sin web encontrados en esta ejecucion: {leads}")
    print(f"Leads acumulados: {RUTA_LEADS_SIN_WEB}")
    print(f"Historial actualizado: {RUTA_HISTORIAL_PROCESADOS}")


if __name__ == "__main__":
    main()
