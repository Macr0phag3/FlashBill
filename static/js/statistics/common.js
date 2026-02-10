/**
 * 统计页面公共模块
 * 
 * 提供图表主题颜色配置、时间计算等通用功能
 */

/**
 * 获取当前主题对应的图表颜色配置
 * @returns {Object} 包含各种颜色属性的配置对象
 */
const getChartColors = () => {
    const isDark = document.documentElement.classList.contains('dark');
    return {
        isDark,
        backgroundColor: isDark ? 'transparent' : '#fff',
        textColor: isDark ? '#dee2e6' : '#303133',
        axisLineColor: isDark ? '#4c4d4f' : '#DCDFE6',
        splitLineColor: isDark ? '#363637' : '#E4E7ED',
        tooltipBg: isDark ? 'rgba(0, 0, 0, 0.8)' : 'rgba(255, 255, 255, 0.9)',
        tooltipBorder: isDark ? '#4C4D4F' : '#E4E7ED',
        tooltipText: isDark ? '#fff' : '#303133',
        borderColor: isDark ? '#4C4D4F' : '#DCDFE6'
    };
};

/**
 * 计算两个日期之间的时间单位数量
 * 用于计算日均/周均/月均/年均开销
 * 
 * @param {Date} start - 开始日期
 * @param {Date} end - 结束日期
 * @param {string} type - 时间单位 ('day'|'week'|'month'|'year')
 * @returns {number} 时间单位数量（至少为1）
 */
const calculateDivisor = (start, end, type) => {
    if (!start || !end) return 1;
    let divisor = 1;

    const daysDiff = Math.max(1, Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1);

    switch (type) {
        case 'day':
            divisor = daysDiff;
            break;
        case 'week':
            divisor = (daysDiff / 7).toFixed(2);
            break;
        case 'month':
            let months = (end.getFullYear() - start.getFullYear()) * 12;
            months += (end.getMonth() - start.getMonth());

            const startDay = start.getDate();
            const endDay = end.getDate();
            const daysInStartMonth = new Date(start.getFullYear(), start.getMonth() + 1, 0).getDate();
            const daysInEndMonth = new Date(end.getFullYear(), end.getMonth() + 1, 0).getDate();

            if (endDay >= startDay) {
                months += (endDay - startDay) / daysInEndMonth;
            } else {
                months -= 1;
                months += (daysInStartMonth - startDay + endDay) / daysInEndMonth;
            }

            divisor = Math.max(1, parseFloat(months.toFixed(2)));
            break;
        case 'year':
            const years = end.getFullYear() - start.getFullYear();
            const totalDaysDiff = (end - start) / (1000 * 60 * 60 * 24);
            const yearCount = years + 1;
            let totalDaysInYears = 0;
            for (let i = 0; i < yearCount; i++) {
                const y = start.getFullYear() + i;
                totalDaysInYears += (y % 4 === 0 && y % 100 !== 0) || y % 400 === 0 ? 366 : 365;
            }
            const preciseYears = totalDaysDiff / totalDaysInYears * yearCount;
            divisor = Math.max(1, parseFloat(preciseYears.toFixed(2)));
            break;
    }
    return Number(divisor);
};

/**
 * 计算净支出总额
 * 支出（负数）计为正值，收入（正数）计为负值
 * 
 * @param {Array} data - 交易数据数组
 * @returns {number} 净支出总额
 */
const calculateTotalAmount = (data) => {
    return data.reduce((sum, item) => {
        const amount = Number(item.amount) || 0;
        return sum + (amount < 0 ? Math.abs(amount) : -amount);
    }, 0);
};

/**
 * 获取数据的时间范围
 * @param {Array} data - 交易数据数组
 * @returns {Object} { start: Date, end: Date }
 */
const getTimeRange = (data) => {
    const dates = data
        .map(item => new Date(item.date))
        .filter(date => !isNaN(date.getTime()))
        .sort((a, b) => a - b);

    if (dates.length === 0) return { start: null, end: null };
    return { start: dates[0], end: dates[dates.length - 1] };
};
