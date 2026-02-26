/**
 * 统计页面 - 日历热力图 Tab 模块
 */
const useCalendarTab = () => {
    let myChart = null;
    let allCalendarData = [];
    let yearBlockHeight = 140;

    // Animation timers
    let glitchInterval = null;

    /** 按年份分组处理日历数据 */
    const processCalendarDataByYear = (data) => {
        const dailyData = {};
        data.forEach(item => {
            if (!item.date) return;
            const dateObj = new Date(item.date);
            if (isNaN(dateObj.getTime())) return;

            const year = dateObj.getFullYear();
            const month = String(dateObj.getMonth() + 1).padStart(2, '0');
            const day = String(dateObj.getDate()).padStart(2, '0');
            const dateKey = `${year}-${month}-${day}`;

            if (!dailyData[dateKey]) dailyData[dateKey] = 0;
            dailyData[dateKey] += Math.abs(Number(item.amount) || 0);
        });

        // 按年份分组
        const yearlyData = {};
        Object.entries(dailyData).forEach(([date, amount]) => {
            const year = date.split('-')[0];
            if (!yearlyData[year]) yearlyData[year] = [];
            yearlyData[year].push([date, amount]);
        });

        return yearlyData;
    };

    /** 初始化日历图表容器 */
    const initCalendarChart = () => {
        const scrollContainer = document.getElementById('calendarScrollContainer');
        if (!scrollContainer) return;

        scrollContainer.innerHTML = '';

        const chartDiv = document.createElement('div');
        chartDiv.id = 'calendar-chart-instance';
        chartDiv.style.width = '100%';
        chartDiv.style.height = '100px';
        scrollContainer.appendChild(chartDiv);

        if (myChart) {
            myChart.dispose();
            myChart = null;
        }

        const colors = getChartColors();
        myChart = echarts.init(chartDiv, colors.isDark ? 'dark' : undefined);

        window.addEventListener('app:anim-chart-change', (e) => {
            if (myChart) myChart.setOption({ animation: e.detail.enabled });
        });
    };

    /** 更新日历图表 */
    const updateCalendarChart = (data) => {
        allCalendarData = data;

        // 清除现有的动画
        if (glitchInterval) {
            clearInterval(glitchInterval);
            glitchInterval = null;
        }

        const scrollContainer = document.getElementById('calendarScrollContainer');
        if (!scrollContainer) return;

        if (data.length === 0) {
            scrollContainer.innerHTML = '<div style="text-align: center; padding: 50px; color: #909399;">暂无数据</div>';
            if (myChart) {
                myChart.dispose();
                myChart = null;
            }
            return;
        }

        if (!myChart || !document.getElementById('calendar-chart-instance')) {
            initCalendarChart();
        }

        const yearlyData = processCalendarDataByYear(data);
        const availableYears = Object.keys(yearlyData).map(Number).sort((a, b) => b - a);

        // 计算高度
        const TOP_PADDING = 60;
        const BOTTOM_PADDING = 20;
        const totalHeight = TOP_PADDING + availableYears.length * yearBlockHeight + BOTTOM_PADDING;

        const chartDiv = document.getElementById('calendar-chart-instance');
        if (chartDiv) {
            chartDiv.style.height = `${totalHeight}px`;
            myChart.resize();
        }

        const colors = getChartColors();

        // 基础配置
        const getBaseOption = () => {
            const option = {
                textStyle: { fontFamily: 'fusion-pixel' },
                backgroundColor: 'transparent',
                tooltip: {
                    position: 'top',
                    backgroundColor: colors.tooltipBg,
                    borderColor: colors.tooltipBorder,
                    textStyle: { color: colors.tooltipText },
                    formatter: function (params) {
                        if (params.value[1] === undefined || params.value[1] === null) return;
                        return `${params.value[0]}<br/>支出: ${formatAmount(params.value[1])}`;
                    }
                },
                visualMap: {
                    type: 'piecewise',
                    orient: 'horizontal',
                    left: 'center',
                    top: 0,
                    textStyle: { color: colors.textColor },
                    pieces: [
                        { min: 0.01, max: 10, label: '<10', color: '#89c0edff' },
                        { min: 10, max: 100, label: '<100', color: '#64b5f6' },
                        { min: 100, max: 200, label: '<200', color: '#1e88e5' },
                        { min: 200, max: 300, label: '<300', color: '#0d47a1' },
                        { min: 300, max: 500, label: '<500', color: '#e4bfa4ff' },
                        { min: 500, max: 1000, label: '<1000', color: '#FAC858' },
                        { min: 1000, max: 3000, label: '<3000', color: '#FC8452' },
                        { min: 3000, max: 5000, label: '<5000', color: '#f43b09ff' },
                        { min: 5000, max: 10000, label: '<10000', color: '#b67ef9ff' },
                        { min: 10000, label: '爆表', color: '#c407f8ff' }
                    ]
                },
                calendar: availableYears.map((year, index) => ({
                    top: TOP_PADDING + index * yearBlockHeight,
                    left: 48,
                    right: 30,
                    orient: 'horizontal',
                    cellSize: [30, 20],
                    range: year,
                    itemStyle: { borderWidth: 1, borderColor: colors.borderColor, color: 'transparent' },
                    yearLabel: { show: true, margin: 30, color: colors.textColor, fontFamily: 'fusion-pixel' },
                    dayLabel: { firstDay: 1, nameMap: 'cn', color: colors.textColor, margin: 10 },
                    monthLabel: { show: index === 0, color: colors.textColor, nameMap: 'cn', position: 'start', margin: 10 },
                    splitLine: { show: false }
                })),
                graphic: [{
                    type: 'group',
                    right: 30,
                    top: 0,
                    children: [{
                        type: 'rect',
                        z: 100,
                        left: 'center',
                        top: 'middle',
                        shape: { width: 70, height: 25, r: 5 },
                        style: {
                            fill: colors.isDark ? 'rgba(245, 108, 108, 0.15)' : '#f56c6c',
                            stroke: colors.isDark ? 'rgba(245, 108, 108, 0.4)' : colors.borderColor,
                            lineWidth: 1
                        }
                    }, {
                        type: 'text',
                        z: 100,
                        left: 'center',
                        top: 'middle',
                        style: {
                            fill: colors.isDark ? '#f56c6c' : '#fff',
                            text: yearBlockHeight === 160 ? '恢复默认' : '年度拆分'
                        }
                    }],
                    onclick: function () {
                        yearBlockHeight = yearBlockHeight === 160 ? 140 : 160;
                        updateCalendarChart(allCalendarData);
                    }
                }]
            };
            if (localStorage.getItem('anim-chart') === 'false') {
                option.animation = false;
            }
            return option;
        };

        // 1. 设置基础 Option
        myChart.setOption(getBaseOption(), true);

        // --- 渐进式锁定动画逻辑 ---
        const animationEnabled = localStorage.getItem('anim-chart') !== 'false';

        if (!animationEnabled) {
            // 如果动画禁用，直接显示最终数据
            const finalSeries = availableYears.map((year, index) => ({
                type: 'heatmap',
                coordinateSystem: 'calendar',
                calendarIndex: index,
                data: yearlyData[year] || [],
                itemStyle: { borderRadius: 1 }
            }));
            myChart.setOption({ series: finalSeries });
            return;
        }

        const DURATION = 2000; // 动画总时长
        const LOCK_TIMES = {}; // 存储每个日期的锁定时间
        const START_TIME = Date.now();

        // 为每个存在的日期（包括空日期）预计算锁定时间
        availableYears.forEach(year => {
            const isLeap = (year % 4 === 0 && year % 100 !== 0) || year % 400 === 0;
            const days = isLeap ? 366 : 365;
            for (let i = 0; i < days; i++) {
                const d = new Date(year, 0, i + 1);
                const dateKey = [
                    d.getFullYear(),
                    String(d.getMonth() + 1).padStart(2, '0'),
                    String(d.getDate()).padStart(2, '0')
                ].join('-');
                // 随机锁定时间 0 ~ DURATION
                LOCK_TIMES[dateKey] = Math.random() * DURATION;
            }
        });

        const runProgressiveFrame = () => {
            const now = Date.now();
            const elapsed = now - START_TIME;

            // 检查是否所有动画已结束
            if (elapsed > DURATION + 100) { // 稍微多给点buffer
                clearInterval(glitchInterval);
                glitchInterval = null;
                // 最终确保显示完全真实数据
                const finalSeries = availableYears.map((year, index) => ({
                    type: 'heatmap',
                    coordinateSystem: 'calendar',
                    calendarIndex: index,
                    data: yearlyData[year] || [],
                    itemStyle: { borderRadius: 1 }
                }));
                myChart.setOption({ series: finalSeries });
                return;
            }

            // 构建当前帧的数据
            const frameSeries = availableYears.map((year, index) => {
                const yearData = [];
                const isLeap = (year % 4 === 0 && year % 100 !== 0) || year % 400 === 0;
                const days = isLeap ? 366 : 365;

                const progress = Math.min(elapsed / DURATION, 1);
                const noiseAlpha = progress; // 0 -> 1

                for (let i = 0; i < days; i++) {
                    const d = new Date(year, 0, i + 1);
                    const dateKey = [
                        d.getFullYear(),
                        String(d.getMonth() + 1).padStart(2, '0'),
                        String(d.getDate()).padStart(2, '0')
                    ].join('-');

                    // 如果当前时间已超过该日期的锁定时间，显示真实数据
                    if (elapsed >= LOCK_TIMES[dateKey]) {
                        // 查找真实数据中是否有值
                        const realVal = (yearlyData[year] || []).find(item => item[0] === dateKey);
                        if (realVal) {
                            yearData.push(realVal);
                        }
                    } else {
                        // 否则显示随机噪音（始终显示，依赖 opacity 淡出）
                        // 为了避免空隙，我们可以让没锁定的都显示噪音
                        const randomVal = Math.pow(10, Math.random() * 3.5);
                        yearData.push({
                            value: [dateKey, randomVal],
                            itemStyle: {
                                opacity: noiseAlpha
                            }
                        });
                    }
                }

                return {
                    type: 'heatmap',
                    coordinateSystem: 'calendar',
                    calendarIndex: index,
                    data: yearData,
                    itemStyle: { borderRadius: 1 }
                };
            });

            myChart.setOption({ series: frameSeries });
        };

        // 立即执行并启动循环
        runProgressiveFrame();
        glitchInterval = setInterval(runProgressiveFrame, 60);
    };

    /** 调整图表大小 */
    const resizeCalendar = () => {
        if (myChart) myChart.resize();
    };

    return {
        initCalendarChart,
        updateCalendarChart,
        resizeCalendar
    };
};


