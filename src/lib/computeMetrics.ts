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
  breakdown?: Array<{ label: string; type?: string; amount: number; count?: number }>;
}

export interface Layer {
  id: number;
  label: string;
  subtitle: string;
  channels: LayerChannel[];
}

export interface SegmentSummary {
  name: string;
  type: string;
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
  channelCount: number;
}

export interface WaterfallStep {
  label: string;
  value: number;
  type: 'start' | 'subtract' | 'total';
  runningTotal: number;
}

const SEGMENT_DISPLAY: Record<string, string> = {
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

export function buildWaterfallSteps(segment: SegmentSummary): WaterfallStep[] {
  return [
    { label: 'Revenue', value: segment.revenue, type: 'start', runningTotal: segment.revenue },
    { label: 'COGS', value: segment.cogs, type: 'subtract', runningTotal: segment.grossMargin },
    { label: 'Deductions', value: segment.tradeDeductions, type: 'subtract', runningTotal: segment.afterDeductions },
    { label: 'Fines', value: segment.complianceFines, type: 'subtract', runningTotal: segment.afterFines },
    { label: 'Overhead', value: segment.disputeOverhead, type: 'subtract', runningTotal: segment.netContribution },
    { label: 'Net', value: segment.netContribution, type: 'total', runningTotal: segment.netContribution },
  ];
}
