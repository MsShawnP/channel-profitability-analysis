import { useRef, useEffect, useState } from 'react';
import { select } from 'd3-selection';
import { scaleLinear, scalePoint } from 'd3-scale';
import { min, max } from 'd3-array';
import { line as d3Line } from 'd3-shape';
import { SEGMENT_COLORS, FONTS, CHART_COLORS, DIM_OPACITY } from './chartUtils';
import type { TrendQuarter } from '../../lib/computeMetrics';

interface MarginEvolutionChartProps {
  trends: TrendQuarter[];
  channelFilter?: string[];
  footnote?: string;
}

const MARGIN = { top: 16, right: 100, bottom: 28, left: 44 };
const HEIGHT = 280;

const COLOR_MAP: Record<string, string> = {
  retailer: SEGMENT_COLORS.retailer,
  distributor: SEGMENT_COLORS.distributor,
  DTC: SEGMENT_COLORS.dtc,
};

function shortQuarter(q: string): string {
  const [qn, yr] = q.split(' ');
  return `${qn}'${yr.slice(2)}`;
}

export default function MarginEvolutionChart({ trends, channelFilter, footnote }: MarginEvolutionChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [isolated, setIsolated] = useState<string | null>(null);

  useEffect(() => {
    const svg = select(svgRef.current);
    svg.selectAll('*').remove();
    if (trends.length === 0) return;

    const width = svgRef.current?.parentElement?.clientWidth ?? 700;
    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = HEIGHT - MARGIN.top - MARGIN.bottom;

    svg.attr('width', width).attr('height', HEIGHT).attr('viewBox', `0 0 ${width} ${HEIGHT}`);

    const g = svg.append('g').attr('transform', `translate(${MARGIN.left},${MARGIN.top})`);

    const quarters = trends.map(t => t.quarter);
    const allChannels = trends[0].channels.map(c => c.channel_name);
    const channels = channelFilter ?? allChannels;

    const x = scalePoint<string>().domain(quarters).range([0, innerW]);
    const allMargins = trends.flatMap(t => t.channels.filter(c => channels.includes(c.channel_name)).map(c => c.margin_pct));
    const yMin = Math.floor((min(allMargins) ?? 40) / 5) * 5;
    const yMax = Math.ceil((max(allMargins) ?? 90) / 5) * 5;
    const y = scaleLinear().domain([yMin, yMax]).range([innerH, 0]);

    const gridTicks = y.ticks(6);
    g.selectAll('.grid')
      .data(gridTicks)
      .enter().append('line')
      .attr('x1', 0).attr('x2', innerW)
      .attr('y1', d => y(d)).attr('y2', d => y(d))
      .attr('stroke', CHART_COLORS.gridline);

    g.selectAll('.grid-label')
      .data(gridTicks)
      .enter().append('text')
      .attr('x', -8).attr('y', d => y(d))
      .attr('dy', '0.35em').attr('text-anchor', 'end')
      .attr('font-family', FONTS.sans).attr('font-size', '10px')
      .attr('fill', CHART_COLORS.axisText)
      .text(d => `${d}%`);

    const xLabels = quarters.length <= 8 ? quarters : quarters.filter((_, i) => i % 2 === 0 || i === quarters.length - 1);
    g.selectAll('.x-label')
      .data(xLabels)
      .enter().append('text')
      .attr('x', d => x(d)!)
      .attr('y', innerH + 18)
      .attr('text-anchor', 'middle')
      .attr('font-family', FONTS.sans).attr('font-size', '10px')
      .attr('fill', CHART_COLORS.axisText)
      .text(d => shortQuarter(d));

    const lineFn = d3Line<{ quarter: string; margin: number }>()
      .x(d => x(d.quarter)!)
      .y(d => y(d.margin));

    for (const ch of channels) {
      const series = trends.map(t => {
        const c = t.channels.find(tc => tc.channel_name === ch);
        return { quarter: t.quarter, margin: c?.margin_pct ?? 0 };
      });

      const chType = trends[0].channels.find(c => c.channel_name === ch)?.channel_type ?? 'retailer';
      const color = COLOR_MAP[chType] ?? CHART_COLORS.axisText;
      const opacity = isolated ? (ch === isolated ? 1 : DIM_OPACITY) : 0.8;

      g.append('path')
        .datum(series)
        .attr('fill', 'none')
        .attr('stroke', color)
        .attr('stroke-width', isolated === ch ? 2.5 : 1.5)
        .attr('stroke-opacity', opacity)
        .attr('d', lineFn)
        .style('cursor', 'pointer')
        .on('click', () => setIsolated(prev => prev === ch ? null : ch));

      const last = series[series.length - 1];
      g.append('text')
        .attr('x', innerW + 6)
        .attr('y', y(last.margin))
        .attr('dy', '0.35em')
        .attr('font-family', FONTS.sans)
        .attr('font-size', '10px')
        .attr('fill', color)
        .attr('opacity', opacity)
        .style('cursor', 'pointer')
        .text(`${ch} ${last.margin.toFixed(1)}%`)
        .on('click', () => setIsolated(prev => prev === ch ? null : ch));
    }
  }, [trends, channelFilter, isolated]);

  return (
    <div>
      <svg ref={svgRef} role="img" aria-label="Margin evolution over time" style={{ display: 'block' }} />
      {footnote && (
        <p style={{
          fontFamily: FONTS.sans, fontSize: '11px', fontStyle: 'italic',
          color: CHART_COLORS.axisText, marginTop: '4px',
        }}>
          {footnote}{isolated ? ` · Showing ${isolated}` : ' · Click a line to isolate'}
        </p>
      )}
    </div>
  );
}
