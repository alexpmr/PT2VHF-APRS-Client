/* Maidenhead QTH locator: 4/6/8/10 characters, cell-center conversion (WGS84). */
(function (root) {
  'use strict';
  const LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  const stepsLon = [20, 2, 2 / 24, 2 / 240, 2 / 5760];
  const stepsLat = [10, 1, 1 / 24, 1 / 240, 1 / 5760];

  function normalize(value) {
    return String(value == null ? '' : value).trim().toUpperCase();
  }

  function decode(value) {
    const grid = normalize(value);
    if (!/^(?:[A-R]{2}[0-9]{2})(?:[A-X]{2}(?:[0-9]{2}(?:[A-X]{2})?)?)?$/.test(grid)) {
      throw new Error('Grid Locator inválido. Use 4, 6, 8 ou 10 caracteres (ex.: GH64).');
    }
    let lon = -180, lat = -90;
    for (let index = 0; index < grid.length / 2; index++) {
      const x = grid[index * 2], y = grid[index * 2 + 1];
      const vx = index % 2 === 0 ? LETTERS.indexOf(x) : Number(x);
      const vy = index % 2 === 0 ? LETTERS.indexOf(y) : Number(y);
      lon += vx * stepsLon[index];
      lat += vy * stepsLat[index];
    }
    const position = grid.length / 2 - 1;
    const lonSize = stepsLon[position], latSize = stepsLat[position];
    return {
      locator: grid,
      latitude: lat + latSize / 2,
      longitude: lon + lonSize / 2,
      longitudeSpan: lonSize,
      latitudeSpan: latSize
    };
  }

  function encode(latitude, longitude, precision = 6) {
    const lat = Number(latitude), lon = Number(longitude);
    if (!Number.isFinite(lat) || !Number.isFinite(lon) ||
        lat < -90 || lat > 90 || lon < -180 || lon > 180 ||
        ![4, 6, 8, 10].includes(Number(precision))) {
      throw new Error('Latitude, longitude ou tamanho do Grid Locator inválido.');
    }
    const eps = 1e-10;
    let x = Math.max(0, Math.min(360 - eps, lon + 180));
    let y = Math.max(0, Math.min(180 - eps, lat + 90));
    let grid = '';
    for (let i = 0; i < precision / 2; i++) {
      const a = Math.min(i === 0 ? 17 : i % 2 === 0 ? 23 : 9, Math.floor(x / stepsLon[i] + 1e-10));
      const b = Math.min(i === 0 ? 17 : i % 2 === 0 ? 23 : 9, Math.floor(y / stepsLat[i] + 1e-10));
      grid += i % 2 === 0 ? LETTERS[a] + LETTERS[b] : String(a) + String(b);
      x = Math.max(0, x - a * stepsLon[i]);
      y = Math.max(0, y - b * stepsLat[i]);
    }
    return grid;
  }

  const api = { normalize, decode, encode };
  root.PT2VHFMaidenhead = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : (typeof globalThis !== 'undefined' ? globalThis : this));
