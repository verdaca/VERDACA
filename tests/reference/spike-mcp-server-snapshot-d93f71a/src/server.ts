/**
 * Cai Coaching MCP Server
 *
 * Exposes Cai's coaching capabilities via Model Context Protocol.
 * Spike implementation: stub backend, real MCP primitives.
 *
 * Tools (model-controlled):
 *   - single-turn-advice: Get coaching response for a leadership question
 *   - book-session: Book a coaching session
 *
 * Resources (application-driven, read-only context):
 *   - coaching://territories: List of 12 coaching territory modules
 *   - coaching://signals: List of 7 signal types Cai detects
 *   - coaching://phases: The 7-phase coaching arc
 *   - coaching://model: Complete coaching model overview
 *
 * Prompts (user-controlled templates):
 *   - coaching-question: Structured prompt for asking a coaching question
 */

import { McpServer, ResourceTemplate } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';
import {
  COACHING_PHASES,
  SIGNAL_TYPES,
  COACHING_TERRITORIES,
  generateCoachingResponse,
  bookSession,
} from './coaching-data.js';

export function createCaiMcpServer(): McpServer {
  const server = new McpServer(
    {
      name: 'cai-coaching',
      version: '0.1.0',
    },
    {
      instructions: [
        'Cai is EZRA\'s AI coaching companion for leadership development.',
        'Coaching responses use questions and reflection — never direct advice.',
        'Use the single-turn-advice tool when users ask leadership or coaching questions.',
        'Use the book-session tool to schedule coaching sessions.',
        'Read coaching://model for a complete overview of the coaching methodology.',
        'Read coaching://territories to understand available coaching domains.',
      ].join(' '),
      capabilities: {
        logging: {},
      },
    }
  );

  // ─── TOOLS ──────────────────────────────────────────────────────────────────

  server.registerTool(
    'single-turn-advice',
    {
      title: 'Coaching Advice',
      description:
        'Get a single-turn coaching response for a leadership or professional development question. ' +
        'Returns a reflective coaching response (questions, not advice), detected signal, suggested territory, and coaching phase.',
      inputSchema: z.object({
        question: z.string().describe('The leadership or professional development question to explore'),
        territory: z
          .string()
          .optional()
          .describe(
            'Optional coaching territory to focus on (e.g., delegation, managing_up, imposter_syndrome). ' +
            'Read coaching://territories for the full list.'
          ),
      }),
      outputSchema: z.object({
        response: z.string().describe('Coaching response using reflective questions'),
        detectedSignal: z.string().nullable().describe('Detected coaching signal, if any'),
        suggestedTerritory: z.string().describe('Coaching territory this question maps to'),
        phase: z.string().describe('Current coaching phase (e.g., chat, offer)'),
      }),
    },
    async ({ question, territory }) => {
      const result = generateCoachingResponse(question, territory);
      return {
        content: [
          {
            type: 'text',
            text: result.response,
          },
        ],
        structuredContent: result,
      };
    }
  );

  server.registerTool(
    'book-session',
    {
      title: 'Book Coaching Session',
      description: 'Book a coaching session with a specific date, time slot, and coach type.',
      inputSchema: z.object({
        date: z.string().describe('Session date in YYYY-MM-DD format'),
        timeSlot: z.string().describe('Preferred time slot (e.g., "10:00-11:00", "afternoon")'),
        coachType: z
          .enum(['ai', 'human', 'hybrid'])
          .default('ai')
          .describe('Type of coaching: ai (Cai), human (EZRA coach), or hybrid'),
      }),
      outputSchema: z.object({
        confirmed: z.boolean(),
        sessionId: z.string(),
        date: z.string(),
        timeSlot: z.string(),
        coachType: z.string(),
        message: z.string(),
      }),
    },
    async ({ date, timeSlot, coachType }) => {
      const result = bookSession(date, timeSlot, coachType);
      return {
        content: [{ type: 'text', text: result.message }],
        structuredContent: result,
      };
    }
  );

  // ─── RESOURCES ──────────────────────────────────────────────────────────────

  server.registerResource(
    'coaching-territories',
    'coaching://territories',
    {
      title: 'Coaching Territories',
      description:
        'The 12 coaching territory modules that guide Cai\'s coaching. ' +
        'Each territory covers a specific leadership development domain.',
      mimeType: 'application/json',
    },
    async (uri) => ({
      contents: [
        {
          uri: uri.href,
          text: JSON.stringify(COACHING_TERRITORIES, null, 2),
        },
      ],
    })
  );

  server.registerResource(
    'coaching-signals',
    'coaching://signals',
    {
      title: 'Coaching Signal Types',
      description:
        'The 7 signal types Cai detects during conversation to identify coaching opportunities.',
      mimeType: 'application/json',
    },
    async (uri) => ({
      contents: [
        {
          uri: uri.href,
          text: JSON.stringify(SIGNAL_TYPES, null, 2),
        },
      ],
    })
  );

  server.registerResource(
    'coaching-phases',
    'coaching://phases',
    {
      title: 'Coaching Arc Phases',
      description:
        'The 7-phase coaching arc tracked via coaching_step tool calls: ' +
        'chat → offer → contract → explore → insight → commit → close.',
      mimeType: 'application/json',
    },
    async (uri) => ({
      contents: [
        {
          uri: uri.href,
          text: JSON.stringify(COACHING_PHASES, null, 2),
        },
      ],
    })
  );

  server.registerResource(
    'coaching-model',
    'coaching://model',
    {
      title: 'Cai Coaching Model Overview',
      description:
        'Complete overview of Cai\'s coaching methodology: phases, signals, territories, ' +
        'and interaction principles. Use this to understand how coaching works before using tools.',
      mimeType: 'application/json',
    },
    async (uri) => ({
      contents: [
        {
          uri: uri.href,
          text: JSON.stringify(
            {
              name: 'Cai Coaching Model',
              description:
                'Cai is EZRA\'s AI coaching companion that guides employees through leadership ' +
                'development using structured coaching methodology rooted in behavioral science.',
              principles: [
                'One question at a time; reflection before questions',
                'Resist premature problem-solving',
                'Concise responses (2-4 sentences)',
                'No generic affirmations or therapy-speak',
                'Challenge delivered with warmth',
              ],
              phases: COACHING_PHASES,
              signals: SIGNAL_TYPES,
              territories: COACHING_TERRITORIES,
            },
            null,
            2
          ),
        },
      ],
    })
  );

  // Dynamic resource: territory detail by ID
  server.registerResource(
    'territory-detail',
    new ResourceTemplate('coaching://territories/{territoryId}', {
      list: async () => ({
        resources: COACHING_TERRITORIES.map((t) => ({
          uri: `coaching://territories/${t.id}`,
          name: t.name,
        })),
      }),
    }),
    {
      title: 'Territory Detail',
      description: 'Detailed information about a specific coaching territory.',
      mimeType: 'application/json',
    },
    async (uri, { territoryId }) => {
      const territory = COACHING_TERRITORIES.find((t) => t.id === territoryId);
      if (!territory) {
        return {
          contents: [{ uri: uri.href, text: JSON.stringify({ error: 'Territory not found' }) }],
        };
      }
      return {
        contents: [{ uri: uri.href, text: JSON.stringify(territory, null, 2) }],
      };
    }
  );

  // ─── PROMPTS ────────────────────────────────────────────────────────────────

  server.registerPrompt(
    'coaching-question',
    {
      title: 'Ask a Coaching Question',
      description:
        'Structured prompt for exploring a leadership challenge with Cai. ' +
        'Reads the coaching model for context, then uses single-turn-advice.',
      argsSchema: {
        question: z.string().describe('Your leadership or professional development question'),
        territory: z.string().optional().describe('Optional: specific coaching territory to focus on'),
      },
    },
    ({ question, territory }) => ({
      messages: [
        {
          role: 'user' as const,
          content: {
            type: 'text' as const,
            text: [
              `I'd like coaching on this question: "${question}"`,
              territory ? `Focus area: ${territory}` : '',
              '',
              'Please:',
              '1. Read the coaching://model resource to understand the coaching methodology',
              '2. Use the single-turn-advice tool with my question',
              '3. Reflect the coaching response back to me naturally, as a coach would',
              '4. Ask one follow-up question to deepen the exploration',
            ]
              .filter(Boolean)
              .join('\n'),
          },
        },
      ],
    })
  );

  return server;
}
