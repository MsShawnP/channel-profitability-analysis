import { useMemo } from 'react';
import { computeSegmentSummaries, computeChannelSummary, buildWaterfallSteps } from '../../lib/computeMetrics';
import WaterfallChart from '../charts/WaterfallChart';
import RevenueChart from '../charts/RevenueChart';
import MarginEvolutionChart from '../charts/MarginEvolutionChart';
import OverheadScatterChart from '../charts/OverheadScatterChart';
import MarginTable from '../charts/MarginTable';
import ActionCards from './ActionCards';
import { SEGMENT_COLORS, FONTS, CHART_COLORS, formatCompact } from '../charts/chartUtils';
import type { Channel, Layer, TrendQuarter } from '../../lib/computeMetrics';

const SEGMENT_COLOR_MAP: Record<string, string> = {
  retailer: SEGMENT_COLORS.retailer,
  distributor: SEGMENT_COLORS.distributor,
  DTC: SEGMENT_COLORS.dtc,
};

interface LandingViewProps {
  channels: Channel[];
  layers: Layer[];
  trends: TrendQuarter[];
  periodLabel: string;
  onDrillToSegment: (segmentType: string) => void;
}

export default function LandingView({ channels, layers, trends, periodLabel, onDrillToSegment }: LandingViewProps) {
  const segments = useMemo(
    () => computeSegmentSummaries(channels, layers),
    [channels, layers],
  );

  const revenueItems = useMemo(
    () => channels.map(c => ({ name: c.channel_name, type: c.channel_type, revenue: c.gross_revenue })),
    [channels],
  );

  const overheadItems = useMemo(() => {
    const l4 = layers.find(l => l.id === 4);
    const l3 = layers.find(l => l.id === 3);
    if (!l4 || !l3) return [];
    return channels.filter(c => c.disputes_filed > 0).map(c => {
      const prev = l3.channels.find(lc => lc.channel_name === c.channel_name)?.value ?? 0;
      const net = l4.channels.find(lc => lc.channel_name === c.channel_name)?.value ?? 0;
      return { name: c.channel_name, type: c.channel_type, disputes: c.disputes_filed, overhead: prev - net, revenue: c.gross_revenue };
    });
  }, [channels, layers]);

  const actionCardData = useMemo(() => {
    const segs = computeSegmentSummaries(channels, layers);
    const retailSeg = segs.find(s => s.type === 'retailer');
    const distSeg = segs.find(s => s.type === 'distributor');
    const costco = computeChannelSummary('Costco', layers);
    const walmart = channels.find(c => c.channel_name === 'Walmart');
    const walmartSummary = computeChannelSummary('Walmart', layers);

    return {
      retailMarginPct: retailSeg?.marginPct ?? 0,
      distributorMarginPct: distSeg?.marginPct ?? 0,
      totalOverhead: segs.reduce((s, seg) => s + seg.disputeOverhead, 0),
      walmartOverhead: walmartSummary?.disputeOverhead ?? 0,
      walmartDisputes: walmart?.disputes_filed ?? 0,
      costcoMarginPct: costco?.marginPct ?? 0,
      costcoDeductionRate: costco ? (costco.tradeDeductions / costco.revenue) * 100 : 0,
    };
  }, [channels, layers]);

  const tableRows = useMemo(() => {
    return channels.map(c => {
      const summary = computeChannelSummary(c.channel_name, layers);
      return {
        channel_name: c.channel_name,
        channel_type: c.channel_type,
        revenue: summary?.revenue ?? c.gross_revenue,
        contribution: summary?.netContribution ?? 0,
        margin_pct: summary?.marginPct ?? 0,
        erosion: (summary?.revenue ?? 0) - (summary?.netContribution ?? 0),
      };
    });
  }, [channels, layers]);

  return (
    <div>
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(3, 1fr)',
      gap: '24px',
      marginTop: '40px',
    }}>
      {segments.map(seg => {
        const steps = buildWaterfallSteps(seg);
        const color = SEGMENT_COLOR_MAP[seg.type];

        return (
          <div
            key={seg.type}
            onClick={() => onDrillToSegment(seg.type)}
            style={{
              background: 'white',
              borderLeft: `4px solid ${color}`,
              borderRadius: '2px',
              padding: '24px 16px',
              cursor: 'pointer',
              transition: 'box-shadow 0.12s ease',
            }}
            onMouseEnter={e => (e.currentTarget.style.boxShadow = '0 2px 12px rgba(0,0,0,0.08)')}
            onMouseLeave={e => (e.currentTarget.style.boxShadow = 'none')}
          >
            <h3 style={{
              fontFamily: FONTS.serif,
              fontSize: '20px',
              fontWeight: 700,
              color: CHART_COLORS.ink,
              margin: '0 0 4px',
            }}>
              {seg.name}
            </h3>
            <p style={{
              fontFamily: FONTS.sans,
              fontSize: '13px',
              color: CHART_COLORS.axisText,
              margin: '0 0 16px',
            }}>
              {seg.channelCount} channel{seg.channelCount !== 1 ? 's' : ''} · {formatCompact(seg.revenue)} revenue
            </p>

            <div style={{ marginBottom: '20px' }}>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'baseline',
                marginBottom: '6px',
              }}>
                <span style={{
                  fontFamily: FONTS.sans,
                  fontSize: '11px',
                  color: CHART_COLORS.axisText,
                  textTransform: 'uppercase' as const,
                  letterSpacing: '0.5px',
                }}>
                  Contribution Margin
                </span>
                <span style={{
                  fontFamily: FONTS.serif,
                  fontSize: '28px',
                  fontWeight: 700,
                  color,
                }}>
                  {seg.marginPct.toFixed(1)}%
                </span>
              </div>
              <div style={{
                height: '8px',
                backgroundColor: CHART_COLORS.gridline,
                borderRadius: '2px',
                overflow: 'hidden',
              }}>
                <div style={{
                  width: `${Math.max(4, seg.marginPct)}%`,
                  height: '100%',
                  backgroundColor: color,
                  borderRadius: '2px',
                }} />
              </div>
            </div>

            <WaterfallChart
              steps={steps}
              height={190}
              footnote={`${periodLabel}, all ${seg.channelCount} ${seg.type === 'DTC' ? 'DTC' : seg.name.toLowerCase()}`}
            />
          </div>
        );
      })}
    </div>

    <div style={{ marginTop: '48px' }}>
      <h3 style={{ fontFamily: FONTS.serif, fontSize: '22px', fontWeight: 700, color: CHART_COLORS.ink, margin: '0 0 12px' }}>
        Revenue by Channel
      </h3>
      <RevenueChart items={revenueItems} footnote={periodLabel} />
    </div>

    <div style={{ marginTop: '48px' }}>
      <h3 style={{ fontFamily: FONTS.serif, fontSize: '22px', fontWeight: 700, color: CHART_COLORS.ink, margin: '0 0 12px' }}>
        Margin Evolution
      </h3>
      <MarginEvolutionChart trends={trends} footnote={`${periodLabel}, all channels`} />
    </div>

    {overheadItems.length > 0 && (
      <div style={{ marginTop: '48px' }}>
        <h3 style={{ fontFamily: FONTS.serif, fontSize: '22px', fontWeight: 700, color: CHART_COLORS.ink, margin: '0 0 12px' }}>
          Dispute Overhead
        </h3>
        <OverheadScatterChart items={overheadItems} footnote={periodLabel} />
      </div>
    )}

    <div style={{ marginTop: '48px' }}>
      <h3 style={{ fontFamily: FONTS.serif, fontSize: '22px', fontWeight: 700, color: CHART_COLORS.ink, margin: '0 0 12px' }}>
        The Full Picture
      </h3>
      <MarginTable rows={tableRows} periodLabel={periodLabel} />
    </div>

    <div style={{ marginTop: '64px' }}>
      <h3 style={{ fontFamily: FONTS.serif, fontSize: '22px', fontWeight: 700, color: CHART_COLORS.ink, margin: '0 0 16px' }}>
        Capital Allocation
      </h3>
      <ActionCards {...actionCardData} />
    </div>
    </div>
  );
}
