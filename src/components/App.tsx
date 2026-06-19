import { useState, useCallback, useMemo } from 'react';
import channelsData from '../data/channels.json';
import layersData from '../data/layers.json';
import trendsData from '../data/trends.json';
import LandingView from './landing/LandingView';
import SegmentView from './segment/SegmentView';
import ChannelView from './channel/ChannelView';
import TimeFilter from './TimeFilter';
import { FONTS, CHART_COLORS } from './charts/chartUtils';
import {
  SEGMENT_DISPLAY,
  getQuartersForFilter,
  getFilterLabel,
  synthesizeFromTrends,
} from '../lib/computeMetrics';
import type { Channel, Layer, TrendQuarter } from '../lib/computeMetrics';

type DrillState =
  | { level: 'all' }
  | { level: 'segment'; segmentType: string }
  | { level: 'channel'; segmentType: string; channelName: string };

const baseChannels = channelsData as Channel[];
const baseLayers = layersData as Layer[];
const trends = trendsData as TrendQuarter[];
const DEFAULT_TIME_FILTER = 'FY2026';

export default function App() {
  const [drill, setDrill] = useState<DrillState>({ level: 'all' });
  const [timeFilter, setTimeFilter] = useState(DEFAULT_TIME_FILTER);

  const { channels, layers, periodLabel } = useMemo(() => {
    const label = getFilterLabel(timeFilter);
    if (timeFilter === 'full') {
      return { channels: baseChannels, layers: baseLayers, periodLabel: label };
    }
    const quarters = getQuartersForFilter(timeFilter);
    const synth = synthesizeFromTrends(trends, quarters);
    return { channels: synth.channels, layers: synth.layers, periodLabel: label };
  }, [timeFilter]);

  const drillToSegment = useCallback((segmentType: string) => {
    setDrill({ level: 'segment', segmentType });
  }, []);

  const drillToChannel = useCallback((segmentType: string, channelName: string) => {
    setDrill({ level: 'channel', segmentType, channelName });
  }, []);

  const navigateAll = useCallback(() => setDrill({ level: 'all' }), []);

  const navigateSegment = useCallback((segmentType: string) => {
    setDrill({ level: 'segment', segmentType });
  }, []);

  const segmentChannels = useMemo(() => {
    if (drill.level === 'all') return [];
    return channels.filter(c => c.channel_type === drill.segmentType);
  }, [drill, channels]);

  return (
    <div>
      <div style={{ marginBottom: '20px' }}>
        <TimeFilter value={timeFilter} onChange={setTimeFilter} />
      </div>

      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '24px',
        flexWrap: 'wrap',
        gap: '12px',
      }}>
        <nav aria-label="Drill-down breadcrumb" style={{
          fontFamily: FONTS.sans,
          fontSize: '14px',
          color: CHART_COLORS.axisText,
        }}>
          <span
            onClick={navigateAll}
            style={{
              cursor: drill.level !== 'all' ? 'pointer' : 'default',
              color: drill.level !== 'all' ? '#1f2e7a' : CHART_COLORS.ink,
              fontWeight: drill.level === 'all' ? 600 : 400,
              textDecoration: drill.level !== 'all' ? 'underline' : 'none',
            }}
          >
            All Segments
          </span>

          {drill.level !== 'all' && (
            <>
              <span style={{ margin: '0 8px', color: CHART_COLORS.disabled }}>/</span>
              <span
                onClick={() => navigateSegment(drill.segmentType)}
                style={{
                  cursor: drill.level === 'channel' ? 'pointer' : 'default',
                  color: drill.level === 'channel' ? '#1f2e7a' : CHART_COLORS.ink,
                  fontWeight: drill.level === 'segment' ? 600 : 400,
                  textDecoration: drill.level === 'channel' ? 'underline' : 'none',
                }}
              >
                {SEGMENT_DISPLAY[drill.segmentType]}
              </span>
            </>
          )}

          {drill.level === 'channel' && (
            <>
              <span style={{ margin: '0 8px', color: CHART_COLORS.disabled }}>/</span>
              <span style={{ fontWeight: 600, color: CHART_COLORS.ink }}>
                {drill.channelName}
              </span>
            </>
          )}
        </nav>

        <select
          value={drill.level === 'channel' ? drill.channelName : ''}
          onChange={e => {
            const val = e.target.value;
            if (!val) return;
            if (drill.level === 'all') {
              drillToSegment(val);
            } else {
              drillToChannel(drill.segmentType, val);
            }
          }}
          style={{
            fontFamily: FONTS.sans,
            fontSize: '13px',
            padding: '6px 12px',
            border: `1px solid ${CHART_COLORS.gridline}`,
            borderRadius: '2px',
            backgroundColor: 'white',
            color: CHART_COLORS.ink,
            cursor: 'pointer',
          }}
        >
          {drill.level === 'all' ? (
            <>
              <option value="">Select segment…</option>
              <option value="retailer">Retailers</option>
              <option value="distributor">Distributors</option>
              <option value="DTC">DTC</option>
            </>
          ) : (
            <>
              <option value="">Select channel…</option>
              {segmentChannels.map(c => (
                <option key={c.channel_name} value={c.channel_name}>
                  {c.channel_name}
                </option>
              ))}
            </>
          )}
        </select>
      </div>

      {drill.level === 'all' && (
        <LandingView
          channels={channels}
          layers={layers}
          trends={trends}
          baseLayers={baseLayers}
          periodLabel={periodLabel}
          onDrillToSegment={drillToSegment}
        />
      )}

      {drill.level === 'segment' && (
        <SegmentView
          segmentType={drill.segmentType}
          channels={channels}
          layers={layers}
          periodLabel={periodLabel}
          onDrillToChannel={(name) => drillToChannel(drill.segmentType, name)}
        />
      )}

      {drill.level === 'channel' && (
        <ChannelView
          channelName={drill.channelName}
          layers={layers}
          trends={trends}
          periodLabel={periodLabel}
        />
      )}
    </div>
  );
}
