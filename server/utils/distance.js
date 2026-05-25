/** 用 Haversine 公式计算两个经纬度点之间的直线距离（米） */
function calcDistance(lat1, lng1, lat2, lng2) {
  const R = 6371000; const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLng = (lng2 - lng1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLng / 2) ** 2;
  return Math.round(R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a)));
}

function findNearestStation(userLat, userLng, stations) {
  if (userLat == null || userLng == null || !Array.isArray(stations)) return null
  let best = null, minDist = Infinity;
  for (const s of stations) {
    if (s.lat == null || s.lng == null) continue // 跳过无效站点
    const d = calcDistance(userLat, userLng, s.lat, s.lng);
    if (isNaN(d)) continue
    if (d < minDist) { minDist = d; best = { station_id: s.id, station_name: s.name, distance: d }; }
  }
  return best;
}

module.exports = { calcDistance, findNearestStation };
