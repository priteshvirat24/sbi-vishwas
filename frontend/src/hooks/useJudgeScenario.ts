import { useState, useEffect, useCallback } from 'react';

export type ScenarioEvent = {
  id: string;
  timeMs: number;
  type: 'customer' | 'ai_reasoning' | 'ai_action' | 'system' | 'resolution';
  title: string;
  description: string;
  activeAgents?: string[];
  impactMetrics?: {
    trustScoreChange?: number;
    timeSavedMinutes?: number;
    escalationsPrevented?: number;
  };
};

export type Scenario = {
  id: string;
  title: string;
  description: string;
  durationMs: number;
  events: ScenarioEvent[];
};

export const FORCED_INSURANCE_SCENARIO: Scenario = {
  id: 'forced_insurance',
  title: 'Forced Insurance Resolution',
  description: 'AI detects and overrides a branch employee demanding mandatory insurance.',
  durationMs: 60000,
  events: [
    { id: '1', timeMs: 3000, type: 'customer', title: 'Customer Opens Account', description: 'Customer attempts to open a zero-balance account at Branch 401.' },
    { id: '2', timeMs: 9000, type: 'system', title: 'Branch Employee Block', description: 'Employee insists life insurance is mandatory to proceed.' },
    { id: '3', timeMs: 15000, type: 'customer', title: 'Customer Complains via App', description: '"They straight up told me it\'s mandatory to buy an insurance scheme."' },
    { id: '4', timeMs: 22000, type: 'ai_reasoning', title: 'Journey Tracker Activated', description: 'Linking complaint to active branch visit.', activeAgents: ['journey_tracker'] },
    { id: '5', timeMs: 29000, type: 'ai_reasoning', title: 'Policy Compliance Check', description: 'Searching RBI guidelines regarding forced bundling...', activeAgents: ['policy_compliance', 'knowledge'] },
    { id: '6', timeMs: 36000, type: 'ai_reasoning', title: 'Violation Detected', description: 'RBI Circular explicitly bans forced bundling for savings accounts.', activeAgents: ['policy_compliance'] },
    { id: '7', timeMs: 42000, type: 'ai_action', title: 'Advocacy Triggered', description: 'Proposing instant override of branch requirement.', activeAgents: ['customer_advocate'] },
    { id: '8', timeMs: 48000, type: 'ai_reasoning', title: 'Judge Evaluation', description: 'Evaluating proposed resolution for fairness and empathy.', activeAgents: ['judge'] },
    { id: '9', timeMs: 53000, type: 'ai_action', title: 'Judge Approves', description: 'Resolution scored 98/100. Executing override.', activeAgents: ['judge'] },
    { id: '10', timeMs: 58000, type: 'resolution', title: 'Customer Notified', description: 'Push notification sent: "Your account is now open. Insurance is not required."', activeAgents: ['notification'], impactMetrics: { trustScoreChange: 15, timeSavedMinutes: 160, escalationsPrevented: 1 } },
  ]
};

export const SCENARIOS = [FORCED_INSURANCE_SCENARIO];

export function useJudgeScenario() {
  const [activeScenario, setActiveScenario] = useState<Scenario>(FORCED_INSURANCE_SCENARIO);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTimeMs, setCurrentTimeMs] = useState(0);
  const [pastEvents, setPastEvents] = useState<ScenarioEvent[]>([]);
  const [activeAgents, setActiveAgents] = useState<string[]>([]);
  
  // Aggregate KPIs
  const [kpis, setKpis] = useState({ trustScore: 75, timeSaved: 0, escalationsPrevented: 0 });

  const togglePlay = useCallback(() => setIsPlaying(p => !p), []);
  
  const reset = useCallback(() => {
    setIsPlaying(false);
    setCurrentTimeMs(0);
    setPastEvents([]);
    setActiveAgents([]);
    setKpis({ trustScore: 75, timeSaved: 0, escalationsPrevented: 0 });
  }, []);

  const selectScenario = useCallback((id: string) => {
    const s = SCENARIOS.find(x => x.id === id);
    if (s) {
      setActiveScenario(s);
      reset();
    }
  }, [reset]);

  useEffect(() => {
    let animationFrameId: number;
    let lastTime = performance.now();

    const loop = (time: number) => {
      if (isPlaying) {
        const delta = time - lastTime;
        setCurrentTimeMs(prev => {
          const nextTime = prev + delta;
          
          if (nextTime >= activeScenario.durationMs) {
            setIsPlaying(false);
            return activeScenario.durationMs;
          }
          return nextTime;
        });
      }
      lastTime = time;
      animationFrameId = requestAnimationFrame(loop);
    };

    animationFrameId = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(animationFrameId);
  }, [isPlaying, activeScenario.durationMs]);

  // Update events based on time
  useEffect(() => {
    const currentEvents = activeScenario.events.filter(e => e.timeMs <= currentTimeMs);
    
    // Only update state if events changed to prevent infinite re-renders
    if (currentEvents.length !== pastEvents.length) {
      setPastEvents(currentEvents);
      
      const latestEvent = currentEvents[currentEvents.length - 1];
      if (latestEvent) {
        setActiveAgents(latestEvent.activeAgents || []);
        
        if (latestEvent.impactMetrics) {
          setKpis(prev => ({
            trustScore: prev.trustScore + (latestEvent.impactMetrics?.trustScoreChange || 0),
            timeSaved: prev.timeSaved + (latestEvent.impactMetrics?.timeSavedMinutes || 0),
            escalationsPrevented: prev.escalationsPrevented + (latestEvent.impactMetrics?.escalationsPrevented || 0)
          }));
        }
      }
    }
  }, [currentTimeMs, activeScenario, pastEvents.length]);

  return {
    activeScenario,
    isPlaying,
    currentTimeMs,
    pastEvents,
    activeAgents,
    kpis,
    togglePlay,
    reset,
    selectScenario,
    progress: (currentTimeMs / activeScenario.durationMs) * 100
  };
}
