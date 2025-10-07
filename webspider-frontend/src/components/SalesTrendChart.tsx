import React from 'react';
import ReactECharts from 'echarts-for-react';

interface SalesTrendChartProps {
  data: Array<{
    date: string;
    totalSales: number;
    avgSales: number;
    count: number;
  }>;
}

const SalesTrendChart: React.FC<SalesTrendChartProps> = ({ data }) => {
  const option = {
    title: {
      text: '销量趋势图',
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
      },
    },
    legend: {
      data: ['总销量', '平均销量', '采集次数'],
      top: 30,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: data.map((item) => item.date),
    },
    yAxis: [
      {
        type: 'value',
        name: '销量',
        position: 'left',
      },
      {
        type: 'value',
        name: '采集次数',
        position: 'right',
      },
    ],
    series: [
      {
        name: '总销量',
        type: 'line',
        smooth: true,
        data: data.map((item) => item.totalSales),
        itemStyle: {
          color: '#5470c6',
        },
        areaStyle: {
          color: 'rgba(84, 112, 198, 0.2)',
        },
      },
      {
        name: '平均销量',
        type: 'line',
        smooth: true,
        data: data.map((item) => item.avgSales),
        itemStyle: {
          color: '#91cc75',
        },
      },
      {
        name: '采集次数',
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        data: data.map((item) => item.count),
        itemStyle: {
          color: '#fac858',
        },
      },
    ],
  };

  return <ReactECharts option={option} style={{ height: '400px', width: '100%' }} />;
};

export default SalesTrendChart;
