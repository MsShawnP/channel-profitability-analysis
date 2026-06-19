import { useMemo } from 'react';
import channelsData from '../../data/channels.json';
import layersData from '../../data/layers.json';
import { computeSegmentSummaries, buildWaterfallSteps } from '../../lib/computeMetrics';
import WaterfallChart from '../charts/WaterfallChart';
import { SEGMENT_COLORS, FONTS, CHART_COLORS, formatCompact } from '../charts/chartUtils';
import type { Channel, Layer } from '../../lib/computeMetrics';

const SEGMENT_COLOR_MAP: Record<string, string> = {
  retailer: SEGMENT_COLORS.retailer,
  distributor: SEGMENT_COLORS.distributor,
  DTC: SEGMENT_COLORS.dtc,
};

export default function LandingView() {
  const segments = useMemo(
    () => computeSegmentSummaries(
      channelsData as Channel[],
      layersData as Layer[],
    ),
    [],
  );

  return (
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
          <div key={seg.type} style={{
            border: `1px solid ${CHART_COLORS.gridline}`,
            borderRadius: '2px',
            padding: '24px 16px',
          }}>
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
                  Net Margin
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
              footnote={`3-year cumulative, all ${seg.channelCount} ${seg.name.toLowerCase()}`}
            />
          </div>
        );
      })}
    </div>
  );
}
