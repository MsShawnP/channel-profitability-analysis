import { useRef, useEffect, useState, useCallback, useMemo } from 'react';
import { select } from 'd3-selection';
import { scaleLinear, scalePoint } from 'd3-scale';
import { min, max, mean } from 'd3-array';
import { axisBottom, axisLeft } from 'd3-axis';
import { line, curveMonotoneX } from 'd3-shape';
import { easeCubicOut } from 'd3-ease';
import 'd3-transition';
import { getSequentialColor, getOpacity, DIM_OPACITY, CHART_COLORS, FONTS } from './chartUtils';

interface TrendChannelData {
  channel_name: string;
  channel_type: string;
  revenue: number;
  cogs: number;
  deductions: number;
  contribution: number;
  margin_pct: number;
}

interface TrendQuarter {
  quarter: string;
  channels: TrendChannelData[];
}

export interface TrendChartProps {
  data: TrendQuarter[];
  channelType: string;
  label: string;
}

const MARGIN = { top: 12, right: 140, bottom: 40, left: 50 };
const CHART_HEIGHT = 300;
const GRIDLINE_COLOR = CHART_COLORS.gridline;
const TRANSITION_DURATION = 200;
const DOT_RADIUS = 3;
const MIN_LABEL_GAP = 13;

export default function TrendChart({ data, channelType, label }: TrendChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [pinnedChannel, setPinnedChannel] = useState<string | null>(null);

  const channelNames = useMemo(() => {
    const names = new Set<string>();
    data.forEach(q => q.channels
      .filter(c => c.channel_type === channelType)
      .forEach(c => names.add(c.channel_name))
    );
    return [...names].sort((a, b) => {
      const avgA = mean(data, q => q.channels.find(c => c.channel_name === a)?.margin_pct) || 0;
      const avgB = mean(data, q => q.channels.find(c => c.channel_name === b)?.margin_pct) || 0;
      return avgB - avgA;
    });
  }, [data, channelType]);

  const series = useMemo(() => channelNames.map((name, i) => ({
    name,
    color: getSequentialColor(i, channelNames.length),
    values: data.map(q => ({
      quarter: q.quarter,
      margin: q.channels.find(c => c.channel_name === name)?.margin_pct || 0,
    })),
  })), [data, channelNames]);

  const handleClick = useCallback((name: string) => {
    setPinnedChannel(current => current === name ? null : name);
  }, []);

  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mq.matches);
    const handler = (e: MediaQueryListEvent) => setPrefersReducedMotion(e.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  useEffect(() => {
    if (!svgRef.current) return;
    const svg = select(svgRef.current);
    const chartWidth = svgRef.current.clientWidth || 700;

    svg.attr('viewBox', `0 0 ${chartWidth} ${CHART_HEIGHT}`);

    const innerWidth = chartWidth - MARGIN.left - MARGIN.right;
    const innerHeight = CHART_HEIGHT - MARGIN.top - MARGIN.bottom;

    let g = svg.select<SVGGElement>('g.chart-inner');
    if (g.empty()) g = svg.append('g').attr('class', 'chart-inner');
    g.attr('transform', `translate(${MARGIN.left},${MARGIN.top})`);

    const quarters = data.map(q => q.quarter);
    const xScale = scalePoint<string>()
      .domain(quarters)
      .range([0, innerWidth])
      .padding(0.1);

    const allMargins = series.flatMap(s => s.values.map(v => v.margin));
    const yMin = Math.floor((min(allMargins) || 70) / 5) * 5 - 2;
    const yMax = Math.ceil((max(allMargins) || 100) / 5) * 5 + 2;

    const yScale = scaleLinear()
      .domain([yMin, yMax])
      .range([innerHeight, 0]);

    // Horizontal gridlines
    const yTicks = yScale.ticks(5);
    const gridlines = g.selectAll<SVGLineElement, number>('line.gridline')
      .data(yTicks, d => String(d));
    gridlines.join(
      enter => enter.append('line')
        .attr('class', 'gridline')
        .attr('x1', 0).attr('x2', innerWidth)
        .attr('y1', d => yScale(d)).attr('y2', d => yScale(d))
        .attr('stroke', GRIDLINE_COLOR).attr('stroke-width', 1),
      update => update.attr('y1', d => yScale(d)).attr('y2', d => yScale(d)).attr('x2', innerWidth),
      exit => exit.remove()
    );

    const duration = prefersReducedMotion ? 0 : TRANSITION_DURATION;

    const lineGen = line<{ quarter: string; margin: number }>()
      .x(d => xScale(d.quarter) || 0)
      .y(d => yScale(d.margin))
      .curve(curveMonotoneX);

    // Lines
    const lines = g.selectAll<SVGPathElement, typeof series[0]>('path.trend-line')
      .data(series, d => d.name);

    lines.join(
      enter => enter.append('path')
        .attr('class', 'trend-line')
        .attr('d', d => lineGen(d.values))
        .attr('fill', 'none')
        .attr('stroke', d => d.color)
        .attr('stroke-width', 2.5)
        .style('cursor', 'pointer')
        .style('opacity', d => !pinnedChannel ? 1 : d.name === pinnedChannel ? 1 : DIM_OPACITY)
        .on('click', (_, d) => handleClick(d.name)),
      update => {
        const u = update.attr('d', d => lineGen(d.values)).attr('stroke', d => d.color);
        if (duration > 0) {
          u.transition().duration(duration).ease(easeCubicOut)
            .style('opacity', d => !pinnedChannel ? 1 : d.name === pinnedChannel ? 1 : DIM_OPACITY);
        } else {
          u.style('opacity', d => !pinnedChannel ? 1 : d.name === pinnedChannel ? 1 : DIM_OPACITY);
        }
        return u;
      },
      exit => exit.remove()
    );

    // Dots
    g.selectAll<SVGGElement, typeof series[0]>('g.dot-group')
      .data(series, d => d.name)
      .join(
        enter => enter.append('g').attr('class', 'dot-group'),
        update => update,
        exit => exit.remove()
      )
      .each(function(seriesData) {
        const opacity = !pinnedChannel ? 1 : seriesData.name === pinnedChannel ? 1 : DIM_OPACITY;
        select(this)
          .selectAll<SVGCircleElement, { quarter: string; margin: number }>('circle')
          .data(seriesData.values, d => d.quarter)
          .join(
            enter => enter.append('circle')
              .attr('cx', d => xScale(d.quarter) || 0)
              .attr('cy', d => yScale(d.margin))
              .attr('r', DOT_RADIUS)
              .attr('fill', seriesData.color)
              .style('cursor', 'pointer')
              .style('opacity', opacity)
              .on('click', () => handleClick(seriesData.name)),
            update => update
              .attr('cx', d => xScale(d.quarter) || 0)
              .attr('cy', d => yScale(d.margin))
              .style('opacity', opacity),
            exit => exit.remove()
          );
      });

    // End labels with collision avoidance
    const lastQuarter = quarters[quarters.length - 1];
    const labelPositions = series.map(s => ({
      name: s.name,
      color: s.color,
      margin: s.values[s.values.length - 1].margin,
      y: yScale(s.values[s.values.length - 1].margin),
    }));
    labelPositions.sort((a, b) => a.y - b.y);
    for (let i = 1; i < labelPositions.length; i++) {
      if (labelPositions[i].y - labelPositions[i - 1].y < MIN_LABEL_GAP) {
        labelPositions[i].y = labelPositions[i - 1].y + MIN_LABEL_GAP;
      }
    }
    const labelYMap = new Map(labelPositions.map(p => [p.name, p.y]));

    const endLabels = g.selectAll<SVGTextElement, typeof labelPositions[0]>('text.end-label')
      .data(labelPositions, d => d.name);

    endLabels.join(
      enter => enter.append('text')
        .attr('class', 'end-label')
        .attr('x', (xScale(lastQuarter) || 0) + 8)
        .attr('y', d => labelYMap.get(d.name) || d.y)
        .attr('dy', '0.35em')
        .attr('font-family', FONTS.sans)
        .attr('font-size', '11px')
        .attr('fill', d => d.color)
        .style('cursor', 'pointer')
        .text(d => `${d.name} ${d.margin}%`)
        .style('opacity', d => !pinnedChannel ? 1 : d.name === pinnedChannel ? 1 : DIM_OPACITY)
        .on('click', (_, d) => handleClick(d.name)),
      update => {
        const u = update
          .attr('x', (xScale(lastQuarter) || 0) + 8)
          .attr('y', d => labelYMap.get(d.name) || d.y)
          .text(d => `${d.name} ${d.margin}%`);
        if (duration > 0) {
          u.transition().duration(duration).ease(easeCubicOut)
            .style('opacity', d => !pinnedChannel ? 1 : d.name === pinnedChannel ? 1 : DIM_OPACITY);
        } else {
          u.style('opacity', d => !pinnedChannel ? 1 : d.name === pinnedChannel ? 1 : DIM_OPACITY);
        }
        return u;
      },
      exit => exit.remove()
    );

    // X axis
    let xAxisGroup = g.select<SVGGElement>('g.x-axis');
    if (xAxisGroup.empty()) xAxisGroup = g.append('g').attr('class', 'x-axis');
    xAxisGroup.attr('transform', `translate(0,${innerHeight})`)
      .call(axisBottom(xScale))
      .call(g => {
        g.select('.domain').remove();
        g.selectAll('.tick line').remove();
        g.selectAll('.tick text')
          .attr('font-family', FONTS.sans)
          .attr('font-size', '12px')
          .attr('fill', CHART_COLORS.axisText);
      });

    // Y axis
    let yAxisGroup = g.select<SVGGElement>('g.y-axis');
    if (yAxisGroup.empty()) yAxisGroup = g.append('g').attr('class', 'y-axis');
    yAxisGroup.call(
      axisLeft(yScale)
        .ticks(5)
        .tickFormat(d => `${d}%`)
    ).call(g => {
      g.select('.domain').remove();
      g.selectAll('.tick line').remove();
      g.selectAll('.tick text')
        .attr('font-family', FONTS.sans)
        .attr('font-size', '12px')
        .attr('fill', CHART_COLORS.axisText);
    });

  }, [series, data, pinnedChannel, handleClick, prefersReducedMotion]);

  return (
    <div className="channel-chart-container">
      <h3 style={{
        fontFamily: FONTS.serif,
        fontSize: '22px',
        fontWeight: 700,
        lineHeight: 1.3,
        color: CHART_COLORS.ink,
        margin: '0 0 16px 0',
      }}>
        {label}
      </h3>
      <svg
        ref={svgRef}
        width="100%"
        height={CHART_HEIGHT}
        style={{ display: 'block', overflow: 'visible' }}
        role="img"
        aria-label={`${label} trend chart showing margin percentages over time`}
      />
    </div>
  );
}
