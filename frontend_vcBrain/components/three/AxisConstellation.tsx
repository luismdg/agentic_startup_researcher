"use client";

import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Stars, Trail } from "@react-three/drei";
import { EffectComposer, Bloom } from "@react-three/postprocessing";
import * as THREE from "three";
import type { Trend } from "@/lib/types";

/**
 * The product's central rule rendered as literal geometry: Founder, Market,
 * and Idea-vs-Market are three independent orbits around a shared core.
 * They never intersect, never merge, and are never averaged into one body —
 * because the underlying scores never are either (see AxisSnapshot.tsx /
 * AxisScoreColumn.tsx, which state the same rule in text). This scene is
 * the same rule, just drawn instead of written.
 */

interface AxisInput {
  score: number; // 0-100
  trend: Trend;
}

interface AxisConstellationProps {
  founder: AxisInput;
  market: AxisInput;
  idea: AxisInput;
  height?: number;
}

interface OrbitConfig {
  key: string;
  color: string;
  radius: number;
  speed: number;
  tilt: number;
  phase: number;
  score: number;
  trend: Trend;
}

function trendPulseSpeed(trend: Trend): number {
  if (trend === "up") return 2.6;
  if (trend === "down") return 0.9;
  return 1.6;
}

function Orb({ config }: { config: OrbitConfig }) {
  const meshRef = useRef<THREE.Mesh>(null);
  const groupRef = useRef<THREE.Group>(null);
  const baseScale = 0.32 + (config.score / 100) * 0.34;
  const pulseSpeed = trendPulseSpeed(config.trend);

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime() * config.speed + config.phase;
    const x = config.radius * Math.cos(t);
    const z = config.radius * Math.sin(t);
    const y = Math.sin(t * 1.3) * config.tilt * config.radius;

    if (groupRef.current) {
      groupRef.current.position.set(x, y, z);
    }
    if (meshRef.current) {
      const pulse = 1 + Math.sin(clock.getElapsedTime() * pulseSpeed) * 0.08;
      meshRef.current.scale.setScalar(baseScale * pulse);
      const material = meshRef.current.material as THREE.MeshStandardMaterial;
      material.emissiveIntensity = 1.4 + Math.sin(clock.getElapsedTime() * pulseSpeed) * 0.6;
    }
  });

  return (
    <group ref={groupRef}>
      <Trail width={2.2} length={5} color={config.color} attenuation={(t) => t * t} decay={1}>
        <mesh ref={meshRef}>
          <sphereGeometry args={[1, 48, 48]} />
          <meshStandardMaterial
            color={config.color}
            emissive={config.color}
            emissiveIntensity={1.6}
            roughness={0.25}
            metalness={0.15}
          />
        </mesh>
      </Trail>
    </group>
  );
}

function Core() {
  const ref = useRef<THREE.Mesh>(null);
  useFrame((_, delta) => {
    if (ref.current) {
      ref.current.rotation.y += delta * 0.12;
      ref.current.rotation.x += delta * 0.05;
    }
  });
  return (
    <mesh ref={ref}>
      <icosahedronGeometry args={[0.85, 1]} />
      <meshBasicMaterial color="#7d8bff" wireframe transparent opacity={0.35} />
    </mesh>
  );
}

function Scene({ founder, market, idea }: Omit<AxisConstellationProps, "height">) {
  const orbits = useMemo<OrbitConfig[]>(
    () => [
      { key: "founder", color: "#4fa8ff", radius: 2.1, speed: 0.36, tilt: 0.16, phase: 0, ...founder },
      { key: "market", color: "#ffb84f", radius: 2.7, speed: -0.24, tilt: 0.26, phase: 2.1, ...market },
      { key: "idea", color: "#b98bff", radius: 3.3, speed: 0.19, tilt: 0.34, phase: 4.2, ...idea },
    ],
    [founder, market, idea]
  );

  return (
    <>
      <ambientLight intensity={0.35} />
      <pointLight position={[5, 5, 5]} intensity={40} color="#ffffff" />
      <pointLight position={[-6, -3, -4]} intensity={20} color="#5566ff" />
      <Stars radius={60} depth={40} count={2600} factor={2.4} saturation={0} fade speed={0.4} />
      <Core />
      {orbits.map((cfg) => (
        <Orb key={cfg.key} config={cfg} />
      ))}
      <OrbitControls
        enablePan={false}
        enableZoom={false}
        autoRotate
        autoRotateSpeed={0.6}
        rotateSpeed={0.35}
        minPolarAngle={Math.PI / 3}
        maxPolarAngle={(Math.PI * 2) / 3}
      />
      <EffectComposer>
        <Bloom intensity={1.1} luminanceThreshold={0.15} luminanceSmoothing={0.4} mipmapBlur />
      </EffectComposer>
    </>
  );
}

export default function AxisConstellation({ founder, market, idea, height = 480 }: AxisConstellationProps) {
  return (
    <div style={{ width: "100%", height }}>
      <Canvas camera={{ position: [0, 1.6, 7.5], fov: 45 }} dpr={[1, 1.75]}>
        <Scene founder={founder} market={market} idea={idea} />
      </Canvas>
    </div>
  );
}