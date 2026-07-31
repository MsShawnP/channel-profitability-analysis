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
const allDataQuarters = trends.map(t => t.quarter);
// Default to the most recent COMPLETE fiscal year. FY2026 is still in progress
// (Q1'26 is a stub) and would total ~$20.3M; FY2025 is a full four quarters
// (~$25.7M combined, Q2'24–Q1'25). The hero cites CY2025 combined ~$25.3M —
// the canonical default period — with its window named inline.
const DEFAULT_TIME_FILTER = 'FY2025';

export default function App() {
  const [drill, setDrill] = useState<DrillState>({ level: 'all' });
  const [timeFilter, setTimeFilter] = useState(DEFAULT_TIME_FILTER);

  const { channels, layers, periodLabel, trendsLabel, filteredTrends } = useMemo(() => {
    const label = getFilterLabel(timeFilter);
    if (timeFilter === 'full') {
      // channels/layers are annual averages, but the trend charts still plot
      // quarterly series — label them by their real window, not the average.
      return { channels: baseChannels, layers: baseLayers, periodLabel: label, trendsLabel: 'Quarterly, Q1 2023 – Q1 2026', filteredTrends: trends };
    }
    const quarters = getQuartersForFilter(timeFilter);
    const synth = synthesizeFromTrends(trends, quarters);
    const ft = trends.filter(t => quarters.includes(t.quarter));
    return { channels: synth.channels, layers: synth.layers, periodLabel: label, trendsLabel: label, filteredTrends: ft };
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
        <TimeFilter value={timeFilter} onChange={setTimeFilter} allQuarters={allDataQuarters} />
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
          fontSize: '15px',
          color: CHART_COLORS.axisText,
          display: 'flex',
          alignItems: 'center',
          gap: '0',
        }}>
          <span
            onClick={navigateAll}
            role="button"
            tabIndex={0}
            onKeyDown={e => { if (e.key === 'Enter') navigateAll(); }}
            style={{
              cursor: drill.level !== 'all' ? 'pointer' : 'default',
              color: drill.level !== 'all' ? '#1f2e7a' : CHART_COLORS.ink,
              fontWeight: drill.level === 'all' ? 600 : 500,
              textDecoration: drill.level !== 'all' ? 'underline' : 'none',
            }}
          >
            {drill.level !== 'all' ? '← All Channels' : 'All Channels'}
          </span>

          {drill.level !== 'all' && (
            <>
              <span style={{ margin: '0 8px', color: CHART_COLORS.disabled }}>{'›'}</span>
              <span
                onClick={() => navigateSegment(drill.segmentType)}
                role="button"
                tabIndex={0}
                onKeyDown={e => { if (e.key === 'Enter') navigateSegment(drill.segmentType); }}
                style={{
                  cursor: drill.level === 'channel' ? 'pointer' : 'default',
                  color: drill.level === 'channel' ? '#1f2e7a' : CHART_COLORS.ink,
                  fontWeight: drill.level === 'segment' ? 600 : 500,
                  textDecoration: drill.level === 'channel' ? 'underline' : 'none',
                }}
              >
                {SEGMENT_DISPLAY[drill.segmentType]}
              </span>
            </>
          )}

          {drill.level === 'channel' && (
            <>
              <span style={{ margin: '0 8px', color: CHART_COLORS.disabled }}>{'›'}</span>
              <span style={{ fontWeight: 600, color: CHART_COLORS.ink }}>
                {drill.channelName}
              </span>
            </>
          )}
        </nav>

        <select
          value=""
          onChange={e => {
            const val = e.target.value;
            if (!val) return;
            if (val.startsWith('seg:')) {
              drillToSegment(val.slice(4));
            } else {
              const segType = drill.level !== 'all' ? drill.segmentType : '';
              if (segType) drillToChannel(segType, val);
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
          <option value="">Drill into…</option>
          <option value="seg:retailer">Retailers</option>
          <option value="seg:distributor">Distributors</option>
          <option value="seg:DTC">DTC</option>
          {drill.level !== 'all' && segmentChannels.length > 0 && (
            <optgroup label={`${SEGMENT_DISPLAY[drill.segmentType]} channels`}>
              {segmentChannels.map(c => (
                <option key={c.channel_name} value={c.channel_name}>
                  {c.channel_name}
                </option>
              ))}
            </optgroup>
          )}
        </select>
      </div>

      {drill.level === 'all' && (
        <LandingView
          channels={channels}
          layers={layers}
          trends={filteredTrends}
          periodLabel={periodLabel}
          trendsLabel={trendsLabel}
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
          trends={filteredTrends}
          periodLabel={periodLabel}
          trendsLabel={trendsLabel}
        />
      )}
    </div>
  );
}
