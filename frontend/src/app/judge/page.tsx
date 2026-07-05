"use client";

import { useState, useEffect, useRef } from "react";
import { HolographicBrain } from "@/components/judge/HolographicBrain";
import { Play, RotateCcw, MonitorPlay, Maximize } from "lucide-react";
import { Button } from "@/components/ui/button";
import { motion, AnimatePresence } from "framer-motion";

// Import all scenes
import { Scene0_Opening } from "@/components/judge/scenes/Scene0_Opening";
import { Scene1_Problem } from "@/components/judge/scenes/Scene1_Problem";
import { Scene2_Awakening } from "@/components/judge/scenes/Scene2_Awakening";
import { Scene3_Reasoning } from "@/components/judge/scenes/Scene3_Reasoning";
import { Scene4_Advocacy } from "@/components/judge/scenes/Scene4_Advocacy";
import { Scene5_Judge } from "@/components/judge/scenes/Scene5_Judge";
import { Scene6_Impact } from "@/components/judge/scenes/Scene6_Impact";

export default function CinematicDirector() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTimeMs, setCurrentTimeMs] = useState(0);
  const [activeScene, setActiveScene] = useState(0);
  const DURATION_MS = 60000;
  const containerRef = useRef<HTMLDivElement>(null);

  // Scene timing thresholds
  const SCENES = [
    { id: 0, start: 0, end: 5000 },
    { id: 1, start: 5000, end: 12000 },
    { id: 2, start: 12000, end: 20000 },
    { id: 3, start: 20000, end: 32000 },
    { id: 4, start: 32000, end: 42000 },
    { id: 5, start: 42000, end: 50000 },
    { id: 6, start: 50000, end: 60000 },
  ];

  const reset = () => {
    setIsPlaying(false);
    setCurrentTimeMs(0);
    setActiveScene(0);
  };

  const startPresentation = () => {
    reset();
    setIsPlaying(true);
    if (containerRef.current?.requestFullscreen) {
      containerRef.current.requestFullscreen().catch(() => {});
    }
  };

  // Master animation loop
  useEffect(() => {
    let animationFrameId: number;
    let lastTime = performance.now();

    const loop = (time: number) => {
      if (isPlaying) {
        const delta = time - lastTime;
        setCurrentTimeMs((prev) => {
          const next = prev + delta;
          if (next >= DURATION_MS) {
            setIsPlaying(false);
            return DURATION_MS;
          }
          return next;
        });
      }
      lastTime = time;
      animationFrameId = requestAnimationFrame(loop);
    };

    if (isPlaying) {
      animationFrameId = requestAnimationFrame(loop);
    }
    return () => cancelAnimationFrame(animationFrameId);
  }, [isPlaying]);

  // Determine active scene
  useEffect(() => {
    const current = SCENES.find(
      (s) => currentTimeMs >= s.start && currentTimeMs < s.end
    );
    if (current && current.id !== activeScene) {
      setActiveScene(current.id);
    }
  }, [currentTimeMs, activeScene]);

  // Calculate local progress for the current scene (0 to 1)
  const currentSceneDef = SCENES[activeScene];
  const sceneProgress = Math.min(
    Math.max((currentTimeMs - currentSceneDef.start) / (currentSceneDef.end - currentSceneDef.start), 0),
    1
  );

  return (
    <div 
      ref={containerRef}
      className="h-screen w-screen bg-black text-white overflow-hidden relative font-sans selection:bg-indigo-500/30"
    >
      {/* 3D Core Layer (Base) */}
      <div className="absolute inset-0 z-0">
        <HolographicBrain activeScene={activeScene} sceneProgress={sceneProgress} />
      </div>

      {/* Cinematic UI Overlay (Top) */}
      <div className="absolute inset-0 z-10 pointer-events-none">
        <AnimatePresence mode="wait">
          {activeScene === 0 && <Scene0_Opening key="s0" progress={sceneProgress} />}
          {activeScene === 1 && <Scene1_Problem key="s1" progress={sceneProgress} />}
          {activeScene === 2 && <Scene2_Awakening key="s2" progress={sceneProgress} />}
          {activeScene === 3 && <Scene3_Reasoning key="s3" progress={sceneProgress} />}
          {activeScene === 4 && <Scene4_Advocacy key="s4" progress={sceneProgress} />}
          {activeScene === 5 && <Scene5_Judge key="s5" progress={sceneProgress} />}
          {activeScene === 6 && <Scene6_Impact key="s6" progress={sceneProgress} />}
        </AnimatePresence>
      </div>

      {/* Global Progress Bar (Bottom Edge) */}
      {isPlaying && (
        <div className="absolute bottom-0 left-0 h-1 bg-white/10 z-50 w-full">
          <motion.div 
            className="h-full bg-indigo-500 shadow-[0_0_15px_rgba(99,102,241,0.8)]"
            style={{ width: `${(currentTimeMs / DURATION_MS) * 100}%` }}
          />
        </div>
      )}

      {/* Control Overlay (Only visible when paused/stopped) */}
      <AnimatePresence>
        {!isPlaying && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-50 bg-black/60 backdrop-blur-md flex flex-col items-center justify-center pointer-events-auto"
          >
            <div className="text-center mb-12">
              <h1 className="text-4xl md:text-6xl font-bold tracking-tighter mb-4">SBI VISHWAS</h1>
              <p className="text-white/60 tracking-widest uppercase text-sm md:text-base">Autonomous AI Banking OS</p>
            </div>
            
            <div className="flex items-center gap-6">
              <Button 
                size="lg" 
                className="bg-white text-black hover:bg-white/90 rounded-full px-8 py-6 h-auto text-lg font-medium shadow-[0_0_40px_rgba(255,255,255,0.2)] hover:scale-105 transition-all"
                onClick={startPresentation}
              >
                <MonitorPlay className="mr-3 h-6 w-6" /> Start Cinematic Demo
              </Button>
              
              {currentTimeMs > 0 && (
                <Button 
                  size="icon" 
                  variant="outline" 
                  className="rounded-full h-16 w-16 border-white/20 hover:bg-white/10"
                  onClick={reset}
                >
                  <RotateCcw className="h-6 w-6" />
                </Button>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Hidden exit fullscreen button for convenience */}
      {isPlaying && (
        <button 
          className="absolute top-4 right-4 z-50 text-white/20 hover:text-white/60 p-2 pointer-events-auto"
          onClick={() => setIsPlaying(false)}
        >
          Pause Demo
        </button>
      )}
    </div>
  );
}
