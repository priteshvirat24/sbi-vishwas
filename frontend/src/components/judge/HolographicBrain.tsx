"use client";

import { useRef, useMemo, useEffect } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { PointMaterial, Points } from '@react-three/drei';
import * as THREE from 'three';
import gsap from 'gsap';

function BrainParticles({ isReasoning, intensity }: { isReasoning: boolean, intensity: number }) {
  const ref = useRef<THREE.Points>(null);
  
  const count = 4000;
  const positions = useMemo(() => {
    const p = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const phi = Math.acos(1 - 2 * (i + 0.5) / count);
      const theta = Math.PI * (1 + Math.sqrt(5)) * i;
      const r = 2.5 + (Math.random() - 0.5) * 0.3;
      p[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      p[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      p[i * 3 + 2] = r * Math.cos(phi);
    }
    return p;
  }, [count]);

  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.y = state.clock.elapsedTime * 0.1 * intensity;
      ref.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.2) * 0.1 * intensity;
      
      if (isReasoning) {
        const scale = 1 + Math.sin(state.clock.elapsedTime * 15) * 0.08 * intensity;
        ref.current.scale.set(scale, scale, scale);
      } else {
        ref.current.scale.lerp(new THREE.Vector3(1, 1, 1), 0.05);
      }
    }
  });

  return (
    <Points ref={ref} positions={positions} stride={3} frustumCulled={false}>
      <PointMaterial
        transparent
        color={isReasoning ? "#6366f1" : "#4338ca"}
        size={0.04 * intensity}
        sizeAttenuation={true}
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </Points>
  );
}

function InnerCore({ isReasoning, intensity }: { isReasoning: boolean, intensity: number }) {
  const mesh = useRef<THREE.Mesh>(null);
  const materialRef = useRef<THREE.MeshStandardMaterial>(null);
  
  useFrame((state) => {
    if (mesh.current && materialRef.current) {
      mesh.current.rotation.y += 0.01 * intensity;
      mesh.current.rotation.z += 0.005 * intensity;
      
      if (isReasoning) {
        materialRef.current.emissiveIntensity = 2 + Math.sin(state.clock.elapsedTime * 20) * intensity;
      } else {
        materialRef.current.emissiveIntensity = 0.5 * intensity;
      }
    }
  });

  return (
    <mesh ref={mesh}>
      <sphereGeometry args={[1.5, 64, 64]} />
      <meshStandardMaterial 
        ref={materialRef}
        color="#000000"
        emissive="#4f46e5"
        emissiveIntensity={0.5}
        wireframe={true}
        transparent
        opacity={0.3 * intensity}
      />
    </mesh>
  );
}

function CinematicCamera({ activeScene }: { activeScene: number }) {
  const { camera } = useThree();

  useEffect(() => {
    let targetPos = { x: 0, y: 0, z: 12 };
    let targetLook = { x: 0, y: 0, z: 0 };

    switch (activeScene) {
      case 0: // Opening: Very far, centered
        targetPos = { x: 0, y: 0, z: 15 };
        break;
      case 1: // Problem: Shift right, brain on left
        targetPos = { x: 4, y: 0, z: 10 };
        targetLook = { x: 4, y: 0, z: 0 };
        break;
      case 2: // Awakening: Zoom in close to core
        targetPos = { x: 0, y: 0, z: 6 };
        targetLook = { x: 0, y: 0, z: 0 };
        break;
      case 3: // Reasoning: Shift left, brain on right
        targetPos = { x: -3, y: 0, z: 9 };
        targetLook = { x: -3, y: 0, z: 0 };
        break;
      case 4: // Advocacy: Top down angle
        targetPos = { x: 0, y: 6, z: 8 };
        targetLook = { x: 0, y: 0, z: 0 };
        break;
      case 5: // Judge: Center, medium distance
        targetPos = { x: 0, y: 0, z: 10 };
        break;
      case 6: // Impact: Zoom way out
        targetPos = { x: 0, y: 0, z: 20 };
        break;
    }

    gsap.to(camera.position, {
      x: targetPos.x,
      y: targetPos.y,
      z: targetPos.z,
      duration: 3,
      ease: "power2.inOut"
    });
    
    // Animate LookAt using a dummy object since camera.lookAt isn't easily tweened directly without onUpdate
    const dummy = { x: camera.rotation.x, y: camera.rotation.y, z: camera.rotation.z };
    const lookTarget = new THREE.Vector3(targetLook.x, targetLook.y, targetLook.z);
    
    // Quick hack for smooth lookAt:
    gsap.to(dummy, {
      duration: 3,
      ease: "power2.inOut",
      onUpdate: () => {
        camera.lookAt(lookTarget);
      }
    });

  }, [activeScene, camera]);

  return null;
}

export function HolographicBrain({ activeScene, sceneProgress }: { activeScene: number, sceneProgress: number }) {
  // Logic to determine if brain is "reasoning" (pulsing)
  const isReasoning = [2, 3, 4].includes(activeScene);
  
  // Logic to determine intensity (brighter during awakening and reasoning)
  let intensity = 1;
  if (activeScene === 0) intensity = sceneProgress * 0.8; // Fade in
  if (activeScene === 2) intensity = 1 + sceneProgress; // Surge
  if (activeScene === 6) intensity = 1 - (sceneProgress * 0.5); // Fade down

  return (
    <div className="w-full h-full bg-[#050505]">
      <Canvas camera={{ position: [0, 0, 15], fov: 45 }}>
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1.5 * intensity} color="#6366f1" />
        <pointLight position={[-10, -10, -10]} intensity={0.5 * intensity} color="#38bdf8" />
        
        <BrainParticles isReasoning={isReasoning} intensity={intensity} />
        <InnerCore isReasoning={isReasoning} intensity={intensity} />
        <CinematicCamera activeScene={activeScene} />
      </Canvas>
    </div>
  );
}
