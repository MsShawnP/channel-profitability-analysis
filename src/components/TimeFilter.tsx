import { FISCAL_YEARS } from '../lib/computeMetrics';
import { FONTS, CHART_COLORS } from './charts/chartUtils';

interface TimeFilterProps {
  value: string;
  onChange: (value: string) => void;
  allQuarters: string[];
}

const FY_OPTIONS = [
  { value: 'full', label: 'Full Range' },
  ...FISCAL_YEARS.map(fy => ({ value: fy.label, label: fy.label })),
];

function formatQuarterLabel(q: string): string {
  const [qn, yr] = q.split(' ');
  return `${qn}'${yr.slice(2)}`;
}

export default function TimeFilter({ value, onChange, allQuarters }: TimeFilterProps) {
  const isQuarterSelected = allQuarters.includes(value);
  const parentFy = FISCAL_YEARS.find(f => f.quarters.includes(value));
  const fyValue = isQuarterSelected ? (parentFy?.label ?? value) : value;

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      flexWrap: 'wrap',
    }}>
      <div style={{
        display: 'flex',
        border: `1px solid ${CHART_COLORS.gridline}`,
        borderRadius: '2px',
        overflow: 'hidden',
      }}>
        {FY_OPTIONS.map(opt => {
          const isActive = opt.value === fyValue;
          return (
            <button
              key={opt.value}
              onClick={() => onChange(opt.value)}
              style={{
                fontFamily: FONTS.sans,
                fontSize: '12px',
                padding: '6px 12px',
                border: 'none',
                borderRight: `1px solid ${CHART_COLORS.gridline}`,
                backgroundColor: isActive ? CHART_COLORS.ink : 'transparent',
                color: isActive ? '#ffffff' : CHART_COLORS.axisText,
                cursor: 'pointer',
                fontWeight: isActive ? 600 : 400,
                letterSpacing: '0.3px',
              }}
            >
              {opt.label}
            </button>
          );
        })}
      </div>

      <select
        value={isQuarterSelected ? value : ''}
        onChange={e => {
          const v = e.target.value;
          onChange(v || fyValue || 'full');
        }}
        style={{
          fontFamily: FONTS.sans,
          fontSize: '12px',
          padding: '5px 8px',
          border: `1px solid ${CHART_COLORS.gridline}`,
          borderRadius: '2px',
          backgroundColor: 'white',
          color: CHART_COLORS.ink,
          cursor: 'pointer',
        }}
      >
        <option value="">All quarters</option>
        {allQuarters.map(q => (
          <option key={q} value={q}>{formatQuarterLabel(q)}</option>
        ))}
      </select>
    </div>
  );
}
