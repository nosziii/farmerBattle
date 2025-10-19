import type { ExpeditionSummary } from '../types/expeditions';

export type ExpeditionPhase = 'outbound' | 'returning' | 'completed';

export interface ExpeditionWithProgress extends ExpeditionSummary {
  outboundProgress: number;
  returnProgress: number;
  currentPhase: ExpeditionPhase;
  etaSeconds: number;
}

const clamp = (value: number) => Math.min(1, Math.max(0, value));

const ensureUtc = (value: string): string => {
  return /(Z|z|[+-]\d{2}:?\d{2})$/.test(value) ? value : `${value}Z`;
};

const toDate = (value: string | null | undefined): number | null => {
  if (!value) return null;
  const parsed = new Date(ensureUtc(value));
  return Number.isNaN(parsed.getTime()) ? null : parsed.getTime();
};

export const decorateExpedition = (
  expedition: ExpeditionSummary,
  nowMs: number,
): ExpeditionWithProgress => {
  const departedAt = toDate(expedition.departed_at);
  const arriveAt = toDate(expedition.arrive_at);
  const resolvedAt = toDate(expedition.resolved_at) ?? arriveAt;
  const returnAt = toDate(expedition.return_at);

  const outboundTotal = departedAt != null && arriveAt != null ? Math.max(1, arriveAt - departedAt) : null;
  const outboundElapsed =
    outboundTotal !== null && departedAt !== null ? Math.min(outboundTotal, Math.max(0, nowMs - departedAt)) : 0;

  const returningTotal =
    expedition.status !== 'outbound' && resolvedAt != null && returnAt != null
      ? Math.max(1, returnAt - resolvedAt)
      : null;
  const returningElapsed =
    returningTotal !== null && resolvedAt !== null ? Math.min(returningTotal, Math.max(0, nowMs - resolvedAt)) : 0;

  let etaSeconds = 0;
  let currentPhase: ExpeditionPhase = expedition.status;

  if (expedition.status === 'outbound' && outboundTotal !== null && departedAt !== null) {
    const remaining = Math.max(0, (arriveAt ?? departedAt) - nowMs);
    etaSeconds = Math.round(remaining / 1000);
  } else if (expedition.status === 'returning' && returningTotal !== null && resolvedAt !== null) {
    const remaining = Math.max(0, (returnAt ?? resolvedAt) - nowMs);
    etaSeconds = Math.round(remaining / 1000);
  } else {
    currentPhase = 'completed';
    etaSeconds = 0;
  }

  const outboundProgress =
    outboundTotal !== null ? (expedition.status === 'outbound' ? clamp(outboundElapsed / outboundTotal) : 1) : 0;
  const returnProgress =
    returningTotal !== null
      ? expedition.status === 'returning'
        ? clamp(returningElapsed / returningTotal)
        : expedition.status === 'completed'
        ? 1
        : 0
      : 0;

  return {
    ...expedition,
    outboundProgress,
    returnProgress,
    currentPhase,
    etaSeconds,
  };
};

export const formatDuration = (seconds: number): string => {
  if (seconds <= 0 || Number.isNaN(seconds)) {
    return '0s';
  }
  const mins = Math.floor(seconds / 60);
  const hrs = Math.floor(mins / 60);
  const remMins = mins % 60;
  const remSecs = seconds % 60;
  if (hrs > 0) {
    return `${hrs}h ${remMins}m`;
  }
  if (mins > 0) {
    return `${mins}m ${remSecs}s`;
  }
  return `${remSecs}s`;
};
