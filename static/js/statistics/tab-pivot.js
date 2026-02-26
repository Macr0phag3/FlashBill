/**
 * 统计页面 - 数据透视 Tab 模块
 */
const usePivotTab = () => {
    const pivotTimeUnit = Vue.ref('monthday');
    // Animation handle
    let sortInterval = null;
    let pivotChart = null;

    /** 处理透视数据 */
    const processPivotData = (data) => {
        const pivotData = {};

        data.forEach(item => {
            if (!item.date) return;
            const date = new Date(item.date);
            if (isNaN(date.getTime())) return;

            let pivotKey;
            let displayLabel;

            switch (pivotTimeUnit.value) {
                case 'hour':
                    const hour = date.getHours();
                    pivotKey = hour;
                    displayLabel = `${hour}时`;
                    break;
                case 'weekday':
                    const weekday = date.getDay();
                    pivotKey = weekday;
                    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
                    displayLabel = weekdays[weekday];
                    break;
                case 'monthday':
                    const monthday = date.getDate();
                    pivotKey = monthday;
                    displayLabel = `${monthday}日`;
                    break;
                case 'yearmonth':
                    const yearmonth = date.getMonth() + 1;
                    pivotKey = yearmonth;
                    displayLabel = `${yearmonth}月`;
                    break;
            }

            if (!pivotData[pivotKey]) {
                pivotData[pivotKey] = { key: pivotKey, label: displayLabel, amount: 0, count: 0 };
            }

            const absAmount = Math.abs(Number(item.amount) || 0);
            pivotData[pivotKey].amount += absAmount;
            pivotData[pivotKey].count += 1;
        });

        // 按 Key (时间维度自然顺序) 排序
        // pivotKey 基本上都是数字，直接相减即可
        const sortedData = Object.values(pivotData).sort((a, b) => a.key - b.key);

        return sortedData; // Return array directly
    };

    /** 初始化透视图表 */
    const initPivotChart = () => {
        const chartContainer = document.getElementById('pivotChartContainer');
        if (!chartContainer) return;

        if (pivotChart) pivotChart.dispose();

        const colors = getChartColors();
        pivotChart = echarts.init(chartContainer, colors.isDark ? 'dark' : undefined);

        window.addEventListener('app:anim-chart-change', (e) => {
            if (pivotChart) pivotChart.setOption({ animation: e.detail.enabled });
        });

        const series = [{
            name: '开销金额',
            type: 'bar',
            data: [],
            realtimeSort: false, // We handle sort manually
            itemStyle: {
                borderRadius: [4, 4, 0, 0], // Rounded corners top
                color: function (params) {
                    const colorPalette = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc'];
                    // Use a fixed mapping based on name if possible, or just cycle
                    return colorPalette[params.dataIndex % colorPalette.length];
                }
            },
            label: {
                show: true,
                position: 'top',
                formatter: function (params) { return formatAmount(params.value); },
                fontSize: 11,
                color: colors.textColor
            },
            // Add a markPoint to show "Sorting..." maybe? No, let's keep it clean.
        }];

        const option = {
            textStyle: { fontFamily: 'fusion-pixel' },
            backgroundColor: 'transparent',
            animationDurationUpdate: 100, // Reduced duration for faster sorting visualization
            animationEasingUpdate: 'quinticInOut',
            title: {
                text: '',
                left: 'center',
                top: '0px',
                textStyle: { color: colors.textColor }
            },
            tooltip: {
                trigger: 'axis',
                backgroundColor: colors.tooltipBg,
                borderColor: colors.tooltipBorder,
                textStyle: { color: colors.tooltipText },
                formatter: function (params) {
                    let result = '';
                    params.forEach(param => {
                        if (param.seriesName === '开销金额') {
                            result += `${param.name}<br/>${param.marker} 开销金额: ${formatAmount(param.value)}<br/>`;
                        }
                    });
                    return result;
                }
            },
            grid: {
                top: 40,
                bottom: 30, // Show labels properly
                left: 10,
                right: 10,
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: [],
                axisLabel: { rotate: 0, interval: 0, color: colors.textColor },
                axisLine: { lineStyle: { color: colors.axisLineColor } },
                splitLine: { show: false }
            },
            yAxis: {
                type: 'value',
                axisLabel: { formatter: function (value) { return formatAmount(value); }, color: colors.textColor },
                splitLine: { lineStyle: { color: colors.splitLineColor } }
            },
            series: series
        };

        if (localStorage.getItem('anim-chart') === 'false') {
            option.animation = false;
        }

        pivotChart.setOption(option);
    };

    /** 更新透视图表 */
    const updatePivotChart = (data) => {
        if (!pivotChart) {
            initPivotChart();
            if (!pivotChart) return;
        }

        const initialData = processPivotData(data); // 按时间维度自然顺序排列

        // 停止正在运行的排序动画
        if (sortInterval) {
            clearInterval(sortInterval);
            sortInterval = null;
        }

        // 渲染初始状态（时间顺序）
        updateChartWithData(initialData);

        // 图表动画关闭时，直接显示排序后的最终结果，不执行冒泡排序动画
        if (localStorage.getItem('anim-chart') === 'false') {
            const sortedData = [...initialData].sort((a, b) => b.amount - a.amount);
            updateChartWithData(sortedData);
            return;
        }

        // 开启状态：启动冒泡排序动画
        if (initialData.length > 1) {
            setTimeout(() => {
                runBubbleSort(initialData);
            }, 1000);
        }
    };

    const updateChartWithData = (sortedData) => {
        pivotChart.setOption({
            xAxis: {
                data: sortedData.map(item => item.label)
            },
            series: [{
                data: sortedData.map(item => item.amount),
                label: {
                    show: true,
                    position: 'top',
                    formatter: function (params) { return formatAmount(params.value); }
                }
            }]
        });
    };

    /** Bubble Sort Animation Logic */
    const runBubbleSort = (dataArray) => {
        let i = 0;
        let j = 0;
        const len = dataArray.length;

        const swapsPerFrame = 5;
        const intervalTime = 50; // Faster if more items

        sortInterval = setInterval(() => {
            let swappedThisFrame = false;

            for (let k = 0; k < swapsPerFrame; k++) {
                if (i < len) {
                    if (j < len - i - 1) {
                        // Compare and swap if needed (Descending)
                        if (dataArray[j].amount < dataArray[j + 1].amount) {
                            const temp = dataArray[j];
                            dataArray[j] = dataArray[j + 1];
                            dataArray[j + 1] = temp;
                            swappedThisFrame = true;
                        }
                        j++;
                    } else {
                        // End of inner loop
                        j = 0;
                        i++;
                    }
                } else {
                    // Sorting done
                    clearInterval(sortInterval);
                    sortInterval = null;
                    return;
                }
            }

            updateChartWithData(dataArray);

        }, intervalTime);
    };

    /** 调整图表大小 */
    const resizePivotChart = () => {
        if (pivotChart) pivotChart.resize();
    };

    return {
        pivotTimeUnit,
        initPivotChart,
        updatePivotChart,
        resizePivotChart
    };
};
