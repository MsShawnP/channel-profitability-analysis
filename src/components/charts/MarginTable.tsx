interface MarginRow {
  channel_name: string;
  revenue: number;
  contribution: number;
  margin_pct: string;
  erosion: number;
}

interface MarginTableProps {
  rows: MarginRow[];
  highlight?: string;
}

const fmt = (v: number) =>
  new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
    notation: 'compact',
  }).format(v);

export default function MarginTable({ rows, highlight }: MarginTableProps) {
  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: "var(--font-sans, 'Source Sans 3', sans-serif)", fontSize: '14px' }}>
        <thead>
          <tr style={{ borderBottom: '2px solid #d9d9d9', textAlign: 'left' }}>
            <th style={{ padding: '8px 12px', fontWeight: 600 }}>Channel</th>
            <th style={{ padding: '8px 12px', fontWeight: 600, textAlign: 'right' }}>Revenue</th>
            <th style={{ padding: '8px 12px', fontWeight: 600, textAlign: 'right' }}>Net Contribution</th>
            <th style={{ padding: '8px 12px', fontWeight: 600, textAlign: 'right' }}>Margin</th>
            <th style={{ padding: '8px 12px', fontWeight: 600, textAlign: 'right' }}>Erosion</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((m) => (
            <tr key={m.channel_name} style={{ borderBottom: '1px solid #d9d9d9', backgroundColor: highlight && m.channel_name === highlight ? '#e4f5f0' : 'transparent' }}>
              <td style={{ padding: '8px 12px' }}>{m.channel_name}</td>
              <td style={{ padding: '8px 12px', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{fmt(m.revenue)}</td>
              <td style={{ padding: '8px 12px', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{fmt(m.contribution)}</td>
              <td style={{ padding: '8px 12px', textAlign: 'right', fontVariantNumeric: 'tabular-nums', color: parseFloat(m.margin_pct) < 85 ? '#cc100a' : '#333333' }}>{m.margin_pct}%</td>
              <td style={{ padding: '8px 12px', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{fmt(m.erosion)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
