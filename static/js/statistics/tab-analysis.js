/**
 * 统计页面 - 数据分析 Tab 模块
 */
const useAnalysisTab = () => {
    const averageResults = Vue.ref([]);
    const firstBillDate = Vue.ref('');
    const lastBillDate = Vue.ref('');
    const timeSpan = Vue.ref({ days: 0, weeks: 0, months: 0, years: 0 });
    const totalBillCount = Vue.ref(0);

    // 时间跨度表格数据
    const timeSpanData = Vue.computed(() => {
        return [
            { label: '开始日期', value: firstBillDate.value },
            { label: '结束日期', value: lastBillDate.value },
            { label: '账单总数', value: totalBillCount.value },
            { label: '总天数', value: timeSpan.value.days },
            { label: '总周数', value: timeSpan.value.weeks },
            { label: '总月数', value: timeSpan.value.months },
            { label: '总年数', value: timeSpan.value.years }
        ];
    });

    /** 计算时间跨度 */
    const calculateTimeSpan = (allData) => {
        const resetStats = () => {
            firstBillDate.value = '';
            lastBillDate.value = '';
            totalBillCount.value = 0;
            timeSpan.value = { days: 0, weeks: 0, months: 0, years: 0 };
        };

        if (!allData || allData.length === 0) {
            resetStats();
            return;
        }

        totalBillCount.value = allData.length;
        const { start, end } = getTimeRange(allData);

        if (!start || !end) {
            resetStats();
            return;
        }

        firstBillDate.value = formatDate(start);
        lastBillDate.value = formatDate(end);

        timeSpan.value = {
            days: calculateDivisor(start, end, 'day'),
            weeks: calculateDivisor(start, end, 'week'),
            months: calculateDivisor(start, end, 'month'),
            years: Math.max(calculateDivisor(start, end, 'year'), 0)
        };
    };

    /** 计算单条统计结果 */
    const calculateSingleStats = (data, name, nameLabel, extraFilters = []) => {
        if (!data || data.length === 0) return null;

        const totalAmount = calculateTotalAmount(data);
        const { start, end } = getTimeRange(data);

        const dayDivisor = calculateDivisor(start, end, 'day');
        const weekDivisor = calculateDivisor(start, end, 'week');
        const monthDivisor = calculateDivisor(start, end, 'month');
        const yearDivisor = calculateDivisor(start, end, 'year');

        const totalValue = Math.abs(totalAmount);

        return {
            name: name || '',
            nameLabel: nameLabel || '名称',
            totalValue: totalValue,
            dayValue: totalValue / dayDivisor,
            weekValue: totalValue / weekDivisor,
            monthValue: totalValue / monthDivisor,
            yearValue: totalValue / yearDivisor,
            filters: extraFilters
        };
    };

    /** 计算平均开销 */
    const calculateAverage = (filteredData, filterForm) => {
        if (!filteredData || filteredData.length === 0) {
            averageResults.value = [];
            return;
        }

        const results = [];

        // 判断是否需要分组
        let groupBy = null;
        if (filterForm.tag && filterForm.tag.length > 1) groupBy = 'tag';
        else if (filterForm.category && filterForm.category.length > 1) groupBy = 'category';
        else if (filterForm.book && filterForm.book.length > 1) groupBy = 'book';
        else if (filterForm.month && filterForm.month.length > 1) groupBy = 'month';
        else if (filterForm.year && filterForm.year.length > 1) groupBy = 'year';

        if (groupBy) {
            const groups = {};
            filteredData.forEach(item => {
                let key = item[groupBy];
                if (groupBy === 'month') {
                    key = new Date(item.date).getMonth() + 1;
                } else if (groupBy === 'year') {
                    key = new Date(item.date).getFullYear();
                }
                if (!groups[key]) groups[key] = [];
                groups[key].push(item);
            });

            Object.entries(groups).forEach(([key, groupData]) => {
                const stat = calculateSingleStats(groupData, key, groupBy);
                if (stat) results.push(stat);
            });
        }

        // 添加总计行
        const totalStat = calculateSingleStats(filteredData, '总计', '总计');
        if (totalStat) results.unshift(totalStat);

        averageResults.value = results;
    };

    return {
        averageResults,
        timeSpanData,
        calculateTimeSpan,
        calculateAverage
    };
};
