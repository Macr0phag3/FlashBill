/**
 * 统计页面 - 折线图 Tab 模块
 */
const useChartTab = () => {
    const timeUnit = Vue.ref('month');
    let chartInstance = null;

    /** 按时间单位分组汇总数据 */
    const processChartData = (data) => {
        const groupedData = {};
        data.forEach(item => {
            if (!item.date) return;
            const date = new Date(item.date);
            if (isNaN(date.getTime())) return;

            let timeKey;
            switch (timeUnit.value) {
                case 'day':
                    timeKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
                    break;
                case 'week':
                    const firstDayOfYear = new Date(date.getFullYear(), 0, 1);
                    const pastDaysOfYear = (date - firstDayOfYear) / 86400000;
                    const weekNumber = Math.ceil((pastDaysOfYear + firstDayOfYear.getDay() + 1) / 7);
                    timeKey = `${date.getFullYear()}-W${String(weekNumber).padStart(2, '0')}`;
                    break;
                case 'month':
                    timeKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
                    break;
                case 'year':
                    timeKey = `${date.getFullYear()}`;
                    break;
            }

            if (!groupedData[timeKey]) groupedData[timeKey] = 0;
            groupedData[timeKey] += Number(item.amount) || 0;
        });

        const sortedKeys = Object.keys(groupedData).sort();
        return {
            months: sortedKeys,
            amounts: sortedKeys.map(key => groupedData[key])
        };
    };

    /** 生成图表配置 */
    const getOption = (colors, xAxisData, seriesData, movingAverage, fullAverage, fullAverageValue) => {
        return {
            textStyle: { fontFamily: 'fusion-pixel' },
            backgroundColor: 'transparent',
            tooltip: {
                trigger: 'axis',
                backgroundColor: colors.tooltipBg,
                borderColor: colors.tooltipBorder,
                textStyle: { color: colors.tooltipText },
                formatter: function (params) {
                    let result = '';
                    params.forEach(param => {
                        result += `${param.name}<br/>${param.marker} ${param.seriesName}: ${formatAmount(param.value)}<br/>`;
                    });
                    return result;
                }
            },
            legend: {
                textStyle: { color: colors.textColor },
                bottom: '-5px'
            },
            grid: {
                top: 30,
                bottom: 80,
                left: 70,
                right: 60,
                containLabel: false
            },
            xAxis: {
                type: 'category',
                data: xAxisData,
                axisLabel: { rotate: 45, color: colors.textColor },
                axisLine: { lineStyle: { color: colors.axisLineColor } }
            },
            yAxis: {
                type: 'value',
                axisLabel: {
                    formatter: function (value) { return formatAmount(value); },
                    color: colors.textColor
                },
                splitLine: { lineStyle: { color: colors.splitLineColor } }
            },
            series: [{
                name: '花销',
                type: 'line',
                data: seriesData,
                smooth: false,
                itemStyle: { color: '#409EFF' },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: 'rgba(64,158,255,0.3)' },
                        { offset: 1, color: 'rgba(64,158,255,0.1)' }
                    ])
                }
            }, {
                name: '短期均线',
                type: 'line',
                data: movingAverage,
                smooth: false,
                itemStyle: { color: '#F56C6C' },
                lineStyle: { width: 2, type: 'dashed' },
                symbol: 'none'
            }, {
                name: '全量均线',
                type: 'line',
                data: fullAverage,
                smooth: false,
                itemStyle: { color: '#67C23A' },
                lineStyle: { width: 2, type: 'dotted' },
                symbol: 'none',
                markPoint: {
                    data: [{
                        name: '全量均线值',
                        value: formatAmount(fullAverageValue),
                        xAxis: xAxisData.length - 1,
                        yAxis: fullAverageValue,
                        symbolSize: 0,
                        itemStyle: { color: '#67C23A' },
                        label: { formatter: '{c}', position: 'right', color: '#67C23A' }
                    }]
                }
            }]
        };
    };

    /** 初始化图表 */
    const initChart = () => {
        const chartContainer = document.getElementById('chartContainer');
        if (!chartContainer) return;

        if (chartInstance) chartInstance.dispose();

        const colors = getChartColors();
        chartInstance = echarts.init(chartContainer, colors.isDark ? 'dark' : undefined);
    };

    /** 更新图表 */
    const updateChart = (data) => {
        if (!chartInstance) initChart();
        if (!chartInstance) return;

        const chartData = processChartData(data);

        // 计算移动平均线
        const calculateMovingAverage = (data, windowSize = 3) => {
            const result = [];
            for (let i = 0; i < data.length; i++) {
                if (i < windowSize - 1) {
                    const sum = data.slice(0, i + 1).reduce((acc, val) => acc + val, 0);
                    result.push(sum / (i + 1));
                } else {
                    const sum = data.slice(i - windowSize + 1, i + 1).reduce((acc, val) => acc + val, 0);
                    result.push(sum / windowSize);
                }
            }
            return result;
        };
        const movingAverage = calculateMovingAverage(chartData.amounts);

        // 计算全量平均线
        const calculateFullAverage = () => {
            if (!data || data.length === 0) return 0;
            const totalAmount = calculateTotalAmount(data);
            const { start, end } = getTimeRange(data);
            const timeDivisor = calculateDivisor(start, end, timeUnit.value);
            return Math.abs(totalAmount / timeDivisor);
        };

        const fullAverageValue = calculateFullAverage();
        const fullAverage = Array(chartData.amounts.length).fill(fullAverageValue);

        const colors = getChartColors();
        const option = getOption(colors, chartData.months, chartData.amounts, movingAverage, fullAverage, fullAverageValue);
        chartInstance.setOption(option);
    };

    /** 调整图表大小 */
    const resizeChart = () => {
        if (chartInstance) chartInstance.resize();
    };

    return {
        timeUnit,
        initChart,
        updateChart,
        resizeChart
    };
};
