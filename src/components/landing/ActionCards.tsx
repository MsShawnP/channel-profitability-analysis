import { FONTS, CHART_COLORS, formatCompact, formatPercent } from '../charts/chartUtils';

interface ActionCardData {
  priority: number;
  title: string;
  metric: string;
  metricLabel: string;
  body: string;
}

interface ActionCardsProps {
  retailMarginPct: number;
  distributorMarginPct: number;
  totalOverhead: number;
  walmartOverhead: number;
  walmartDisputes: number;
  costcoMarginPct: number;
  costcoDeductionRate: number;
}

const CARD_BG = '#1a1a1a';

export default function ActionCards({
  retailMarginPct,
  distributorMarginPct,
  totalOverhead,
  walmartOverhead,
  walmartDisputes,
  costcoMarginPct,
  costcoDeductionRate,
}: ActionCardsProps) {
  const marginGap = (retailMarginPct - distributorMarginPct).toFixed(1);

  const cards: ActionCardData[] = [
    {
      priority: 1,
      title: 'Grow retail volume',
      metric: formatPercent(retailMarginPct),
      metricLabel: 'retail contribution margin',
      body: `${marginGap} points above distribution. Deduction profiles are more complex, but per-dollar return more than compensates. Incremental volume here delivers the highest marginal return.`,
    },
    {
      priority: 2,
      title: 'Restructure dispute triage',
      metric: formatCompact(totalOverhead),
      metricLabel: 'annual dispute overhead',
      body: `Walmart alone accounts for ${formatCompact(walmartOverhead)} on ~${walmartDisputes.toLocaleString()} disputes/yr. Automate low-value claims, raise the filing threshold, or eliminate disputes where recovery is negligible.`,
    },
    {
      priority: 3,
      title: 'Review Costco economics',
      metric: formatPercent(costcoMarginPct),
      metricLabel: 'contribution margin — lowest retailer',
      body: `Trade deduction rate of ${costcoDeductionRate.toFixed(1)}% of revenue — highest among retailers. A trade-term renegotiation or promotional rebalancing could close part of the gap.`,
    },
  ];

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(3, 1fr)',
      gap: '24px',
    }}>
      {cards.map(card => (
        <div key={card.priority} style={{
          backgroundColor: CARD_BG,
          borderRadius: '2px',
          padding: '28px 24px',
        }}>
          <div style={{
            fontFamily: FONTS.sans,
            fontSize: '12px',
            color: '#666666', // London-40
            textTransform: 'uppercase' as const,
            letterSpacing: '1px',
            marginBottom: '8px',
          }}>
            Action {card.priority}
          </div>
          <h4 style={{
            fontFamily: FONTS.serif,
            fontSize: '20px',
            fontWeight: 700,
            color: '#ffffff',
            margin: '0 0 16px',
          }}>
            {card.title}
          </h4>
          <div style={{
            fontFamily: FONTS.serif,
            fontSize: '32px',
            fontWeight: 700,
            color: '#ffffff',
            lineHeight: 1.1,
          }}>
            {card.metric}
          </div>
          <div style={{
            fontFamily: FONTS.sans,
            fontSize: '11px',
            color: '#666666', // London-40
            marginBottom: '16px',
          }}>
            {card.metricLabel}
          </div>
          <p style={{
            fontFamily: FONTS.sans,
            fontSize: '13px',
            color: '#b3b3b3',
            lineHeight: 1.5,
            margin: 0,
          }}>
            {card.body}
          </p>
        </div>
      ))}
    </div>
  );
}
