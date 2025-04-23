import { useEffect, useState } from 'react';
import api from '../api';

export default function useDetectionStatus(pollInterval = 2000) {
  const [isDetecting, setIsDetecting] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      api.get('/analytics/detection-status/')
        .then(res => setIsDetecting(res.data.is_detecting))
        .catch(err => console.error("Detection status error:", err));
    }, pollInterval);

    return () => clearInterval(interval);
  }, [pollInterval]);

  return isDetecting;
}
