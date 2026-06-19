import { useMemo } from 'react';
import {
  computeSegmentSummaries,
  computeChannelSummary,
  buildWaterfallSteps,
  SEGMENT_DISPLAY,
} from '../../lib/computeMetrics';
import WaterfallChart from '../charts/WaterfallChart';
import { SEGMENT_COLORS, FONTS, CHART_COLORS, formatCompact } from '../charts/chartUtils';
import type { Channel, Layer } from '../../lib/computeMetrics';

interface SegmentViewProps {
  segmentType: string;
  channels: Channel[];
  layers: Layer[];
  onDrillToChannel: (channelName: string) => void;
}

const SEGMENT_COLOR_MAP: Record<string, string> = {
  retailer: SEGMENT_COLORS.retailer,
  distributor: SEGMENT_COLORS.distributor,
  DTC: SEGMENT_COLORS.dtc,
};

export default function SegmentView({ segmentType, channels, layers, onDrillToChannel }: SegmentViewProps) {
  const segment = useMemo(() => {
    const all = computeSegmentSummaries(channels, layers);
    return all.find(s => s.type === segmentType)!;
  }, [segmentType, channels, layers]);

  const channelSummaries = useMemo(() => {
    const segChannels = channels.filter(c => c.channel_type === segmentType);
    return segChannels
      .map(c => computeChannelSummary(c.channel_name, layers))
      .filter(Boolean)
      .sort((a, b) => b!.revenue - a!.revenue) as NonNullable<ReturnType<typeof computeChannelSummary>>[];
  }, [segmentType, channels, layers]);

  const steps = useMemo(() => buildWaterfallSteps(segment), [segment]);
  const color = SEGMENT_COLOR_MAP[segmentType];
  const maxRevenue = Math.max(...channelSummaries.map(c => c.revenue));

  return (
    <div>
      <div style={{ marginBottom: '32px' }}>
        <div style={{
          display: 'flex',
          alignItems: 'baseline',
          gap: '16px',
          marginBottom: '4px',
        }}>
          <h2 style={{
            fontFamily: FONTS.serif,
            fontSize: '28px',
            fontWeight: 700,
            color: CHART_COLORS.ink,
            margin: 0,
          }}>
            {SEGMENT_DISPLAY[segmentType]}
          </h2>
          <span style={{
            fontFamily: FONTS.serif,
            fontSize: '28px',
            fontWeight: 700,
            color,
          }}>
            {segment.marginPct.toFixed(1)}%
          </span>
        </div>
        <p style={{
          fontFamily: FONTS.sans,
          fontSize: '14px',
          color: CHART_COLORS.axisText,
          margin: '0 0 24px',
        }}>
          {segment.channelCount} channels · {formatCompact(segment.revenue)} revenue · {formatCompact(segment.netContribution)} net contribution
        </p>

        <div style={{ maxWidth: '600px' }}>
          <h3 style={{
            fontFamily: FONTS.serif,
            fontSize: '18px',
            fontWeight: 700,
            color: CHART_COLORS.ink,
            margin: '0 0 8px',
          }}>
            Margin Erosion
          </h3>
          <WaterfallChart
            steps={steps}
            height={210}
            footnote={`3-year cumulative across all ${segment.channelCount} ${SEGMENT_DISPLAY[segmentType].toLowerCase()}`}
          />
        </div>
      </div>

      <div>
        <h3 style={{
          fontFamily: FONTS.serif,
          fontSize: '22px',
          fontWeight: 700,
          color: CHART_COLORS.ink,
          margin: '0 0 16px',
        }}>
          Channels
        </h3>
        <div style={{ display: 'grid', gap: '12px' }}>
          {channelSummaries.map(ch => (
            <div
              key={ch.name}
              onClick={() => onDrillToChannel(ch.name)}
              style={{
                display: 'grid',
                gridTemplateColumns: '160px 1fr 100px 80px',
                alignItems: 'center',
                gap: '16px',
                padding: '12px 16px',
                border: `1px solid ${CHART_COLORS.gridline}`,
                borderRadius: '2px',
                cursor: 'pointer',
                transition: 'border-color 0.15s',
              }}
              onMouseEnter={e => (e.currentTarget.style.borderColor = color)}
              onMouseLeave={e => (e.currentTarget.style.borderColor = CHART_COLORS.gridline)}
            >
              <span style={{
                fontFamily: FONTS.sans,
                fontSize: '14px',
                fontWeight: 600,
                color: CHART_COLORS.ink,
              }}>
                {ch.name}
              </span>

              <div style={{
                height: '6px',
                backgroundColor: CHART_COLORS.gridline,
                borderRadius: '2px',
                overflow: 'hidden',
              }}>
                <div style={{
                  width: `${(ch.revenue / maxRevenue) * 100}%`,
                  height: '100%',
                  backgroundColor: color,
                  borderRadius: '2px',
                  opacity: 0.6,
                }} />
              </div>

              <span style={{
                fontFamily: FONTS.sans,
                fontSize: '13px',
                color: CHART_COLORS.axisText,
                textAlign: 'right',
                fontVariantNumeric: 'tabular-nums',
              }}>
                {formatCompact(ch.revenue)}
              </span>

              <span style={{
                fontFamily: FONTS.sans,
                fontSize: '13px',
                fontWeight: 600,
                color,
                textAlign: 'right',
                fontVariantNumeric: 'tabular-nums',
              }}>
                {ch.marginPct.toFixed(1)}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
