import { toast } from 'react-toastify';

export function checkAndNotify({ occupancyPercent, peakHour }) {
  if (occupancyPercent >= 90) {
    toast.error('⚠️ Occupancy is above 90%!');
  }

  if (peakHour) {
    const [startHourStr] = peakHour.split(" - "); // e.g., "12:00"
    const now = new Date();
    const currentHour = now.getHours();

    const startHour = parseInt(startHourStr.split(":")[0]);

    const diff = startHour - currentHour;

    if (diff === 0) {
      toast.warn("⏰ Peak hour is happening now!");
    } else if (diff > 0 && diff <= 1) {
      toast.info("⚠️ Peak hour is approaching in less than 1 hour.");
    }
  }
}
