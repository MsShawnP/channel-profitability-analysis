import { useRef, useEffect } from 'react';
import { select } from 'd3-selection';
import { scaleLinear, scaleSqrt } from 'd3-scale';
import { max } from 'd3-array';
import { SEGMENT_COLORS, FONTS, CHART_COLORS, formatCompact } from './chartUtils';

export interface OverheadItem {
  name: string;
  type: string;
  disputes: number;
  overhead: number;
  revenue: number;
}

interface OverheadScatterChartProps {
  items: OverheadItem[];
  footnote?: string;
}

const MARGIN = { top: 16, right: 24, bottom: 36, left: 56 };
const HEIGHT = 300;

const COLOR_MAP: Record<string, string> = {
  retailer: SEGMENT_COLORS.retailer,
  distributor: SEGMENT_COLORS.distributor,
  DTC: SEGMENT_COLORS.dtc,
};

export default function OverheadScatterChart({ items, footnote }: OverheadScatterChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const filtered = items.filter(i => i.disputes > 0);

  useEffect(() => {
    const svg = select(svgRef.current);
    svg.selectAll('*').remove();
    if (filtered.length === 0) return;

    const width = svgRef.current?.parentElement?.clientWidth || 600;
    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = HEIGHT - MARGIN.top - MARGIN.bottom;

    svg.attr('width', width).attr('height', HEIGHT).attr('viewBox', `0 0 ${width} ${HEIGHT}`);

    const g = svg.append('g').attr('transform', `translate(${MARGIN.left},${MARGIN.top})`);

    const x = scaleLinear()
      .domain([0, (max(filtered, d => d.disputes) ?? 100) * 1.1])
      .range([0, innerW]);

    const y = scaleLinear()
      .domain([0, (max(filtered, d => d.overhead) ?? 1000) * 1.15])
      .range([innerH, 0]);

    const r = scaleSqrt()
      .domain([0, max(filtered, d => d.revenue) ?? 1])
      .range([6, 28]);

    const gridTicks = y.ticks(5);
    g.selectAll('.grid')
      .data(gridTicks)
      .enter().append('line')
      .attr('x1', 0).attr('x2', innerW)
      .attr('y1', d => y(d)).attr('y2', d => y(d))
      .attr('stroke', CHART_COLORS.gridline);

    g.selectAll('.y-label')
      .data(gridTicks)
      .enter().append('text')
      .attr('x', -8).attr('y', d => y(d))
      .attr('dy', '0.35em').attr('text-anchor', 'end')
      .attr('font-family', FONTS.sans).attr('font-size', '10px')
      .attr('fill', CHART_COLORS.axisText)
      .text(d => formatCompact(d));

    const xTicks = x.ticks(5);
    g.selectAll('.x-label')
      .data(xTicks)
      .enter().append('text')
      .attr('x', d => x(d)).attr('y', innerH + 18)
      .attr('text-anchor', 'middle')
      .attr('font-family', FONTS.sans).attr('font-size', '10px')
      .attr('fill', CHART_COLORS.axisText)
      .text(d => d.toString());

    g.append('text')
      .attr('x', innerW / 2).attr('y', innerH + 32)
      .attr('text-anchor', 'middle')
      .attr('font-family', FONTS.sans).attr('font-size', '11px')
      .attr('fill', CHART_COLORS.axisText)
      .text('Disputes filed');

    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -innerH / 2).attr('y', -44)
      .attr('text-anchor', 'middle')
      .attr('font-family', FONTS.sans).attr('font-size', '11px')
      .attr('fill', CHART_COLORS.axisText)
      .text('Overhead ($)');

    g.selectAll('circle')
      .data(filtered)
      .enter().append('circle')
      .attr('cx', d => x(d.disputes))
      .attr('cy', d => y(d.overhead))
      .attr('r', d => r(d.revenue))
      .attr('fill', d => COLOR_MAP[d.type] ?? CHART_COLORS.axisText)
      .attr('fill-opacity', 0.65)
      .attr('stroke', d => COLOR_MAP[d.type] ?? CHART_COLORS.axisText)
      .attr('stroke-width', 1);

    g.selectAll('.dot-label')
      .data(filtered)
      .enter().append('text')
      .attr('x', d => x(d.disputes))
      .attr('y', d => y(d.overhead) - r(d.revenue) - 4)
      .attr('text-anchor', 'middle')
      .attr('font-family', FONTS.sans).attr('font-size', '10px')
      .attr('fill', CHART_COLORS.ink)
      .text(d => d.name);
  }, [filtered]);

  return (
    <div>
      <svg ref={svgRef} width="100%" height={HEIGHT} role="img" aria-label="Dispute overhead scatter" style={{ display: 'block', overflow: 'visible' }} />
      {footnote && (
        <p style={{
          fontFamily: FONTS.sans, fontSize: '11px', fontStyle: 'italic',
          color: CHART_COLORS.axisText, marginTop: '4px',
        }}>
          {footnote} · Bubble size = channel revenue
        </p>
      )}
    </div>
  );
}
