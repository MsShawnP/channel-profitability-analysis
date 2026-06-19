import { useState, useMemo } from 'react';
import { FONTS, CHART_COLORS, SEGMENT_COLORS, formatCompact } from './chartUtils';

export interface MarginRow {
  channel_name: string;
  channel_type: string;
  revenue: number;
  contribution: number;
  margin_pct: number;
  erosion: number;
}

interface MarginTableProps {
  rows: MarginRow[];
  highlight?: string;
  periodLabel?: string;
}

type SortKey = 'channel_name' | 'revenue' | 'contribution' | 'margin_pct' | 'erosion';

const SEGMENT_DOT: Record<string, string> = {
  retailer: SEGMENT_COLORS.retailer,
  distributor: SEGMENT_COLORS.distributor,
  DTC: SEGMENT_COLORS.dtc,
};

const COLUMNS: { key: SortKey; label: string; align: 'left' | 'right' }[] = [
  { key: 'channel_name', label: 'Channel', align: 'left' },
  { key: 'revenue', label: 'Revenue', align: 'right' },
  { key: 'contribution', label: 'Net Contribution', align: 'right' },
  { key: 'margin_pct', label: 'Margin', align: 'right' },
  { key: 'erosion', label: 'Erosion', align: 'right' },
];

export default function MarginTable({ rows, highlight, periodLabel }: MarginTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>('margin_pct');
  const [sortAsc, setSortAsc] = useState(false);

  const sorted = useMemo(() => {
    const copy = [...rows];
    copy.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (typeof av === 'string' && typeof bv === 'string') {
        return sortAsc ? av.localeCompare(bv) : bv.localeCompare(av);
      }
      return sortAsc ? (av as number) - (bv as number) : (bv as number) - (av as number);
    });
    return copy;
  }, [rows, sortKey, sortAsc]);

  const handleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(key === 'channel_name');
    }
  };

  const arrow = (key: SortKey) => {
    if (key !== sortKey) return '';
    return sortAsc ? ' ▲' : ' ▼';
  };

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: FONTS.sans, fontSize: '14px' }}>
        <thead>
          <tr style={{ borderBottom: `2px solid ${CHART_COLORS.gridline}`, textAlign: 'left' }}>
            {COLUMNS.map(col => (
              <th
                key={col.key}
                onClick={() => handleSort(col.key)}
                style={{
                  padding: '8px 12px',
                  fontWeight: 600,
                  textAlign: col.align,
                  cursor: 'pointer',
                  userSelect: 'none',
                  whiteSpace: 'nowrap',
                }}
              >
                {col.label}{arrow(col.key)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map(m => (
            <tr
              key={m.channel_name}
              style={{
                borderBottom: `1px solid ${CHART_COLORS.gridline}`,
                backgroundColor: highlight && m.channel_name === highlight ? '#e4f5f0' : 'transparent',
              }}
            >
              <td style={{ padding: '8px 12px' }}>
                <span style={{
                  display: 'inline-block',
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  backgroundColor: SEGMENT_DOT[m.channel_type] ?? CHART_COLORS.axisText,
                  marginRight: '8px',
                  verticalAlign: 'middle',
                }} />
                {m.channel_name}
              </td>
              <td style={{ padding: '8px 12px', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                {formatCompact(m.revenue)}
              </td>
              <td style={{ padding: '8px 12px', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                {formatCompact(m.contribution)}
              </td>
              <td style={{ padding: '8px 12px', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                {m.margin_pct.toFixed(1)}%
              </td>
              <td style={{ padding: '8px 12px', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                {formatCompact(m.erosion)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {periodLabel && (
        <p style={{
          fontFamily: FONTS.sans, fontSize: '11px', fontStyle: 'italic',
          color: CHART_COLORS.axisText, marginTop: '4px',
        }}>
          {periodLabel} · Click column headers to sort
        </p>
      )}
    </div>
  );
}
