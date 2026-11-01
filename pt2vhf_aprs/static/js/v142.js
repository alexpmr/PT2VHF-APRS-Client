(() => {
'use strict';

const $ = (s, r=document) => r.querySelector(s);
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const lang = () => String(document.documentElement.lang || localStorage.getItem('pt2vhf_language') || 'pt-BR').toLowerCase();
const tr = (pt,en,es,fr) => {
  const consolidated = window.pt2vhfI18n.lookup(pt);
  if (consolidated !== undefined) return consolidated;
    const l = lang();
    const locale = l.startsWith('de') ? 'de-DE'
      : l.startsWith('it') ? 'it-IT'
      : l.startsWith('ja') ? 'ja-JP'
      : l.startsWith('pl') ? 'pl-PL'
      : l.startsWith('nl') ? 'nl-NL'
      : l.startsWith('zh') ? 'zh-CN' : '';
    const extended = locale ? window.PT2VHF_I18N?.[locale]?.[pt] : '';
    if (extended) return extended;
    return l.startsWith('en') ? en : l.startsWith('es') ? es : l.startsWith('fr') ? fr : pt;
  };
const coverageState = {
  enabled: localStorage.getItem('pt2vhf_rf_coverage_enabled') === '1',
  mode: localStorage.getItem('pt2vhf_rf_coverage_mode') || 'heatmap',
  map: null,
  layer: null,
  loading: false,
  points: [],
  meta: null,
  timer: null,
};

async function req(url) {
  const response = await fetch(url, {cache:'no-store'});
  const data = await response.json();
  if (!response.ok) throw new Error(data?.error || response.statusText);
  return data;
}

// Cobertura de 5 km de diâmetro ao redor de cada estação, digi ou tracker (v1.14.53).
const HEAT_RADIUS_METERS = 2500;
const HEAT_MIN_RADIUS_PX = 5;
const HEAT_MAX_RADIUS_PX = 320;
const HEAT_MAX_ALPHA = 215;
const HEAT_GRADIENT = [[0, '#0000ff'], [.35, '#00c8ff'], [.55, '#00ff40'], [.7, '#ffff00'], [.85, '#ff8000'], [1, '#ff0000']];
const heatStamps = new Map();
let heatPaletteCache = null;

function heatStamp(radius) {
  if (heatStamps.has(radius)) return heatStamps.get(radius);
  const stamp = document.createElement('canvas');
  stamp.width = stamp.height = radius * 2;
  const ctx = stamp.getContext('2d');
  const gradient = ctx.createRadialGradient(radius, radius, 0, radius, radius, radius);
  gradient.addColorStop(0, 'rgba(0,0,0,1)');
  gradient.addColorStop(.6, 'rgba(0,0,0,.6)');
  gradient.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, radius * 2, radius * 2);
  heatStamps.set(radius, stamp);
  return stamp;
}

function heatPalette() {
  if (heatPaletteCache) return heatPaletteCache;
  const canvas = document.createElement('canvas');
  canvas.width = 1; canvas.height = 256;
  const ctx = canvas.getContext('2d');
  const gradient = ctx.createLinearGradient(0, 0, 0, 256);
  for (const [stop, color] of HEAT_GRADIENT) gradient.addColorStop(stop, color);
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 1, 256);
  heatPaletteCache = ctx.getImageData(0, 0, 1, 256).data;
  return heatPaletteCache;
}

function createHeatLayer() {
  if (!window.L || !L.Layer) return null;
  return L.Layer.extend({
    initialize(points=[]) { this._points = points; },
    setPoints(points=[]) { this._points = points; this._draw(); return this; },
    onAdd(map) {
      this._map = map;
      this._canvas = L.DomUtil.create('canvas', 'v142-rf-heatmap-canvas');
      this._canvas.setAttribute('aria-hidden', 'true');
      map.getPanes().overlayPane.appendChild(this._canvas);
      map.on('moveend zoomend resize', this._reset, this);
      this._reset();
    },
    onRemove(map) {
      map.off('moveend zoomend resize', this._reset, this);
      this._canvas?.remove();
      this._canvas = null;
      this._map = null;
    },
    _reset() {
      if (!this._map || !this._canvas) return;
      const size = this._map.getSize();
      const ratio = Math.max(1, Math.min(2, window.devicePixelRatio || 1));
      this._canvas.width = Math.max(1, Math.round(size.x * ratio));
      this._canvas.height = Math.max(1, Math.round(size.y * ratio));
      this._canvas.style.width = size.x + 'px';
      this._canvas.style.height = size.y + 'px';
      const topLeft = this._map.containerPointToLayerPoint([0,0]);
      L.DomUtil.setPosition(this._canvas, topLeft);
      this._draw();
    },
    // v1.14.52: mapa de calor clássico (densidade → paleta azul…vermelho).
    // Cada ponto soma intensidade num canvas em tons de alfa; depois a
    // intensidade acumulada vira cor. O raio é geográfico (2,5 km = 5 km de diâmetro), então a
    // espessura acompanha a área real em qualquer zoom.
    _draw() {
      if (!this._map || !this._canvas) return;
      const ctx = this._canvas.getContext('2d');
      if (!ctx) return;
      const width = this._canvas.width, height = this._canvas.height;
      const ratio = width / Math.max(1, this._map.getSize().x);
      ctx.setTransform(1,0,0,1,0,0);
      ctx.clearRect(0,0,width,height);
      const points = this._points || [];
      if (!points.length) return;
      const zoom = Number(this._map.getZoom() || 8);
      const lat = this._map.getCenter().lat;
      const metersPerPixel = 40075016.686 * Math.cos(lat * Math.PI / 180) / Math.pow(2, zoom + 8);
      const radius = Math.round(Math.max(HEAT_MIN_RADIUS_PX,
        Math.min(HEAT_MAX_RADIUS_PX, HEAT_RADIUS_METERS / Math.max(metersPerPixel, 1e-6))) * ratio);
      const stamp = heatStamp(radius);
      const bounds = this._map.getBounds().pad(.1);
      for (const point of points) {
        const plat = Number(point.latitude), plon = Number(point.longitude);
        if (!Number.isFinite(plat) || !Number.isFinite(plon)) continue;
        const ll = L.latLng(plat, plon);
        if (!bounds.contains(ll)) continue;
        const pos = this._map.latLngToContainerPoint(ll);
        ctx.globalAlpha = Math.max(.08, Math.min(1, Number(point.weight || .3)));
        ctx.drawImage(stamp, pos.x * ratio - radius, pos.y * ratio - radius);
      }
      ctx.globalAlpha = 1;
      const image = ctx.getImageData(0, 0, width, height);
      const pixels = image.data;
      const palette = heatPalette();
      for (let i = 3; i < pixels.length; i += 4) {
        const alpha = pixels[i];
        if (!alpha) continue;
        const index = alpha * 4;
        pixels[i - 3] = palette[index];
        pixels[i - 2] = palette[index + 1];
        pixels[i - 1] = palette[index + 2];
        pixels[i] = Math.min(HEAT_MAX_ALPHA, 70 + alpha);
      }
      ctx.putImageData(image, 0, 0);
    }
  });
}

function currentHours() {
  const value = Number($('#mapPeriodHours')?.value || 0);
  return Number.isFinite(value) ? value : 0;
}

function mapInstance() {
  // window.map é o <div id="map"> (id global do DOM) até o Leaflet criar o mapa.
  const map = window.pt2vhfMainMap || window.map || null;
  return typeof map?.on === 'function' ? map : null;
}

function updateCoverageToggle() {
  const input = $('#v142RfCoverageToggle');
  if (input) input.checked = coverageState.enabled;
  const count = $('#v142RfCoverageCount');
  if (count) count.textContent = coverageState.meta ? String(coverageState.meta.points?.length ?? coverageState.points.length) : String(coverageState.points.length);
  const status = $('#v142RfCoverageStatus');
  if (status) {
    if (!coverageState.enabled) status.textContent = tr('desativado','disabled','desactivado','désactivé');
    else if (coverageState.loading) status.textContent = tr('carregando…','loading…','cargando…','chargement…');
    else if (coverageState.meta) status.textContent = tr(
      `${coverageState.points.length} pontos · ${coverageState.meta.rf_stations || 0} estações RF`,
      `${coverageState.points.length} points · ${coverageState.meta.rf_stations || 0} RF stations`,
      `${coverageState.points.length} puntos · ${coverageState.meta.rf_stations || 0} estaciones RF`,
      `${coverageState.points.length} points · ${coverageState.meta.rf_stations || 0} stations RF`
    );
  }
}

function ensureCoverageTreeNode() {
  const tree = $('#mapViewTree');
  if (!tree || $('#v142RfCoverageToggle', tree)) return;
  const node = document.createElement('div');
  node.className = 'map-view-node v142-rf-coverage-node';
  node.dataset.depth = '0';
  node.innerHTML = `
    <div class="map-view-row">
      <span class="map-view-expand-spacer"></span>
      <input id="v142RfCoverageToggle" type="checkbox" class="map-view-checkbox">
      <span class="map-view-label">
        <strong>${tr('Cobertura RF','RF coverage','Cobertura RF','Couverture RF')}</strong>
        <small id="v142RfCoverageStatus"></small>
      </span>
      <span id="v142RfCoverageCount" class="map-view-count">0</span>
    </div>`;
  tree.appendChild(node);
  $('#v142RfCoverageToggle', tree)?.addEventListener('change', event => {
    coverageState.enabled = !!event.target.checked;
    localStorage.setItem('pt2vhf_rf_coverage_enabled', coverageState.enabled ? '1' : '0');
    void refreshCoverage(true);
  });
  updateCoverageToggle();
}

function attachCoverageLayer() {
  const map = mapInstance();
  if (!map || !window.L) return false;
  coverageState.map = map;
  if (!coverageState.layer) {
    const HeatLayer = createHeatLayer();
    if (!HeatLayer) return false;
    coverageState.layer = new HeatLayer(coverageState.points);
  }
  if (coverageState.enabled) {
    if (!map.hasLayer(coverageState.layer)) coverageState.layer.addTo(map);
    coverageState.layer.setPoints(coverageState.points);
  } else if (map.hasLayer(coverageState.layer)) {
    map.removeLayer(coverageState.layer);
  }
  return true;
}

async function refreshCoverage(force=false) {
  ensureCoverageTreeNode();
  if (!coverageState.enabled) {
    attachCoverageLayer();
    updateCoverageToggle();
    return;
  }
  if (coverageState.loading && !force) return;
  coverageState.loading = true;
  updateCoverageToggle();
  try {
    const hours = currentHours();
    const data = await req('/api/v142/rf-coverage?hours='+encodeURIComponent(hours)+'&limit=3500');
    coverageState.points = Array.isArray(data.points) ? data.points : [];
    coverageState.meta = data;
    attachCoverageLayer();
  } catch (error) {
    console.warn('RF coverage:', error);
    const status = $('#v142RfCoverageStatus');
    if (status) status.textContent = tr('erro ao carregar','load error','error al cargar','erreur de chargement');
  } finally {
    coverageState.loading = false;
    updateCoverageToggle();
  }
}

function installCoverage() {
  ensureCoverageTreeNode();
  const tree = $('#mapViewTree');
  if (tree && !tree.dataset.v142Observed) {
    tree.dataset.v142Observed = '1';
    new MutationObserver(() => ensureCoverageTreeNode()).observe(tree,{childList:true});
  }
  $('#mapPeriodHours')?.addEventListener('change', () => {
    if (coverageState.enabled) void refreshCoverage(true);
  });
  $('#mapViewSelectAllButton')?.addEventListener('click', () => {
    coverageState.enabled = true;
    localStorage.setItem('pt2vhf_rf_coverage_enabled', '1');
    setTimeout(() => void refreshCoverage(true), 0);
  });
  $('#mapViewClearAllButton')?.addEventListener('click', () => {
    coverageState.enabled = false;
    localStorage.setItem('pt2vhf_rf_coverage_enabled', '0');
    setTimeout(() => void refreshCoverage(true), 0);
  });
  window.addEventListener('pt2vhf:main-map-ready', () => {
    attachCoverageLayer();
    if (coverageState.enabled) void refreshCoverage(true);
  });
  coverageState.timer = window.setInterval(() => {
    if (coverageState.enabled) void refreshCoverage(false);
  }, 60000);
  let attempts=0;
  const wait = window.setInterval(() => {
    attempts += 1;
    ensureCoverageTreeNode();
    if (attachCoverageLayer() || attempts > 30) {
      clearInterval(wait);
      if (coverageState.enabled) void refreshCoverage(true);
    }
  }, 500);
}

function pick(source, keys) {
  for (const key of keys) {
    const value = source?.[key];
    if (value !== undefined && value !== null && String(value).trim() !== '') return value;
  }
  return '';
}

function aisRows(profile) {
  const p = profile?.source_payload && typeof profile.source_payload === 'object' ? profile.source_payload : {};
  const rows = [];
  const add = (label,value) => { if (value !== '' && value !== null && value !== undefined) rows.push([label,String(value)]); };
  add(tr('Nome da embarcação','Vessel name','Nombre de la embarcación','Nom du navire'), pick(p,['name','vessel_name','ship_name']) || profile?.name);
  add('IMO', pick(p,['imo','imo_number']));
  add(tr('Indicativo','Callsign','Indicativo','Indicatif'), pick(p,['callsign','call_sign','call']));
  add(tr('Tipo de embarcação','Vessel type','Tipo de embarcación','Type de navire'), pick(p,['vessel_type','ship_type','type','class']));
  add(tr('Status de navegação','Navigation status','Estado de navegación','Statut de navigation'), pick(p,['nav_status','navigation_status','navigational_status']));
  add(tr('Velocidade SOG','SOG speed','Velocidad SOG','Vitesse SOG'), pick(p,['sog','speed','speed_over_ground']));
  add('COG', pick(p,['cog','course','course_over_ground']));
  add(tr('Proa','Heading','Proa','Cap'), pick(p,['heading','true_heading']));
  add(tr('Destino','Destination','Destino','Destination'), pick(p,['destination','dest']));
  add('ETA', pick(p,['eta','estimated_arrival']));
  add(tr('Calado','Draught','Calado','Tirant d’eau'), pick(p,['draught','draft']));
  const length = pick(p,['length','length_m']);
  const width = pick(p,['width','beam','width_m']);
  if (length || width) add(tr('Dimensões','Dimensions','Dimensiones','Dimensions'), [length,width].filter(Boolean).join(' × '));
  return {rows, vesselType: pick(p,['vessel_type','ship_type','type','class'])};
}

function illustrativeVesselMarkup(vesselType) {
  return `<div class="v142-ais-illustration" role="img" aria-label="${esc(tr('Imagem ilustrativa de embarcação','Illustrative vessel image','Imagen ilustrativa de embarcación','Image illustrative de navire'))}">
    <svg viewBox="0 0 220 90" aria-hidden="true">
      <path d="M30 57h160l-21 20H54z"></path>
      <path d="M78 54V30h58v24M95 30V17h24v13"></path>
      <circle cx="69" cy="66" r="4"></circle><circle cx="151" cy="66" r="4"></circle>
    </svg>
    <small>${esc(tr('Imagem ilustrativa do tipo','Illustrative image of type','Imagen ilustrativa del tipo','Image illustrative du type'))}: ${esc(vesselType || tr('Embarcação','Vessel','Embarcación','Navire'))}</small>
  </div>`;
}

async function enrichAisPopup(popup) {
  const el = popup?.getElement?.();
  const root = el?.querySelector('.object-friendly-popup');
  if (!root || root.dataset.v142Ais === '1') return;
  const labels = Array.from(root.querySelectorAll('strong'));
  const mmsiLabel = labels.find(node => node.textContent.trim() === 'MMSI');
  const mmsi = mmsiLabel?.nextElementSibling?.textContent?.trim() || '';
  if (!/^\d{7,9}$/.test(mmsi)) return;
  root.dataset.v142Ais = '1';
  try {
    const profile = await req('/api/v110/ais-profile/'+encodeURIComponent(mmsi));
    const {rows,vesselType} = aisRows(profile);
    let section = root.querySelector('.v142-ais-enrichment');
    if (!section) {
      section = document.createElement('section');
      section.className = 'v142-ais-enrichment';
      const technical = root.querySelector('.object-popup-technical');
      root.insertBefore(section, technical || null);
    }
    const dataMarkup = rows.length ? '<div class="v142-ais-grid">'+rows.map(([k,v])=>'<strong>'+esc(k)+'</strong><span>'+esc(v)+'</span>').join('')+'</div>' : '';
    const source = profile?.provider ? '<small class="v142-ais-source">'+esc(tr('Fonte externa','External source','Fuente externa','Source externe'))+': '+esc(profile.provider)+'</small>' : '';
    const existingPhoto = root.querySelector('.v110-ais-photo img');
    const fallback = !existingPhoto && !profile?.image_url ? illustrativeVesselMarkup(vesselType) : '';
    section.innerHTML = dataMarkup + fallback + source;
  } catch (error) {
    console.debug('AIS enrichment unavailable:', error);
  }
}

function installAisEnhancement() {
  const bind = () => {
    const map = mapInstance();
    if (!map || map.__v142AisBound) return false;
    map.__v142AisBound = true;
    map.on('popupopen', event => { void enrichAisPopup(event.popup); });
    return true;
  };
  if (bind()) return;
  window.addEventListener('pt2vhf:main-map-ready', bind);
  const timer=setInterval(()=>{ if(bind()) clearInterval(timer); },700);
}

function boot() {
  // v1.14.51: a cobertura RF é a opção nativa do menu Ver (app.js), que
  // reutiliza este desenhador de mapa de calor; a opção duplicada saiu.
  window.pt2vhfCreateHeatLayer = (() => {
    let HeatLayer = null;
    return () => {
      if (!HeatLayer) HeatLayer = createHeatLayer();
      return HeatLayer;
    };
  })();
  installAisEnhancement();
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
else boot();
})();
