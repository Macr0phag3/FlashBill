/**
 * 公共工具函数
 * 
 * 提供格式化、日期处理等通用功能
 */

// ==================== 格式化函数 ====================

/**
 * 格式化金额为两位小数
 * @param {number|string} amount - 金额
 * @returns {string} 格式化后的金额字符串
 */
function formatAmount(amount) {
    if (amount === null || amount === undefined) return '0.00';
    return Number(amount).toFixed(2);
}

/**
 * 格式化日期为 YYYY-MM-DD
 * @param {string|Date} dateStr - 日期字符串或 Date 对象
 * @returns {string} 格式化后的日期字符串
 */
function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return dateStr;

    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');

    return `${year}-${month}-${day}`;
}

/**
 * 格式化时间为 HH:MM:SS
 * @param {string|Date} dateStr - 日期时间字符串或 Date 对象
 * @returns {string} 格式化后的时间字符串
 */
function formatTime(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return dateStr;

    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');

    return `${hours}:${minutes}:${seconds}`;
}

/**
 * 获取账本标签类型（用于 Element Plus Tag 组件）
 * @param {string} book - 账本名称
 * @returns {string} 标签类型
 */
function getBookTagType(book) {
    const bookMap = {
        '日常开销': "",
        '旅游基金': 'success',
        '私房钱': 'warning',
        '房租': 'danger',
        '不计入': 'info',
        '大事资金': 'warning',
    };
    return bookMap[book] || '';
}

// ==================== 导出（用于模块化环境） ====================
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { formatAmount, formatDate, formatTime, getBookTagType };
}
