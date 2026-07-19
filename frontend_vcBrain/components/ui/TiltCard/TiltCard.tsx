"use client";

import { useRef, type ReactNode, type MouseEvent } from "react";
import { motion, useMotionValue, useMotionValueEvent, useSpring, useTransform } from "framer-motion";
import styles from "./TiltCard.module.css";

interface TiltCardProps {
  children: ReactNode;
  className?: string;
  maxTilt?: number;
}

/** Wraps its children in a glass panel that tilts toward the cursor in 3D,
 * spring-settling back to flat on mouse-leave. Purely cosmetic — no layout
 * or interaction logic lives here, so it's safe to drop around any panel. */
export default function TiltCard({ children, className, maxTilt = 8 }: TiltCardProps) {
  const ref = useRef<HTMLDivElement>(null);
  const x = useMotionValue(0.5);
  const y = useMotionValue(0.5);
  const springX = useSpring(x, { stiffness: 150, damping: 18 });
  const springY = useSpring(y, { stiffness: 150, damping: 18 });
  const rotateX = useTransform(springY, [0, 1], [maxTilt, -maxTilt]);
  const rotateY = useTransform(springX, [0, 1], [-maxTilt, maxTilt]);

  // Drives the CSS spotlight in TiltCard.module.css (.tilt::before) via
  // custom properties, set directly on the node -- same tracking data as
  // the tilt, but this way the glow never triggers a React re-render.
  useMotionValueEvent(springX, "change", (v) => {
    ref.current?.style.setProperty("--mx", `${v * 100}%`);
  });
  useMotionValueEvent(springY, "change", (v) => {
    ref.current?.style.setProperty("--my", `${v * 100}%`);
  });

  function handleMouseMove(e: MouseEvent<HTMLDivElement>) {
    const rect = ref.current?.getBoundingClientRect();
    if (!rect) return;
    x.set((e.clientX - rect.left) / rect.width);
    y.set((e.clientY - rect.top) / rect.height);
  }

  function handleMouseLeave() {
    x.set(0.5);
    y.set(0.5);
  }

  return (
    <motion.div
      ref={ref}
      className={`${styles.tilt} ${className ?? ""}`}
      style={{ rotateX, rotateY, transformPerspective: 900 }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {children}
    </motion.div>
  );
}