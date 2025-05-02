// OverlayHeatmap.jsx
import React, { useEffect, useState } from "react";
import api from "../api";

export default function OverlayHeatmap({ width = 640, height = 480 }) {
  const [zones, setZones] = useState([]);

  useEffect(() => {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth() + 1;
    api.get(`/analytics/popular-zones/?year=${year}&month=${month}`)
      .then(res => setZones(res.data.zones || []))
      .catch(err => console.error("Zone fetch failed", err));
  }, []);

  const zoneMap = {};
  let maxCount = 0;
  zones.forEach(z => {
    zoneMap[z.zone_id] = z.count;
    if (z.count > maxCount) maxCount = z.count;
  });

  const cellSize = 40;
  const cols = Math.floor(width / cellSize);
  const rows = Math.floor(height / cellSize);

  return (
    <div className="bg-white p-4 rounded-xl shadow w-fit">
      <h2 className="text-lg font-semibold mb-2">Chair-Based Heatmap Grid</h2>
      <div
        className="relative grid gap-1"
        style={{
          gridTemplateColumns: `repeat(${cols}, minmax(32px, 1fr))`,
          width: `${cols * cellSize}px`,
          height: `${rows * cellSize}px`,
        }}
      >
        {Array.from({ length: rows * cols }).map((_, i) => {
          const x = i % cols;
          const y = Math.floor(i / cols);
          const key = `${x}_${y}`;
          const count = zoneMap[key] || 0;
          const opacity = maxCount > 0 ? count / maxCount : 0;

          return (
            <div
              key={key}
              className="flex items-center justify-center text-xs text-white font-semibold rounded"
              style={{
                width: `${cellSize}px`,
                height: `${cellSize}px`,
                backgroundColor: `rgba(255,149,0,${opacity})`,
              }}
              title={`Zone ${key}: ${count} visits`}
            >
              {count > 0 ? count : ""}
            </div>
          );
        })}
      </div>
    </div>
  );
}
