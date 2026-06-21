import { useRef, useEffect } from 'react';
import { select } from 'd3-selection';
import { scaleLinear, scaleBand } from 'd3-scale';
import { max, median } from 'd3-array';
import { SEGMENT_COLORS, FONTS, CHART_COLORS, formatCompact } from './chartUtils';

export interface RevenueItem {
  name: string;
  type: string;
  revenue: number;
}

interface RevenueChartProps {
  items: RevenueItem[];
  footnote?: string;
}

const MARGIN = { top: 18, right: 72, bottom: 4, left: 120 };
const BAR_HEIGHT = 22;

const COLOR_MAP: Record<string, string> = {
  retailer: SEGMENT_COLORS.retailer,
  distributor: SEGMENT_COLORS.distributor,
  DTC: SEGMENT_COLORS.dtc,
};

export default function RevenueChart({ items, footnote }: RevenueChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const sorted = [...items].sort((a, b) => b.revenue - a.revenue);
  const totalRevenue = sorted.reduce((s, i) => s + i.revenue, 0);
  const top3Revenue = sorted.slice(0, 3).reduce((s, i) => s + i.revenue, 0);
  const top3Pct = totalRevenue > 0 ? ((top3Revenue / totalRevenue) * 100).toFixed(0) : '0';
  const height = MARGIN.top + sorted.length * (BAR_HEIGHT + 6) + MARGIN.bottom;

  useEffect(() => {
    const svg = select(svgRef.current);
    svg.selectAll('*').remove();
    if (sorted.length === 0) return;

    const width = svgRef.current?.parentElement?.clientWidth || 600;
    const innerW = width - MARGIN.left - MARGIN.right;

    svg.attr('width', width).attr('height', height).attr('viewBox', `0 0 ${width} ${height}`);

    const g = svg.append('g').attr('transform', `translate(${MARGIN.left},${MARGIN.top})`);

    const x = scaleLinear()
      .domain([0, max(sorted, d => d.revenue) ?? 1])
      .range([0, innerW]);

    const y = scaleBand<string>()
      .domain(sorted.map(d => d.name))
      .range([0, height - MARGIN.top - MARGIN.bottom])
      .padding(0.22);

    g.selectAll('rect')
      .data(sorted)
      .enter().append('rect')
      .attr('x', 0)
      .attr('y', d => y(d.name)!)
      .attr('width', d => Math.max(2, x(d.revenue)))
      .attr('height', y.bandwidth())
      .attr('fill', d => COLOR_MAP[d.type] ?? CHART_COLORS.axisText);

    g.selectAll('.name')
      .data(sorted)
      .enter().append('text')
      .attr('x', -8)
      .attr('y', d => y(d.name)! + y.bandwidth() / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', 'end')
      .attr('font-family', FONTS.sans)
      .attr('font-size', '12px')
      .attr('fill', CHART_COLORS.axisText)
      .text(d => d.name);

    g.selectAll('.val')
      .data(sorted)
      .enter().append('text')
      .attr('x', d => x(d.revenue) + 4)
      .attr('y', d => y(d.name)! + y.bandwidth() / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', 'start')
      .attr('font-family', FONTS.sans)
      .attr('font-size', '11px')
      .attr('fill', CHART_COLORS.axisText)
      .text(d => formatCompact(d.revenue));

    const medianRevenue = median(sorted, d => d.revenue) ?? 0;
    g.append('line')
      .attr('x1', x(medianRevenue))
      .attr('x2', x(medianRevenue))
      .attr('y1', 0)
      .attr('y2', height - MARGIN.top - MARGIN.bottom)
      .attr('stroke', CHART_COLORS.reference)
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', '6,4');

    g.append('text')
      .attr('x', x(medianRevenue) + 4)
      .attr('y', -2)
      .attr('font-family', FONTS.sans)
      .attr('font-size', '12px')
      .attr('fill', CHART_COLORS.axisText)
      .text('median');
  }, [sorted, height]);

  return (
    <div>
      <svg ref={svgRef} width="100%" height={height} role="img" aria-label="Revenue by channel" style={{ display: 'block', overflow: 'visible' }} />
      {footnote && (
        <p style={{
          fontFamily: FONTS.sans, fontSize: '11px', fontStyle: 'italic',
          color: CHART_COLORS.axisText, marginTop: '4px',
        }}>
          {footnote} · Top 3 = {top3Pct}% of revenue
        </p>
      )}
    </div>
  );
}
