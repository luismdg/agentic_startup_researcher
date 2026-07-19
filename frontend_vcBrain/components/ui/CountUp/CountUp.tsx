"use client";

import { useEffect, useRef } from "react";
import { animate, useMotionValue, useMotionValueEvent } from "framer-motion";

interface CountUpProps {
  value: number;
  duration?: number;
  format?: (n: number) => string;
  className?: string;
}

/** Animates a number from 0 (or its previous value) up to `value`. Writes
 * straight to the DOM node via a motion value listener instead of React
 * state, so a fast-ticking counter never triggers a re-render per frame. */
export default function CountUp({ value, duration = 1.1, format, className }: CountUpProps) {
  const spanRef = useRef<HTMLSpanElement>(null);
  const motionValue = useMotionValue(0);
  const render = (n: number) => (format ? format(n) : Math.round(n).toString());

  useEffect(() => {
    const controls = animate(motionValue, value, { duration, ease: "easeOut" });
    return () => controls.stop();
  }, [value, duration, motionValue]);

  useMotionValueEvent(motionValue, "change", (latest) => {
    if (spanRef.current) spanRef.current.textContent = render(latest);
  });

  return (
    <span ref={spanRef} className={className}>
      {render(0)}
    </span>
  );
}