// useLiveSeats.js
import { useState, useEffect } from "react";

export default function useLiveSeats() {
  const [seats, setSeats] = useState({});

  useEffect(() => {
    const fetchSeats = () => {
      fetch("/api/live-seats/")
        .then((res) => res.json())
        .then((data) => setSeats(data.chairs));
    };

    fetchSeats();
    const interval = setInterval(fetchSeats, 5000);
    return () => clearInterval(interval);
  }, []);

  return seats;
}
