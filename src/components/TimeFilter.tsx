import { FISCAL_YEARS, type FiscalYear } from '../lib/computeMetrics';
import { FONTS, CHART_COLORS } from './charts/chartUtils';

interface TimeFilterProps {
  value: string;
  onChange: (value: string) => void;
}

const FY_OPTIONS = [
  { value: 'full', label: 'Full Range' },
  ...FISCAL_YEARS.map(fy => ({ value: fy.label, label: fy.label })),
];

function formatQuarterLabel(q: string): string {
  const [qn, yr] = q.split(' ');
  return `${qn}'${yr.slice(2)}`;
}

function getActiveFy(value: string): FiscalYear | null {
  const fy = FISCAL_YEARS.find(f => f.label === value);
  if (fy) return fy;
  for (const f of FISCAL_YEARS) {
    if (f.quarters.includes(value)) return f;
  }
  return null;
}

export default function TimeFilter({ value, onChange }: TimeFilterProps) {
  const activeFy = getActiveFy(value);
  const isQuarterSelected = activeFy?.quarters.includes(value) ?? false;
  const fyValue = isQuarterSelected ? activeFy!.label : value;

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

      {activeFy && (
        <select
          value={isQuarterSelected ? value : ''}
          onChange={e => {
            const v = e.target.value;
            onChange(v || activeFy.label);
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
          {activeFy.quarters.map(q => (
            <option key={q} value={q}>{formatQuarterLabel(q)}</option>
          ))}
        </select>
      )}
    </div>
  );
}
