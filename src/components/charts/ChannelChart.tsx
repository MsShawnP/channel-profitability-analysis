import { useRef, useEffect, useState, useCallback } from 'react';
import * as d3 from 'd3';
import CalloutCard from './CalloutCard';
import { formatCompact, getTealColor } from './chartUtils';
import type { LayerBreakdownItem } from './CalloutCard';

export interface ChannelData {
  channel_name: string;
  value: number;
  previous_value?: number;
  breakdown?: LayerBreakdownItem[];
}

export interface ChannelChartProps {
  data: ChannelData[];
  layerLabel: string;
  valueLabel?: string;
}

// Chart dimensions
const MARGIN = { top: 12, right: 80, bottom: 40, left: 140 };
const BAR_HEIGHT = 36;
const BAR_GAP = 8;
const GRIDLINE_COLOR = '#e5e0d8';
const DIM_OPACITY = 0.2;
const TRANSITION_DURATION = 200;

/**
 * Horizontal bar chart with click-to-pin interaction.
 * D3 owns the SVG internals; React manages the container and CalloutCard.
 * Compatible with Astro's client:visible hydration directive.
 */
export default function ChannelChart({ data, layerLabel, valueLabel }: ChannelChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [pinnedChannel, setPinnedChannel] = useState<string | null>(null);

  // Sort data by value descending to assign teal palette correctly
  const sortedData = [...data].sort((a, b) => b.value - a.value);

  const pinnedData = sortedData.find((d) => d.channel_name === pinnedChannel);

  const handleBarClick = useCallback((channelName: string) => {
    setPinnedChannel((current) => (current === channelName ? null : channelName));
  }, []);

  // Check for reduced motion preference
  const prefersReducedMotion = typeof window !== 'undefined'
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // D3 rendering
  useEffect(() => {
    const svg = d3.select(svgRef.current);
    if (!svgRef.current) return;

    const chartWidth = svgRef.current.clientWidth || 700;
    const chartHeight = MARGIN.top + MARGIN.bottom + sortedData.length * (BAR_HEIGHT + BAR_GAP);

    // Update SVG dimensions
    svg.attr('viewBox', `0 0 ${chartWidth} ${chartHeight}`);

    const innerWidth = chartWidth - MARGIN.left - MARGIN.right;
    const innerHeight = chartHeight - MARGIN.top - MARGIN.bottom;

    // Scales
    const maxValue = d3.max(sortedData, (d) => d.value) || 0;
    const xScale = d3.scaleLinear()
      .domain([0, maxValue > 0 ? maxValue : 1])
      .range([0, innerWidth]);

    const yScale = d3.scaleBand()
      .domain(sortedData.map((d) => d.channel_name))
      .range([0, innerHeight])
      .padding(BAR_GAP / (BAR_HEIGHT + BAR_GAP));

    // Container group
    let g = svg.select<SVGGElement>('g.chart-inner');
    if (g.empty()) {
      g = svg.append('g').attr('class', 'chart-inner');
    }
    g.attr('transform', `translate(${MARGIN.left},${MARGIN.top})`);

    // Gridlines (horizontal only)
    const ticks = xScale.ticks(5);
    const gridlines = g.selectAll<SVGLineElement, number>('line.gridline')
      .data(ticks, (d) => String(d));

    gridlines.join(
      (enter) => enter.append('line')
        .attr('class', 'gridline')
        .attr('x1', (d) => xScale(d))
        .attr('x2', (d) => xScale(d))
        .attr('y1', 0)
        .attr('y2', innerHeight)
        .attr('stroke', GRIDLINE_COLOR)
        .attr('stroke-width', 1)
        .attr('stroke-dasharray', 'none'),
      (update) => update
        .attr('x1', (d) => xScale(d))
        .attr('x2', (d) => xScale(d))
        .attr('y2', innerHeight),
      (exit) => exit.remove()
    );

    // Bars
    const bars = g.selectAll<SVGRectElement, ChannelData>('rect.bar')
      .data(sortedData, (d) => d.channel_name);

    const duration = prefersReducedMotion ? 0 : TRANSITION_DURATION;

    bars.join(
      (enter) => enter.append('rect')
        .attr('class', 'bar')
        .attr('x', 0)
        .attr('y', (d) => yScale(d.channel_name) || 0)
        .attr('width', (d) => Math.max(0, xScale(d.value)))
        .attr('height', yScale.bandwidth())
        .attr('fill', (_, i) => getTealColor(i, sortedData.length))
        .attr('rx', 2)
        .attr('ry', 2)
        .style('cursor', 'pointer')
        .style('opacity', (d) => {
          if (!pinnedChannel) return 1;
          return d.channel_name === pinnedChannel ? 1 : DIM_OPACITY;
        })
        .on('click', (_, d) => handleBarClick(d.channel_name)),
      (update) => {
        const u = update
          .attr('y', (d) => yScale(d.channel_name) || 0)
          .attr('width', (d) => Math.max(0, xScale(d.value)))
          .attr('height', yScale.bandwidth())
          .attr('fill', (_, i) => getTealColor(i, sortedData.length));

        if (duration > 0) {
          u.transition()
            .duration(duration)
            .ease(d3.easeCubicOut)
            .style('opacity', (d) => {
              if (!pinnedChannel) return 1;
              return d.channel_name === pinnedChannel ? 1 : DIM_OPACITY;
            });
        } else {
          u.style('opacity', (d) => {
            if (!pinnedChannel) return 1;
            return d.channel_name === pinnedChannel ? 1 : DIM_OPACITY;
          });
        }
        return u;
      },
      (exit) => exit.remove()
    );

    // Bar value labels (text on each bar)
    const labels = g.selectAll<SVGTextElement, ChannelData>('text.bar-label')
      .data(sortedData, (d) => d.channel_name);

    labels.join(
      (enter) => enter.append('text')
        .attr('class', 'bar-label')
        .attr('x', (d) => xScale(d.value) + 6)
        .attr('y', (d) => (yScale(d.channel_name) || 0) + yScale.bandwidth() / 2)
        .attr('dy', '0.35em')
        .attr('font-family', "var(--font-sans, 'Source Sans 3', sans-serif)")
        .attr('font-size', '12px')
        .attr('fill', '#2a2a2a')
        .text((d) => formatCompact(d.value))
        .style('opacity', (d) => {
          if (!pinnedChannel) return 1;
          return d.channel_name === pinnedChannel ? 1 : DIM_OPACITY;
        }),
      (update) => {
        const u = update
          .attr('x', (d) => xScale(d.value) + 6)
          .attr('y', (d) => (yScale(d.channel_name) || 0) + yScale.bandwidth() / 2)
          .text((d) => formatCompact(d.value));

        if (duration > 0) {
          u.transition()
            .duration(duration)
            .ease(d3.easeCubicOut)
            .style('opacity', (d) => {
              if (!pinnedChannel) return 1;
              return d.channel_name === pinnedChannel ? 1 : DIM_OPACITY;
            });
        } else {
          u.style('opacity', (d) => {
            if (!pinnedChannel) return 1;
            return d.channel_name === pinnedChannel ? 1 : DIM_OPACITY;
          });
        }
        return u;
      },
      (exit) => exit.remove()
    );

    // Y-axis (channel names)
    const yAxisLabels = g.selectAll<SVGTextElement, ChannelData>('text.y-label')
      .data(sortedData, (d) => d.channel_name);

    yAxisLabels.join(
      (enter) => enter.append('text')
        .attr('class', 'y-label')
        .attr('x', -8)
        .attr('y', (d) => (yScale(d.channel_name) || 0) + yScale.bandwidth() / 2)
        .attr('dy', '0.35em')
        .attr('text-anchor', 'end')
        .attr('font-family', "var(--font-sans, 'Source Sans 3', sans-serif)")
        .attr('font-size', '12px')
        .attr('fill', '#2a2a2a')
        .text((d) => d.channel_name)
        .style('opacity', (d) => {
          if (!pinnedChannel) return 1;
          return d.channel_name === pinnedChannel ? 1 : DIM_OPACITY;
        }),
      (update) => {
        const u = update
          .attr('y', (d) => (yScale(d.channel_name) || 0) + yScale.bandwidth() / 2)
          .text((d) => d.channel_name);

        if (duration > 0) {
          u.transition()
            .duration(duration)
            .ease(d3.easeCubicOut)
            .style('opacity', (d) => {
              if (!pinnedChannel) return 1;
              return d.channel_name === pinnedChannel ? 1 : DIM_OPACITY;
            });
        } else {
          u.style('opacity', (d) => {
            if (!pinnedChannel) return 1;
            return d.channel_name === pinnedChannel ? 1 : DIM_OPACITY;
          });
        }
        return u;
      },
      (exit) => exit.remove()
    );

    // X-axis (bottom) with compact dollar formatting
    let xAxisGroup = g.select<SVGGElement>('g.x-axis');
    if (xAxisGroup.empty()) {
      xAxisGroup = g.append('g').attr('class', 'x-axis');
    }
    xAxisGroup
      .attr('transform', `translate(0,${innerHeight})`)
      .call(
        d3.axisBottom(xScale)
          .ticks(5)
          .tickFormat((d) => formatCompact(d as number))
      )
      .call((g) => {
        g.select('.domain').remove();
        g.selectAll('.tick line').remove();
        g.selectAll('.tick text')
          .attr('font-family', "var(--font-sans, 'Source Sans 3', sans-serif)")
          .attr('font-size', '12px')
          .attr('fill', '#6b6b6b');
      });

  }, [sortedData, pinnedChannel, handleBarClick, prefersReducedMotion]);

  // Calculate SVG height based on data
  const svgHeight = MARGIN.top + MARGIN.bottom + sortedData.length * (BAR_HEIGHT + BAR_GAP);

  return (
    <div className="channel-chart-container">
      {/* Chart title */}
      <h3 style={{
        fontFamily: "var(--font-serif, 'Playfair Display', Georgia, 'Times New Roman', serif)",
        fontSize: '22px',
        fontWeight: 700,
        lineHeight: 1.3,
        color: '#2a2a2a',
        margin: '0 0 16px 0',
      }}>
        {layerLabel}
      </h3>

      {/* Callout card rendered above chart when a channel is pinned */}
      {pinnedData && (
        <CalloutCard
          channelName={pinnedData.channel_name}
          totalValue={pinnedData.value}
          breakdown={pinnedData.breakdown}
        />
      )}

      {/* SVG container — D3 manages internals */}
      <svg
        ref={svgRef}
        width="100%"
        height={svgHeight}
        style={{ display: 'block', overflow: 'visible' }}
        role="img"
        aria-label={`${layerLabel} bar chart showing ${valueLabel || 'values'} by channel`}
      />
    </div>
  );
}
