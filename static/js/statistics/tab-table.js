/**
 * 统计页面 - 表格 Tab 模块
 */
const useTableTab = (updateCallback) => {
    const tableData = Vue.ref([]);
    const loading = Vue.ref(false);
    const currentPage = Vue.ref(1);
    const pageSize = Vue.ref(20);
    const total = Vue.ref(0);
    const sortBy = Vue.ref('date');
    const sortOrder = Vue.ref('desc');

    const tableFreqSortField = Vue.ref(''); // 频率排序字段
    const tableFreqSortEmptyLast = Vue.ref(false); // 空值置底 (默认关闭)

    /** 每页条数变更 */
    const handleSizeChange = (val) => {
        pageSize.value = val;
        currentPage.value = 1;
        if (updateCallback) updateCallback();
    };

    /** 页码变更 */
    const handleCurrentChange = (val) => {
        currentPage.value = val;
        if (updateCallback) updateCallback();
    };

    /** 排序变更 */
    const handleSortChange = ({ prop, order }) => {
        if (!order) {
            sortBy.value = 'date';
            sortOrder.value = 'desc';
        } else {
            sortBy.value = prop;
            sortOrder.value = order === 'ascending' ? 'asc' : 'desc';
        }
        if (updateCallback) updateCallback();
    };

    /** 搜索/频率排序变更 */
    const handleTableSearch = () => {
        currentPage.value = 1;
        if (updateCallback) updateCallback();
    };

    return {
        tableData,
        loading,
        currentPage,
        pageSize,
        total,
        sortBy,
        sortOrder,
        tableFreqSortField,
        tableFreqSortEmptyLast,
        handleSizeChange,
        handleCurrentChange,
        handleSortChange,
        handleTableSearch
    };
};
