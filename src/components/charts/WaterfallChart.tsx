import { useRef, useEffect } from 'react';
import { select } from 'd3-selection';
import { scaleLinear, scaleBand } from 'd3-scale';
import { max } from 'd3-array';
import { WATERFALL_COLORS, CHART_COLORS, FONTS, formatCompact } from './chartUtils';
import type { WaterfallStep } from '../../lib/computeMetrics';

interface WaterfallChartProps {
  steps: WaterfallStep[];
  height?: number;
  footnote?: string;
}

const MARGIN = { top: 4, right: 56, bottom: 4, left: 76 };
const MIN_BAR_WIDTH = 2;

export default function WaterfallChart({ steps, height = 190, footnote }: WaterfallChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current) return;
    const svg = select(svgRef.current);
    const width = svgRef.current.clientWidth || 350;

    svg.attr('viewBox', `0 0 ${width} ${height}`);
    svg.selectAll('*').remove();

    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = height - MARGIN.top - MARGIN.bottom;

    const g = svg.append('g').attr('transform', `translate(${MARGIN.left},${MARGIN.top})`);

    const maxVal = max(steps, d => d.type === 'subtract' ? d.runningTotal + d.value : d.value) || 0;
    const xScale = scaleLinear().domain([0, maxVal]).range([0, innerW]);

    const yScale = scaleBand<string>()
      .domain(steps.map(s => s.label))
      .range([0, innerH])
      .padding(0.2);

    for (let i = 0; i < steps.length - 1; i++) {
      const y1 = (yScale(steps[i].label) || 0) + yScale.bandwidth();
      const y2 = yScale(steps[i + 1].label) || 0;
      g.append('line')
        .attr('x1', xScale(steps[i].runningTotal))
        .attr('x2', xScale(steps[i].runningTotal))
        .attr('y1', y1)
        .attr('y2', y2)
        .attr('stroke', WATERFALL_COLORS.connector)
        .attr('stroke-width', 1)
        .attr('stroke-dasharray', '3,2');
    }

    steps.forEach(step => {
      const y = yScale(step.label) || 0;
      let barX: number, barW: number, color: string;

      if (step.type === 'start') {
        barX = 0;
        barW = xScale(step.value);
        color = WATERFALL_COLORS.revenue;
      } else if (step.type === 'total') {
        barX = 0;
        barW = xScale(step.value);
        color = WATERFALL_COLORS.net;
      } else {
        barX = xScale(step.runningTotal);
        barW = xScale(step.value);
        color = WATERFALL_COLORS.cost;
      }

      g.append('rect')
        .attr('x', barX)
        .attr('y', y)
        .attr('width', Math.max(MIN_BAR_WIDTH, barW))
        .attr('height', yScale.bandwidth())
        .attr('fill', color)
        .attr('rx', 2);

      g.append('text')
        .attr('x', -8)
        .attr('y', y + yScale.bandwidth() / 2)
        .attr('dy', '0.35em')
        .attr('text-anchor', 'end')
        .attr('font-family', FONTS.sans)
        .attr('font-size', '11px')
        .attr('fill', CHART_COLORS.axisText)
        .text(step.label);

      const rightEdge = step.type === 'subtract'
        ? xScale(step.runningTotal + step.value)
        : xScale(step.value);

      g.append('text')
        .attr('x', rightEdge + 4)
        .attr('y', y + yScale.bandwidth() / 2)
        .attr('dy', '0.35em')
        .attr('font-family', FONTS.sans)
        .attr('font-size', '10px')
        .attr('fill', step.type === 'subtract' ? WATERFALL_COLORS.cost : CHART_COLORS.axisText)
        .text(step.type === 'subtract' ? `−${formatCompact(step.value)}` : formatCompact(step.value));
    });
  }, [steps, height]);

  return (
    <div>
      <svg
        ref={svgRef}
        width="100%"
        height={height}
        style={{ display: 'block', overflow: 'visible' }}
        role="img"
        aria-label="Waterfall chart showing margin erosion"
      />
      {footnote && (
        <p style={{
          fontFamily: FONTS.sans,
          fontSize: '11px',
          fontStyle: 'italic',
          color: CHART_COLORS.axisText,
          margin: '4px 0 0',
        }}>
          {footnote}
        </p>
      )}
    </div>
  );
}
