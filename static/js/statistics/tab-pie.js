/**
 * 统计页面 - 饼图 Tab 模块
 */
const usePieTab = () => {
    let categoryPieChart = null;
    let tagPieChart = null;

    /** 按字段分组汇总数据 */
    const processPieData = (data, field) => {
        const pieData = {};
        data.forEach(item => {
            if (item[field]) {
                if (!pieData[item[field]]) pieData[item[field]] = 0;
                pieData[item[field]] += Number(item.amount) || 0;
            }
        });

        return Object.entries(pieData).map(([name, value]) => ({
            name,
            value: Math.abs(value)
        })).sort((a, b) => b.value - a.value);
    };

    /** 初始化饼图 */
    const initPieCharts = () => {
        const categoryContainer = document.getElementById('categoryPieContainer');
        const tagContainer = document.getElementById('tagPieContainer');
        if (!categoryContainer || !tagContainer) return;

        if (categoryPieChart) categoryPieChart.dispose();
        if (tagPieChart) tagPieChart.dispose();

        const colors = getChartColors();
        const theme = colors.isDark ? 'dark' : undefined;
        const animationEnabled = localStorage.getItem('anim-chart') !== 'false';

        categoryPieChart = echarts.init(categoryContainer, theme);
        tagPieChart = echarts.init(tagContainer, theme);

        const onAnimationChange = (e) => {
            const enabled = e.detail.enabled;
            if (categoryPieChart) categoryPieChart.setOption({ animation: enabled });
            if (tagPieChart) tagPieChart.setOption({ animation: enabled });
        };
        window.addEventListener('app:anim-chart-change', onAnimationChange);

        const pieOption = {
            textStyle: { fontFamily: 'fusion-pixel' },
            backgroundColor: 'transparent',
            title: {
                text: '',
                left: 'center',
                top: '20px',
                textStyle: { fontSize: 16, fontWeight: 'bold', color: colors.textColor }
            },
            tooltip: {
                trigger: 'item',
                backgroundColor: colors.tooltipBg,
                borderColor: colors.tooltipBorder,
                textStyle: { color: colors.tooltipText },
                formatter: function (params) {
                    return `${params.name}: ${formatAmount(params.value)} (${params.percent}%)`;
                }
            },
            legend: {
                orient: 'vertical',
                left: 0,
                type: 'scroll',
                top: '40px',
                textStyle: { color: colors.textColor }
            },
            series: [{
                type: 'pie',
                radius: '50%',
                center: ['50%', '60%'],
                data: [],
                emphasis: {
                    itemStyle: {
                        shadowBlur: 10,
                        shadowOffsetX: 0,
                        shadowColor: 'rgba(0, 0, 0, 0.5)'
                    }
                },
                label: { color: colors.textColor }
            }],
            animation: animationEnabled
        };

        categoryPieChart.setOption({ ...pieOption, title: { ...pieOption.title, text: '类别统计' } });
        tagPieChart.setOption({ ...pieOption, title: { ...pieOption.title, text: '标签统计' } });
    };

    /** 更新饼图数据 */
    const updatePieCharts = (data) => {
        if (!categoryPieChart || !tagPieChart) {
            initPieCharts();
            if (!categoryPieChart || !tagPieChart) return;
        }

        const categoryData = processPieData(data, 'category');
        const tagData = processPieData(data, 'tag');

        categoryPieChart.setOption({ series: [{ data: categoryData }] });
        tagPieChart.setOption({ series: [{ data: tagData }] });
    };

    /** 调整图表大小 */
    const resizePieCharts = () => {
        if (categoryPieChart) categoryPieChart.resize();
        if (tagPieChart) tagPieChart.resize();
    };

    return {
        initPieCharts,
        updatePieCharts,
        resizePieCharts
    };
};
