import { useMemo } from 'react';
import { computeChannelSummary, buildWaterfallSteps, SEGMENT_DISPLAY } from '../../lib/computeMetrics';
import WaterfallChart from '../charts/WaterfallChart';
import MarginEvolutionChart from '../charts/MarginEvolutionChart';
import { FONTS, CHART_COLORS, WATERFALL_COLORS, formatCompact } from '../charts/chartUtils';
import type { Layer, BreakdownItem, TrendQuarter } from '../../lib/computeMetrics';

interface ChannelViewProps {
  channelName: string;
  layers: Layer[];
  trends: TrendQuarter[];
  periodLabel: string;
}

function BreakdownSection({ title, items, color }: { title: string; items: BreakdownItem[]; color: string }) {
  if (items.length === 0) return null;
  const maxAmount = Math.max(...items.map(i => i.amount));
  const total = items.reduce((s, i) => s + i.amount, 0);

  return (
    <div style={{ marginBottom: '32px' }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'baseline',
        marginBottom: '12px',
      }}>
        <h3 style={{
          fontFamily: FONTS.serif,
          fontSize: '18px',
          fontWeight: 700,
          color: CHART_COLORS.ink,
          margin: 0,
        }}>
          {title}
        </h3>
        <span style={{
          fontFamily: FONTS.sans,
          fontSize: '14px',
          fontWeight: 600,
          color,
        }}>
          {formatCompact(total)}
        </span>
      </div>
      <div style={{ display: 'grid', gap: '8px' }}>
        {items.map(item => (
          <div key={item.label} style={{
            display: 'grid',
            gridTemplateColumns: '140px 1fr 70px',
            alignItems: 'center',
            gap: '12px',
          }}>
            <span style={{
              fontFamily: FONTS.sans,
              fontSize: '13px',
              color: CHART_COLORS.axisText,
            }}>
              {item.label}
            </span>
            <div style={{
              height: '6px',
              backgroundColor: CHART_COLORS.gridline,
              borderRadius: '2px',
              overflow: 'hidden',
            }}>
              <div style={{
                width: `${(item.amount / maxAmount) * 100}%`,
                height: '100%',
                backgroundColor: color,
                borderRadius: '2px',
              }} />
            </div>
            <span style={{
              fontFamily: FONTS.sans,
              fontSize: '12px',
              color: CHART_COLORS.axisText,
              textAlign: 'right',
              fontVariantNumeric: 'tabular-nums',
            }}>
              {formatCompact(item.amount)}
              {item.count != null && (
                <span style={{ color: CHART_COLORS.disabled, marginLeft: '4px' }}>
                  ({item.count})
                </span>
              )}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function ChannelView({ channelName, layers, trends, periodLabel }: ChannelViewProps) {
  const summary = useMemo(
    () => computeChannelSummary(channelName, layers),
    [channelName, layers],
  );

  if (!summary) {
    return <p style={{ fontFamily: FONTS.sans, color: CHART_COLORS.axisText }}>Channel not found.</p>;
  }

  const steps = buildWaterfallSteps(summary);

  return (
    <div>
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
          {channelName}
        </h2>
        <span style={{
          fontFamily: FONTS.sans,
          fontSize: '14px',
          color: CHART_COLORS.axisText,
        }}>
          {SEGMENT_DISPLAY[summary.type]}
        </span>
      </div>

      <div style={{
        display: 'flex',
        gap: '32px',
        marginBottom: '32px',
        fontFamily: FONTS.sans,
      }}>
        <div>
          <span style={{ fontSize: '12px', color: CHART_COLORS.axisText, textTransform: 'uppercase' as const, letterSpacing: '0.5px' }}>Revenue</span>
          <div style={{ fontSize: '22px', fontWeight: 700, color: CHART_COLORS.ink, fontFamily: FONTS.serif }}>{formatCompact(summary.revenue)}</div>
        </div>
        <div>
          <span style={{ fontSize: '12px', color: CHART_COLORS.axisText, textTransform: 'uppercase' as const, letterSpacing: '0.5px' }}>Net Contribution</span>
          <div style={{ fontSize: '22px', fontWeight: 700, color: CHART_COLORS.ink, fontFamily: FONTS.serif }}>{formatCompact(summary.netContribution)}</div>
        </div>
        <div>
          <span style={{ fontSize: '12px', color: CHART_COLORS.axisText, textTransform: 'uppercase' as const, letterSpacing: '0.5px' }}>Margin</span>
          <div style={{ fontSize: '22px', fontWeight: 700, color: WATERFALL_COLORS.net, fontFamily: FONTS.serif }}>{summary.marginPct.toFixed(1)}%</div>
        </div>
      </div>

      <div style={{ marginBottom: '40px' }}>
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
          footnote={periodLabel}
        />
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
        gap: '32px',
      }}>
        <BreakdownSection
          title={channelName === 'DTC' ? 'Channel Operating Costs' : 'Trade Deductions'}
          items={summary.deductionBreakdown}
          color={WATERFALL_COLORS.cost}
        />
        <BreakdownSection
          title={channelName === 'DTC' ? 'Returns & Damages' : 'Compliance Fines'}
          items={summary.fineBreakdown}
          color={WATERFALL_COLORS.cost}
        />
        {summary.overheadBreakdown.length > 0 && (
          <BreakdownSection
            title="Dispute Overhead"
            items={summary.overheadBreakdown}
            color={WATERFALL_COLORS.cost}
          />
        )}
      </div>

      {channelName === 'DTC' && (
        <p style={{
          fontFamily: FONTS.sans,
          fontSize: '12px',
          color: CHART_COLORS.axisText,
          marginTop: '24px',
          lineHeight: 1.5,
          fontStyle: 'italic',
        }}>
          DTC margin excludes customer acquisition costs (paid social, email, influencer), which are classified as marketing expenses rather than channel costs.
        </p>
      )}

      <div style={{ marginTop: '48px' }}>
        <h3 style={{
          fontFamily: FONTS.serif,
          fontSize: '18px',
          fontWeight: 700,
          color: CHART_COLORS.ink,
          margin: '0 0 8px',
        }}>
          Margin Trend
        </h3>
        <MarginEvolutionChart
          trends={trends}
          channelFilter={[channelName]}
          footnote={periodLabel}
        />
      </div>
    </div>
  );
}
