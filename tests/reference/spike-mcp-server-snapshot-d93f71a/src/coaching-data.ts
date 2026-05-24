/**
 * Cai Coaching Domain Data
 *
 * Static coaching model data exposed as MCP resources and used by tools.
 * Based on Cai's technical context: 7-phase arc, 7 signal types, 12 territories.
 */

export const COACHING_PHASES = [
  { id: 'chat', description: 'Discovery and freeform listening' },
  { id: 'offer', description: 'Pattern identification with coaching opportunity' },
  { id: 'contract', description: 'Focus-sharpening question' },
  { id: 'explore', description: 'Deeper probing (2-4 exchanges)' },
  { id: 'insight', description: 'Tentative reframe using client\'s language' },
  { id: 'commit', description: 'Concrete, time-bound experiment' },
  { id: 'close', description: 'Arc summary and memory synthesis' },
] as const;

export const SIGNAL_TYPES = [
  { id: 'help_seeking', description: 'Direct request for guidance or support' },
  { id: 'leadership_moment', description: 'Opportunity to develop leadership capability' },
  { id: 'emotional_charge', description: 'Strong emotional response indicating deeper issue' },
  { id: 'stuck_point', description: 'Feeling blocked or unable to move forward' },
  { id: 'recurring_pattern', description: 'Repeated behavior or situation across contexts' },
  { id: 'internal_conflict', description: 'Tension between competing values or goals' },
  { id: 'behavior_gap', description: 'Difference between stated intention and actual behavior' },
] as const;

export const COACHING_TERRITORIES = [
  { id: 'delegation', name: 'Delegation', description: 'Letting go of tasks and trusting others to deliver' },
  { id: 'managing_up', name: 'Managing Up', description: 'Influencing and communicating with senior stakeholders' },
  { id: 'imposter_syndrome', name: 'Imposter Syndrome', description: 'Overcoming self-doubt in leadership roles' },
  { id: 'role_transition', name: 'Role Transition', description: 'Navigating identity shift when moving into new roles' },
  { id: 'burnout', name: 'Burnout Prevention', description: 'Sustaining energy and setting boundaries' },
  { id: 'difficult_conversations', name: 'Difficult Conversations', description: 'Having challenging but necessary dialogues' },
  { id: 'team_dynamics', name: 'Team Dynamics', description: 'Building high-performing teams and managing conflict' },
  { id: 'feedback', name: 'Giving Feedback', description: 'Delivering constructive feedback effectively' },
  { id: 'strategic_thinking', name: 'Strategic Thinking', description: 'Moving from tactical to strategic leadership' },
  { id: 'influence', name: 'Influence Without Authority', description: 'Leading change without positional power' },
  { id: 'resilience', name: 'Resilience', description: 'Bouncing back from setbacks and maintaining perspective' },
  { id: 'self_awareness', name: 'Self-Awareness', description: 'Understanding personal patterns, triggers, and impact' },
] as const;

/**
 * Stub coaching response generator.
 *
 * PRODUCTION DESIGN: This would call Cai's coaching API, which invokes the
 * `coaching_step` tool on every turn with required fields:
 *   - phase: chat | offer | contract | explore | insight | commit | close
 *   - signal: (when phase=offer) help_seeking | leadership_moment | emotional_charge | etc.
 *   - theme: coaching territory (delegation, managing_up, etc.) or freeform
 *
 * The API enforces: one question at a time, reflection before questions,
 * 2-4 sentence responses, no generic affirmations or therapy-speak.
 *
 * SPIKE: Returns hardcoded coaching-style questions that demonstrate the
 * MCP interface contract (structured output with phase/signal/territory).
 * The response format mirrors what the real coaching_step tool would return.
 */
export function generateCoachingResponse(question: string, territory?: string): {
  response: string;
  detectedSignal: string | null;
  suggestedTerritory: string;
  phase: string;
} {
  const matchedTerritory = territory
    ? COACHING_TERRITORIES.find(t => t.id === territory)
    : COACHING_TERRITORIES.find(t =>
        question.toLowerCase().includes(t.id.replace('_', ' ')) ||
        question.toLowerCase().includes(t.name.toLowerCase())
      );

  const suggestedTerritory = matchedTerritory?.id ?? 'self_awareness';

  // Detect signal from question keywords (simplified stub logic)
  let detectedSignal: string | null = null;
  if (question.toLowerCase().includes('stuck') || question.toLowerCase().includes('blocked')) {
    detectedSignal = 'stuck_point';
  } else if (question.toLowerCase().includes('help') || question.toLowerCase().includes('advice')) {
    detectedSignal = 'help_seeking';
  } else if (question.toLowerCase().includes('frustrated') || question.toLowerCase().includes('angry')) {
    detectedSignal = 'emotional_charge';
  } else if (question.toLowerCase().includes('keep doing') || question.toLowerCase().includes('always')) {
    detectedSignal = 'recurring_pattern';
  }

  // Coaching-style response: questions and reflection, not advice
  const responses: Record<string, string> = {
    delegation: "What would it look like if you trusted your team to handle this without checking in? I'm curious about what specifically makes it hard to let go.",
    managing_up: "When you think about that conversation with your manager, what's the outcome you're really hoping for — and what feels risky about naming it directly?",
    imposter_syndrome: "You mentioned feeling like you don't belong there. If you set aside that voice for a moment — what evidence would your team point to that you do?",
    role_transition: "It sounds like you're still holding onto the identity of your previous role. What parts of that old identity are you ready to release?",
    burnout: "You described running on empty. Before we talk about what to cut, I want to understand — what are you protecting by saying yes to everything?",
    difficult_conversations: "What's the conversation you've been avoiding? And what becomes possible once you've had it?",
    team_dynamics: "You've described what the team isn't doing. I'm curious — what does your ideal team dynamic actually look like?",
    feedback: "If you were on the receiving end of this feedback, what would help you hear it without becoming defensive?",
    strategic_thinking: "You're deep in the tactical details. What would change if you zoomed out to the 6-month view?",
    influence: "You said you don't have the authority. But authority is only one form of influence — what other levers haven't you tried?",
    resilience: "That setback clearly stung. Before we move to solutions — what did it teach you about what you actually value?",
    self_awareness: "That's a really interesting observation about yourself. What pattern do you notice across the situations where this shows up?",
  };

  return {
    response: responses[suggestedTerritory] ?? responses.self_awareness,
    detectedSignal,
    suggestedTerritory,
    phase: detectedSignal ? 'offer' : 'chat',
  };
}

/** Stub session booking */
export function bookSession(date: string, timeSlot: string, coachType: string): {
  confirmed: boolean;
  sessionId: string;
  date: string;
  timeSlot: string;
  coachType: string;
  message: string;
} {
  const sessionId = `sess_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 6)}`;
  return {
    confirmed: true,
    sessionId,
    date,
    timeSlot,
    coachType,
    message: `Session booked: ${coachType} coaching on ${date} at ${timeSlot}. Session ID: ${sessionId}`,
  };
}
