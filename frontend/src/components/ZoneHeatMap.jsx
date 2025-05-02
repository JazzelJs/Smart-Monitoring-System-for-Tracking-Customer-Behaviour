import React, { useEffect, useState } from 'react';
import api from '../api';

export default function ZoneHeatmap({ year, month }) {
  const [zones, setZones] = useState([]);

  useEffect(() => {
    api.get(`/analytics/popular-zones/?year=${year}&month=${month}`)
      .then(res => setZones(res.data.zones || []))
      .catch(err => {
        console.error("Failed to fetch zone data:", err);
        setZones([]);
      });
  }, [year, month]);

  const zoneMap = {};
  let maxRow = 0;
  let maxCol = 0;

  zones.forEach(z => {
    const [col, row] = z.zone.split('_').map(Number);
    maxRow = Math.max(maxRow, row);
    maxCol = Math.max(maxCol, col);
    zoneMap[`${row}_${col}`] = z.count;
  });

  const counts = zones.map(z => z.count);
  const maxCount = Math.max(...counts, 1); // prevent div by zero

  return (
    <div className="w-full">
      <h2 className="text-sm text-gray-500 mb-2">Popular Seating Area Grid</h2>
      <div
        className="grid gap-1 bg-gray-200 p-2 rounded"
        style={{ gridTemplateColumns: `repeat(${maxCol + 1}, minmax(32px, 1fr))` }}
      >
        {Array.from({ length: (maxRow + 1) * (maxCol + 1) }).map((_, i) => {
          const row = Math.floor(i / (maxCol + 1));
          const col = i % (maxCol + 1);
          const key = `${row}_${col}`;
          const count = zoneMap[key] || 0;
          const intensity = count / maxCount;
          const bgColor = intensity === 0
            ? 'bg-gray-100'
            : `bg-[rgba(255,149,0,${intensity.toFixed(2)})]`;

          return (
            <div
              key={key}
              className={`w-8 h-8 text-xs text-white font-bold flex items-center justify-center rounded ${bgColor}`}
              title={`Zone ${key.replace('_', ', ')} - ${count} visits`}
            >
              {count > 0 ? count : ''}
            </div>
          );
        })}
      </div>
    </div>
  );
}
