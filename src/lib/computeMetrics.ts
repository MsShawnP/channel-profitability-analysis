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
  return [
    { label: 'Revenue', value: profile.revenue, type: 'start', runningTotal: profile.revenue },
    { label: 'COGS', value: profile.cogs, type: 'subtract', runningTotal: profile.grossMargin },
    { label: 'Deductions', value: profile.tradeDeductions, type: 'subtract', runningTotal: profile.afterDeductions },
    { label: 'Fines', value: profile.complianceFines, type: 'subtract', runningTotal: profile.afterFines },
    { label: 'Overhead', value: profile.disputeOverhead, type: 'subtract', runningTotal: profile.netContribution },
    { label: 'Net', value: profile.netContribution, type: 'total', runningTotal: profile.netContribution },
  ];
}
