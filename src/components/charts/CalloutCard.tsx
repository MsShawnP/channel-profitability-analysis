import { formatCompact } from './chartUtils';

export interface LayerBreakdownItem {
  label: string;
  amount: number;
}

interface CalloutCardProps {
  channelName: string;
  totalValue: number;
  breakdown?: LayerBreakdownItem[];
}

/**
 * Dark detail card rendered above the chart when a channel is pinned.
 * Shows channel name, total value, and line-item breakdown.
 */
export default function CalloutCard({ channelName, totalValue, breakdown }: CalloutCardProps) {
  return (
    <div style={styles.card}>
      <div style={styles.header}>
        <span style={styles.channelName}>{channelName}</span>
        <span style={styles.totalValue}>{formatCompact(totalValue)}</span>
      </div>
      {breakdown && breakdown.length > 0 && (
        <div style={styles.breakdownSection}>
          {breakdown.map((item, index) => (
            <div key={item.label} style={styles.breakdownRow}>
              {index > 0 && <div style={styles.divider} />}
              <div style={styles.rowContent}>
                <span style={styles.itemLabel}>{item.label}</span>
                <span style={styles.itemAmount}>{formatCompact(item.amount)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  card: {
    background: '#1a1a1a',
    borderRadius: '2px',
    padding: '20px 24px',
    marginBottom: '16px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'baseline',
    marginBottom: '12px',
  },
  channelName: {
    color: '#ffffff',
    fontFamily: "var(--font-sans, 'Source Sans 3', 'Source Sans Pro', 'Helvetica Neue', Helvetica, Arial, sans-serif)",
    fontSize: '18px',
    fontWeight: 600,
  },
  totalValue: {
    color: '#ffffff',
    fontFamily: "var(--font-serif, 'Playfair Display', Georgia, 'Times New Roman', serif)",
    fontSize: '28px',
    fontWeight: 700,
  },
  breakdownSection: {
    marginTop: '8px',
  },
  breakdownRow: {
    display: 'flex',
    flexDirection: 'column' as const,
  },
  divider: {
    height: '1px',
    background: 'rgba(255, 255, 255, 0.12)',
    margin: '8px 0',
  },
  rowContent: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  itemLabel: {
    color: '#ededed',
    fontFamily: "var(--font-sans, 'Source Sans 3', 'Source Sans Pro', 'Helvetica Neue', Helvetica, Arial, sans-serif)",
    fontSize: '14px',
    fontWeight: 400,
  },
  itemAmount: {
    color: '#d8d8d8',
    fontFamily: "var(--font-sans, 'Source Sans 3', 'Source Sans Pro', 'Helvetica Neue', Helvetica, Arial, sans-serif)",
    fontSize: '14px',
    fontWeight: 400,
  },
};
