"""Análise de cobertura de um transmissor APRS (Ferramentas → Análise de cobertura, v1.14.63).

Portada do PT2VHF Mesh Analyzer v0.6.62 (mesh_analyzer/coverage.py), com unidades de VHF/APRS:
potência em W (padrão 50 W), 145,570 MHz e sensibilidade para decodificar APRS 1200 bps.


Calcula, em volta de um ponto do mapa ou de um nó conhecido, o sinal que chegaria
a um receptor em cada lugar, usando o mesmo relevo das outras ferramentas
(tiles Terrarium, ~38 m por pixel no zoom 12) e:

- perda em espaço livre;
- difração nos horizontes do transmissor e do receptor de cada trajeto (dois
  gumes de faca, Epstein-Peterson, ITU-R P.526), sobre a curvatura efetiva da
  Terra (fator k obtido da refratividade, como no modelo Longley-Rice);
- altura de obstáculos (vegetação/prédios) somada ao terreno entre as pontas;
- margem de confiabilidade: % de locais e % do tempo, com a variabilidade
  típica do clima de rádio escolhido.

O cálculo é feito ao longo de radiais a partir do transmissor e depois passado
para uma grade quadrada. A resposta traz a grade em dBm (um byte por pixel), para
a interface colorir e trocar a escala na hora, sem recalcular.
É uma estimativa para planejamento: não substitui medições.
"""
from __future__ import annotations

import base64
import math
from array import array
from concurrent.futures import ThreadPoolExecutor
from statistics import NormalDist

from .planning import (APRS_FREQ_MHZ, DEFAULT_SENSITIVITY_DBM, EARTH_R, TILE_URL, TerrainTiles, _knife_edge_db,
                       _number, _png_rgb, _point, _reason, despike, microvolts, s_units)

# Clima de rádio (nomes do Longley-Rice) -> desvio padrão da variação no tempo (dB).
CLIMATES = {
    "equatorial": ("Equatorial", 2.5),
    "continental_subtropical": ("Continental subtropical", 3.0),
    "maritime_subtropical": ("Marítimo subtropical", 3.0),
    "desert": ("Desértico", 4.5),
    "continental_temperate": ("Continental temperado", 4.0),
    "maritime_temperate_land": ("Marítimo temperado (terra)", 3.0),
    "maritime_temperate_sea": ("Marítimo temperado (mar)", 3.5),
}
LOCATION_SIGMA_DB = 8.0       # variação entre locais à mesma distância (terreno irregular)
NORMAL_ZOOM_MAX_TILES = 64
HIRES_ZOOM = 12
HIRES_MAX_KM = 40.0
MAX_KM = 100.0
DEFAULT_KM = 50.0
SEARCH_MAX_KM = 50.0
GRID_MAX = 640                # lado máximo da grade devolvida (pixels)
NODATA = 0                    # byte sem dado; os demais valem dBm + 200


def refractivity_k(n_units):
    """Fator k da Terra efetiva a partir da refratividade de superfície (N)."""
    return 1.0 / (1.0 - 0.04665 * math.exp(0.005577 * n_units))


DEFAULT_POWER_W = 50.0


def coverage_params(params):
    params = params or {}
    climate = str(params.get("climate") or "continental_subtropical")
    if climate not in CLIMATES:
        raise ValueError("Clima de rádio desconhecido")
    watts = _number(params, "tx_power_w", DEFAULT_POWER_W, 0.1, 1500, "Potência (W)")
    p = {
        "name": str(params.get("name") or "Transmissor")[:60],
        "tx_power_w": watts,
        "tx_power_dbm": round(10 * math.log10(watts * 1000), 1),
        "freq_mhz": _number(params, "freq_mhz", APRS_FREQ_MHZ, 28, 1300, "Frequência (MHz)"),
        "tx_height_m": _number(params, "tx_height_m", 10, 0.5, 300, "Altura do transmissor (m)"),
        "tx_gain_dbi": _number(params, "tx_gain_dbi", 3, -10, 30, "Ganho da antena do transmissor (dBi)"),
        "rx_sensitivity_dbm": _number(params, "rx_sensitivity_dbm", DEFAULT_SENSITIVITY_DBM, -140, -80,
                                      "Sensibilidade (dBm)"),
        "rx_height_m": _number(params, "rx_height_m", 2, 0.5, 100, "Altura do receptor (m)"),
        "rx_gain_dbi": _number(params, "rx_gain_dbi", 3, -10, 30, "Ganho da antena do receptor (dBi)"),
        "rx_cable_db": _number(params, "rx_cable_db", 1, 0, 30, "Perda no cabo (dB)"),
        "clutter_m": _number(params, "clutter_m", 1, 0, 60, "Altura de obstáculos (m)"),
        "refractivity_n": _number(params, "refractivity_n", 301, 250, 400, "Refratividade (N)"),
        "location_pct": _number(params, "location_pct", 95, 50, 99.9, "% de locais"),
        "time_pct": _number(params, "time_pct", 95, 50, 99.9, "% do tempo"),
        "max_km": _number(params, "max_km", DEFAULT_KM, 1, MAX_KM, "Raio da cobertura (km)"),
        "climate": climate,
        "hires": bool(params.get("hires")),
        "station": str(params.get("station") or "").upper().strip()[:12],
    }
    if p["hires"] and p["max_km"] > HIRES_MAX_KM:
        raise ValueError("Relevo em alta resolução: raio máximo de %d km" % HIRES_MAX_KM)
    return p


def fade_margin_db(location_pct, time_pct, climate):
    """Margem para que o sinal seja atingido em location_pct% dos locais e time_pct% do tempo."""
    z = NormalDist().inv_cdf
    zl, zt = z(location_pct / 100), z(time_pct / 100)
    sigma_t = CLIMATES[climate][1]
    sign = 1 if zl * LOCATION_SIGMA_DB + zt * sigma_t >= 0 else -1
    return sign * math.hypot(zl * LOCATION_SIGMA_DB, zt * sigma_t)


class _Raster:
    """Elevação por coordenada usando os tiles de um único zoom (baixados em paralelo).

    Cada tile fica num array de floats de 32 bits (256 KB), não em listas do Python."""

    def __init__(self, tiles: TerrainTiles, center, radius_m, zoom):
        self.tiles, self.z = tiles, zoom
        self.n = 2 ** zoom
        x0, y0, x1, y1 = self._span(tiles, center, radius_m, zoom)
        keys = [(tx % self.n, ty) for tx in range(x0, x1 + 1)
                for ty in range(max(0, y0), min(self.n - 1, y1) + 1)]
        self.grids = {}
        with ThreadPoolExecutor(max_workers=8) as pool:
            for key, grid in zip(keys, pool.map(self._load, keys)):
                self.grids[key] = grid

    @staticmethod
    def _span(tiles, center, radius_m, zoom):
        lat, lon = center
        dlat = math.degrees(radius_m / EARTH_R)
        dlon = dlat / max(0.05, math.cos(math.radians(lat)))
        x0, y0 = tiles._pixel(lat + dlat, lon - dlon, zoom)
        x1, y1 = tiles._pixel(lat - dlat, lon + dlon, zoom)
        return int(x0 // 256) - 1, int(y0 // 256) - 1, int(x1 // 256) + 1, int(y1 // 256) + 1

    @classmethod
    def tile_count(cls, tiles, center, radius_m, zoom):
        x0, y0, x1, y1 = cls._span(tiles, center, radius_m, zoom)
        return (x1 - x0 + 1) * (y1 - y0 + 1)

    def _load(self, key):
        tx, ty = key
        data = None
        path = None
        if self.tiles.cache_dir:
            from pathlib import Path
            path = Path(self.tiles.cache_dir) / str(self.z) / str(tx) / ("%d.png" % ty)
            if path.exists():
                data = path.read_bytes()
        if data is None:
            try:
                data = self.tiles.getter(TILE_URL.format(z=self.z, x=tx, y=ty))
            except Exception as exc:
                raise RuntimeError("Não foi possível baixar o relevo (%s). Verifique a internet; áreas já "
                                   "calculadas continuam disponíveis sem ela." % _reason(exc)) from exc
            if path is not None:
                try:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(data)
                except OSError:
                    pass
        width, bpp, rows = _png_rgb(data)
        grid = array("f")
        for r in rows:
            grid.extend((r[i] * 256 + r[i + 1] + r[i + 2] / 256) - 32768 for i in range(0, width * bpp, bpp))
        despike(grid, width)
        return grid

    def _v(self, gx, gy):
        tx, ty = int(gx // 256) % self.n, min(self.n - 1, max(0, int(gy // 256)))
        grid = self.grids.get((tx, ty))
        if grid is None:
            grid = self.grids[(tx, ty)] = self._load((tx, ty))
        return grid[(int(gy) % 256) * 256 + int(gx) % 256]

    def elevation(self, lat, lon):
        px, py = self.tiles._pixel(lat, lon, self.z)
        x0, y0 = math.floor(px - 0.5), math.floor(py - 0.5)
        fx, fy = px - 0.5 - x0, py - 0.5 - y0
        v00, v10, v01, v11 = self._v(x0, y0), self._v(x0 + 1, y0), self._v(x0, y0 + 1), self._v(x0 + 1, y0 + 1)
        return (v00 * (1 - fx) + v10 * fx) * (1 - fy) + (v01 * (1 - fx) + v11 * fx) * fy


def pixel_size_m(lat, zoom):
    return 2 * math.pi * EARTH_R * math.cos(math.radians(lat)) / (256 * 2 ** zoom)


def choose_zoom(tiles, center, radius_m, hires):
    if hires:
        return HIRES_ZOOM
    for z in range(HIRES_ZOOM - 1, 7, -1):
        if _Raster.tile_count(tiles, center, radius_m, z) <= NORMAL_ZOOM_MAX_TILES:
            return z
    return 8


def _destination(lat, lon, bearing_rad, dist_m):
    """Ponto a dist_m do (lat, lon) no rumo dado (aproximação plana local, até ~70 km)."""
    dlat = dist_m * math.cos(bearing_rad) / EARTH_R
    dlon = dist_m * math.sin(bearing_rad) / (EARTH_R * math.cos(math.radians(lat)))
    return lat + math.degrees(dlat), lon + math.degrees(dlon)


def _v(x, y, x0, y0, x1, y1, wavelength):
    """Parâmetro de difração de um gume em (x, y) sobre a reta (x0, y0)-(x1, y1)."""
    d1, d2 = x - x0, x1 - x
    if d1 <= 0 or d2 <= 0:
        return -9.0
    line = y0 + (y1 - y0) * d1 / (x1 - x0)
    return (y - line) * math.sqrt(2 * (x1 - x0) / (wavelength * d1 * d2))


def _radial(raster, lat, lon, bearing, steps, step, htx, rx_h, clutter, k_r, wavelength, base, log_f):
    """Sinal (dBm) em cada passo de uma radial.

    As alturas ficam num plano corrigido pela curvatura (h' = h - d²/2kR), onde os raios
    são retas. A envoltória superior do perfil (o "elástico" esticado sobre o terreno) é
    mantida a cada passo; para cada receptor, os gumes que contam são o horizonte do
    transmissor e o do receptor (Epstein-Peterson com dois gumes)."""
    row = [None] * steps
    hx, hy = [0.0], [htx]                 # envoltória superior: transmissor + obstáculos
    for i in range(1, steps):
        d = i * step
        plat, plon = _destination(lat, lon, bearing, d)
        g = raster.elevation(plat, plon)
        drop = d * d / k_r
        rx, ry = d, g + rx_h - drop
        # Último vértice da envoltória ainda visível pelo receptor (tangente a partir dele).
        lo, hi = 0, len(hx) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            cross = (hx[mid] - hx[mid - 1]) * (ry - hy[mid - 1]) - (hy[mid] - hy[mid - 1]) * (rx - hx[mid - 1])
            if cross < 0:
                lo = mid
            else:
                hi = mid - 1
        k = lo
        loss = 20 * math.log10(d / 1000) + log_f
        if k == 0:
            if len(hx) > 1:               # visada: só a zona de Fresnel do horizonte do transmissor
                loss += _knife_edge_db(_v(hx[1], hy[1], 0.0, htx, rx, ry, wavelength))
        elif k == 1:
            loss += _knife_edge_db(_v(hx[1], hy[1], 0.0, htx, rx, ry, wavelength))
        else:
            ax, ay, bx, by = hx[1], hy[1], hx[k], hy[k]
            loss += _knife_edge_db(_v(ax, ay, 0.0, htx, bx, by, wavelength))
            loss += _knife_edge_db(_v(bx, by, ax, ay, rx, ry, wavelength))
        row[i] = base - loss
        # O ponto (com a altura de obstáculos) entra na envoltória para os próximos passos.
        px, py = d, g + clutter - drop
        while len(hx) >= 2 and (hx[-1] - hx[-2]) * (py - hy[-2]) - (hy[-1] - hy[-2]) * (px - hx[-2]) >= 0:
            hx.pop()
            hy.pop()
        hx.append(px)
        hy.append(py)
    return row


def coverage(tiles: TerrainTiles, center, params=None):
    """Grade de sinal estimado (dBm) em volta do transmissor."""
    lat, lon = _point(center, "transmissor")
    p = coverage_params(params)
    radius = p["max_km"] * 1000
    zoom = choose_zoom(tiles, (lat, lon), radius, p["hires"])
    raster = _Raster(tiles, (lat, lon), radius, zoom)
    step = max(15.0, pixel_size_m(lat, zoom))
    steps = int(radius / step) + 1
    radials = max(360, min(2048, int(math.ceil(2 * math.pi * radius / (1.5 * step)))))
    k_r = 2 * refractivity_k(p["refractivity_n"]) * EARTH_R      # d²/k_r = queda pela curvatura
    wavelength = 299.792458 / p["freq_mhz"]
    ground0 = raster.elevation(lat, lon)
    htx = ground0 + p["tx_height_m"]
    fade = fade_margin_db(p["location_pct"], p["time_pct"], p["climate"])
    base = p["tx_power_dbm"] + p["tx_gain_dbi"] + p["rx_gain_dbi"] - p["rx_cable_db"] - fade
    clutter, rx_h = p["clutter_m"], p["rx_height_m"]
    log_f = 20 * math.log10(p["freq_mhz"]) + 32.44
    table = []
    for r in range(radials):
        bearing = 2 * math.pi * r / radials
        table.append(_radial(raster, lat, lon, bearing, steps, step, htx, rx_h, clutter, k_r, wavelength, base, log_f))
    # Radiais -> grade quadrada centrada no transmissor.
    size = min(GRID_MAX, max(64, int(2 * radius / step)))
    cell = 2 * radius / size
    out = bytearray(size * size)
    above = 0
    farthest = 0.0
    sens = p["rx_sensitivity_dbm"]
    for y in range(size):
        north = radius - (y + 0.5) * cell
        for x in range(size):
            east = -radius + (x + 0.5) * cell
            d = math.hypot(east, north)
            if d > radius:
                continue
            i = int(round(d / step))
            if i >= steps:
                continue
            r = int(round(math.atan2(east, north) / (2 * math.pi) * radials)) % radials
            value = table[r][i] if i else table[r][1] if steps > 1 else None
            if value is None:
                continue
            out[y * size + x] = max(1, min(254, int(round(value)) + 200))
            if value >= sens:
                above += 1
                farthest = max(farthest, d)
    dlat = math.degrees(radius / EARTH_R)
    dlon = dlat / math.cos(math.radians(lat))
    return {
        "center": {"lat": lat, "lon": lon, "ground_m": round(ground0, 1)},
        "params": p,
        "bounds": [[lat - dlat, lon - dlon], [lat + dlat, lon + dlon]],
        "size": size,
        "cell_m": round(cell, 1),
        "grid": base64.b64encode(bytes(out)).decode("ascii"),
        "encoding": "uint8: 0 = sem dado; demais = dBm + 200",
        "terrain_m": round(pixel_size_m(lat, zoom), 1),
        "radials": radials,
        "fade_margin_db": round(fade, 1),
        "covered_km2": round(above * cell * cell / 1e6, 1),
        "farthest_km": round(farthest / 1000, 1),
        "sensitivity_uv": round(microvolts(p["rx_sensitivity_dbm"]), 2),
        "sensitivity_s": s_units(p["rx_sensitivity_dbm"]),
        "notes": "Estimativa: relevo de ~%d m por pixel, difração nos horizontes do transmissor e do receptor "
                 "de cada trajeto (dois gumes), "
                 "fator k %.2f (N=%g) e margem de %.1f dB para %g%% dos locais e %g%% do tempo. "
                 "Prédios e árvores só entram pela altura de obstáculos informada."
                 % (round(pixel_size_m(lat, zoom)), refractivity_k(p["refractivity_n"]), p["refractivity_n"],
                    fade, p["location_pct"], p["time_pct"]),
    }


def highest_point(tiles: TerrainTiles, center, radius_km):
    """Ponto mais alto do terreno dentro do raio (km), para posicionar o transmissor."""
    lat, lon = _point(center, "ponto")
    try:
        radius_km = float(radius_km)
    except (TypeError, ValueError):
        raise ValueError("Raio de busca inválido") from None
    if not 0.05 <= radius_km <= SEARCH_MAX_KM:
        raise ValueError("Buscar ponto mais alto: raio de 0,05 a %d km" % SEARCH_MAX_KM)
    radius = radius_km * 1000
    # Raios grandes usam relevo mais grosso para a busca continuar rápida (~0,5 milhão de amostras).
    zoom = HIRES_ZOOM if radius_km <= 8 else HIRES_ZOOM - 1 if radius_km <= 20 else HIRES_ZOOM - 2
    raster = _Raster(tiles, (lat, lon), radius, zoom)
    step = max(20.0, pixel_size_m(lat, zoom))
    n = int(radius / step)
    best = (raster.elevation(lat, lon), lat, lon)
    for iy in range(-n, n + 1):
        for ix in range(-n, n + 1):
            if (ix * ix + iy * iy) * step * step > radius * radius:
                continue
            plat = lat + math.degrees(iy * step / EARTH_R)
            plon = lon + math.degrees(ix * step / (EARTH_R * math.cos(math.radians(lat))))
            e = raster.elevation(plat, plon)
            if e > best[0]:
                best = (e, plat, plon)
    return {"lat": round(best[1], 6), "lon": round(best[2], 6), "ground_m": round(best[0], 1),
            "searched_km": radius_km}


def value_at(result, lat, lon):
    """Sinal estimado (dBm) da grade num ponto, ou None fora da grade / sem dado."""
    (s, w), (n, e) = result["bounds"]
    if not (s <= lat <= n and w <= lon <= e):
        return None
    size = result["size"]
    grid = result.get("_bytes")
    if grid is None:
        grid = result["_bytes"] = base64.b64decode(result["grid"])
    x = min(size - 1, int((lon - w) / (e - w) * size))
    y = min(size - 1, int((n - lat) / (n - s) * size))
    b = grid[y * size + x]
    return b - 200 if b else None


def classify_nodes(result, nodes, exclude=None):
    """Separa os nós com posição em: com cobertura, sem cobertura (dentro do raio) e fora do raio."""
    lat0, lon0 = result["center"]["lat"], result["center"]["lon"]
    sens = result["params"]["rx_sensitivity_dbm"]
    radius = result["params"]["max_km"] * 1000
    covered, uncovered, outside = [], [], []
    for n in nodes:
        if exclude is not None and n.get("node_num") == exclude:
            continue
        lat, lon = n.get("lat"), n.get("lon")
        if lat is None or lon is None:
            continue
        dist = math.hypot((lat - lat0) * 111320, (lon - lon0) * 111320 * math.cos(math.radians(lat0)))
        item = {**n, "distance_km": round(dist / 1000, 1)}
        if dist > radius:
            outside.append(item)
            continue
        dbm = value_at(result, lat, lon)
        item["dbm"] = dbm
        if dbm is not None and dbm >= sens:
            covered.append(item)
        else:
            item["missing_db"] = round(sens - dbm, 1) if dbm is not None else None
            uncovered.append(item)
    covered.sort(key=lambda x: -x["dbm"])
    uncovered.sort(key=lambda x: (x["dbm"] is None, -(x["dbm"] or -999)))
    outside.sort(key=lambda x: x["distance_km"])
    return covered, uncovered, outside

