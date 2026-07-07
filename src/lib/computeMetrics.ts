export interface Channel {
  channel_id: string;
  channel_name: string;
  channel_type: string;
  gross_revenue: number;
  total_cogs: number;
  total_deductions: number;
  disputes_filed: number;
  total_deduction_events: number;
}

export interface TrendChannel {
  channel_name: string;
  channel_type: string;
  revenue: number;
  cogs: number;
  deductions: number;
  fines: number;
  overhead: number;
  disputes_filed: number;
  contribution: number;
  margin_pct: number;
}

export interface TrendQuarter {
  quarter: string;
  channels: TrendChannel[];
}

export interface FiscalYear {
  label: string;
  quarters: string[];
}

// FY runs Q2-Q1 (e.g. FY2026 = Q2'25 through Q1'26)
export const FISCAL_YEARS: FiscalYear[] = [
  { label: 'FY2024', quarters: ['Q2 2023', 'Q3 2023', 'Q4 2023', 'Q1 2024'] },
  { label: 'FY2025', quarters: ['Q2 2024', 'Q3 2024', 'Q4 2024', 'Q1 2025'] },
  { label: 'FY2026', quarters: ['Q2 2025', 'Q3 2025', 'Q4 2025', 'Q1 2026'] },
];

export const ALL_QUARTERS = FISCAL_YEARS.flatMap(fy => fy.quarters);

export function getQuartersForFilter(filter: string): string[] {
  if (filter === 'full') return ALL_QUARTERS;
  const fy = FISCAL_YEARS.find(f => f.label === filter);
  if (fy) return fy.quarters;
  return [filter];
}

export function getFilterLabel(filter: string): string {
  if (filter === 'full') return 'Full Range';
  const fy = FISCAL_YEARS.find(f => f.label === filter);
  if (fy) return fy.label;
  const parts = filter.split(' ');
  if (parts.length === 2) {
    return parts[0] + "'" + parts[1].slice(2);
  }
  return 'Full Range';
}

interface TrendAgg {
  type: string;
  revenue: number;
  cogs: number;
  deductions: number;
  fines: number;
  overhead: number;
  disputes_filed: number;
  contribution: number;
}

export function synthesizeFromTrends(
  trends: TrendQuarter[],
  quarters: string[],
): { channels: Channel[]; layers: Layer[] } {
  const filtered = trends.filter(t => quarters.includes(t.quarter));

  const agg = new Map<string, TrendAgg>();
  for (const q of filtered) {
    for (const c of q.channels) {
      const prev = agg.get(c.channel_name) ?? { type: c.channel_type, revenue: 0, cogs: 0, deductions: 0, fines: 0, overhead: 0, disputes_filed: 0, contribution: 0 };
      prev.revenue += c.revenue;
      prev.cogs += c.cogs;
      prev.deductions += c.deductions;
      prev.fines += c.fines;
      prev.overhead += c.overhead;
      prev.disputes_filed += c.disputes_filed;
      prev.contribution += c.contribution;
      agg.set(c.channel_name, prev);
    }
  }

  const channels: Channel[] = Array.from(agg.entries()).map(([name, d]) => ({
    channel_id: name.toLowerCase().replace(/\s+/g, '-'),
    channel_name: name,
    channel_type: d.type,
    gross_revenue: d.revenue,
    total_cogs: d.cogs,
    total_deductions: d.deductions,
    disputes_filed: Math.round(d.disputes_filed),
    total_deduction_events: 0,
  }));

  const layerChannels = (fn: (d: TrendAgg) => number): LayerChannel[] =>
    Array.from(agg.entries()).map(([name, d]) => ({
      channel_name: name,
      channel_type: d.type,
      value: fn(d),
    }));

  const layers: Layer[] = [
    { id: 0, label: 'Revenue', subtitle: '', channels: layerChannels(d => d.revenue) },
    { id: 1, label: 'Gross Margin', subtitle: '', channels: layerChannels(d => d.revenue - d.cogs) },
    { id: 2, label: 'After Deductions', subtitle: '', channels: layerChannels(d => d.contribution + d.fines) },
    { id: 3, label: 'After Fines', subtitle: '', channels: layerChannels(d => d.contribution) },
    { id: 4, label: 'Net Contribution', subtitle: '', channels: layerChannels(d => d.contribution - d.overhead) },
  ];

  return { channels, layers };
}

export interface LayerChannel {
  channel_name: string;
  channel_type: string;
  value: number;
  previous_value?: number;
  breakdown?: BreakdownItem[];
}

export interface Layer {
  id: number;
  label: string;
  subtitle: string;
  channels: LayerChannel[];
}

export interface BreakdownItem {
  label: string;
  type?: string;
  amount: number;
  count?: number;
}

export interface CostProfile {
  revenue: number;
  cogs: number;
  grossMargin: number;
  tradeDeductions: number;
  afterDeductions: number;
  complianceFines: number;
  afterFines: number;
  disputeOverhead: number;
  netContribution: number;
  marginPct: number;
}

export interface SegmentSummary extends CostProfile {
  name: string;
  type: string;
  channelCount: number;
}

export interface ChannelSummary extends CostProfile {
  name: string;
  type: string;
  deductionBreakdown: BreakdownItem[];
  fineBreakdown: BreakdownItem[];
  overheadBreakdown: BreakdownItem[];
}

export interface WaterfallStep {
  label: string;
  value: number;
  type: 'start' | 'subtract' | 'total';
  runningTotal: number;
}

export const SEGMENT_DISPLAY: Record<string, string> = {
  retailer: 'Retailers',
  distributor: 'Distributors',
  DTC: 'DTC',
};

const SEGMENT_ORDER = ['retailer', 'distributor', 'DTC'];

export function computeSegmentSummaries(channels: Channel[], layers: Layer[]): SegmentSummary[] {
  return SEGMENT_ORDER.map(type => {
    const segChannels = channels.filter(c => c.channel_type === type);
    const channelNames = new Set(segChannels.map(c => c.channel_name));

    const sumLayer = (layerId: number) => {
      const layer = layers.find(l => l.id === layerId);
      if (!layer) return 0;
      return layer.channels
        .filter(c => channelNames.has(c.channel_name))
        .reduce((sum, c) => sum + c.value, 0);
    };

    const revenue = sumLayer(0);
    const afterCogs = sumLayer(1);
    const afterDeductions = sumLayer(2);
    const afterFines = sumLayer(3);
    const netContribution = sumLayer(4);

    return {
      name: SEGMENT_DISPLAY[type],
      type,
      revenue,
      cogs: revenue - afterCogs,
      grossMargin: afterCogs,
      tradeDeductions: afterCogs - afterDeductions,
      afterDeductions,
      complianceFines: afterDeductions - afterFines,
      afterFines,
      disputeOverhead: afterFines - netContribution,
      netContribution,
      marginPct: revenue > 0 ? (netContribution / revenue) * 100 : 0,
      channelCount: segChannels.length,
    };
  });
}

export function computeChannelSummary(channelName: string, layers: Layer[]): ChannelSummary | null {
  const findInLayer = (layerId: number) => {
    const layer = layers.find(l => l.id === layerId);
    return layer?.channels.find(c => c.channel_name === channelName) ?? null;
  };

  const l0 = findInLayer(0);
  if (!l0) return null;

  const l1 = findInLayer(1);
  const l2 = findInLayer(2);
  const l3 = findInLayer(3);
  const l4 = findInLayer(4);

  const revenue = l0.value;
  const afterCogs = l1?.value ?? revenue;
  const afterDeductions = l2?.value ?? afterCogs;
  const afterFines = l3?.value ?? afterDeductions;
  const netContribution = l4?.value ?? afterFines;

  return {
    name: channelName,
    type: l0.channel_type,
    revenue,
    cogs: revenue - afterCogs,
    grossMargin: afterCogs,
    tradeDeductions: afterCogs - afterDeductions,
    afterDeductions,
    complianceFines: afterDeductions - afterFines,
    afterFines,
    disputeOverhead: afterFines - netContribution,
    netContribution,
    marginPct: revenue > 0 ? (netContribution / revenue) * 100 : 0,
    deductionBreakdown: (l2?.breakdown ?? []).filter(b => b.amount > 0),
    fineBreakdown: (l3?.breakdown ?? []).filter(b => b.amount > 0),
    overheadBreakdown: (l4?.breakdown ?? []).filter(b => b.amount > 0),
  };
}

export function buildWaterfallSteps(profile: CostProfile): WaterfallStep[] {
  const all: WaterfallStep[] = [
    { label: 'Revenue', value: profile.revenue, type: 'start', runningTotal: profile.revenue },
    { label: 'COGS', value: profile.cogs, type: 'subtract', runningTotal: profile.grossMargin },
    { label: 'Deductions', value: profile.tradeDeductions, type: 'subtract', runningTotal: profile.afterDeductions },
    { label: 'Fines', value: profile.complianceFines, type: 'subtract', runningTotal: profile.afterFines },
    { label: 'Overhead', value: profile.disputeOverhead, type: 'subtract', runningTotal: profile.netContribution },
    { label: 'Net', value: profile.netContribution, type: 'total', runningTotal: profile.netContribution },
  ];
  return all.filter(s => s.type !== 'subtract' || s.value > 0.01);
}
