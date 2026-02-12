/**
 * 统计页面 - 数据管理模块
 * 
 * 负责数据加载、筛选逻辑的集中管理
 */
const useStatisticsData = () => {
    // 核心数据
    const allData = Vue.ref([]);
    const filteredAllData = Vue.ref([]);  // 用于图表（已剔除"不计入"账本）
    const rawFilteredData = Vue.ref([]);  // 用于表格（保留所有账本）
    const loading = Vue.ref(false);

    // 筛选表单
    const filterForm = Vue.ref({
        year: [],
        month: [],
        book: [],
        category: [],
        tag: [],
        minAmount: null,
        maxAmount: null,
        searchQuery: '', // 全局搜索关键词
        searchField: ''  // 全局搜索字段
    });

    // 下拉选项
    const yearOptions = Vue.computed(() => {
        const currentYear = new Date().getFullYear();
        return Array.from({ length: 6 }, (_, i) => currentYear - i);
    });
    const monthOptions = Array.from({ length: 12 }, (_, i) => ({
        value: i + 1,
        label: `${i + 1}月`
    }));
    const bookOptions = Vue.ref([]);
    const categoryOptions = Vue.ref([]);
    const tagOptions = Vue.ref([]);
    const allTags = Vue.ref([]);
    const categoryTagMap = Vue.ref({});
    const categoryMeta = Vue.ref({});

    // 筛选标签（用于界面展示）
    const filterTags = Vue.computed(() => {
        const tags = [];
        if (filterForm.value.year?.length) filterForm.value.year.forEach(y => tags.push({ type: 'year', label: '年份', value: y }));
        if (filterForm.value.month?.length) filterForm.value.month.forEach(m => tags.push({ type: 'month', label: '月份', value: `${m}月` }));
        if (filterForm.value.book?.length) filterForm.value.book.forEach(b => tags.push({ type: 'book', label: '账本', value: b }));
        if (filterForm.value.category?.length) filterForm.value.category.forEach(c => tags.push({ type: 'category', label: '类别', value: c }));
        if (filterForm.value.tag?.length) filterForm.value.tag.forEach(t => tags.push({ type: 'tag', label: '标签', value: t }));
        if (filterForm.value.minAmount !== null) tags.push({ type: 'minAmount', label: '最小金额', value: filterForm.value.minAmount });
        if (filterForm.value.maxAmount !== null) tags.push({ type: 'maxAmount', label: '最大金额', value: filterForm.value.maxAmount });
        if (filterForm.value.searchQuery) {
            const fieldMap = {
                '': '全部字段',
                'counter_party': '交易对方',
                'goods_desc': '商品说明',
                'category': '类别',
                'tag': '标签',
                'remark': '备注'
            };
            const fieldLabel = fieldMap[filterForm.value.searchField] || '未知字段';
            tags.push({ type: 'search', label: `搜索(${fieldLabel})`, value: filterForm.value.searchQuery });
        }
        return tags;
    });

    /**
     * 执行筛选逻辑
     */
    const applyFilters = () => {
        let filtered = [...allData.value];
        const f = filterForm.value;

        if (f.year?.length) filtered = filtered.filter(i => f.year.includes(new Date(i.date).getFullYear()));
        if (f.month?.length) filtered = filtered.filter(i => f.month.includes(new Date(i.date).getMonth() + 1));
        if (f.book?.length) filtered = filtered.filter(i => f.book.includes(i.book));
        if (f.category?.length) filtered = filtered.filter(i => f.category.includes(i.category));
        if (f.tag?.length) filtered = filtered.filter(i => f.tag.includes(i.tag));
        if (f.minAmount !== null) filtered = filtered.filter(i => i.amount >= f.minAmount);
        if (f.maxAmount !== null) filtered = filtered.filter(i => i.amount <= f.maxAmount);

        // 关键词搜索
        if (f.searchQuery) {
            const query = f.searchQuery.trim().toLowerCase();
            const field = f.searchField;
            if (query) {
                filtered = filtered.filter(item => {
                    if (field) {
                        return String(item[field] || '').toLowerCase().includes(query);
                    } else {
                        // 全字段搜索
                        return ['counter_party', 'goods_desc', 'category', 'tag', 'remark'].some(k =>
                            String(item[k] || '').toLowerCase().includes(query)
                        );
                    }
                });
            }
        }

        // 表格数据：保留所有筛选结果
        rawFilteredData.value = filtered;
        // 图表数据：剔除"不计入"账本
        filteredAllData.value = filtered.filter(i => i.book !== "不计入");
    };

    /**
     * 触发筛选更新
     */
    const handleFilter = () => {
        applyFilters();
    };

    /**
     * 重置所有筛选条件
     */
    const resetFilter = () => {
        filterForm.value = {
            year: [], month: [], book: [], category: [], tag: [], minAmount: null, maxAmount: null,
            searchQuery: '', searchField: ''
        };
        handleFilter();
    };

    /**
     * 移除单个筛选标签
     */
    const removeFilterTag = (type, value) => {
        switch (type) {
            case 'year': filterForm.value.year = filterForm.value.year.filter(v => v !== value); break;
            case 'month': filterForm.value.month = filterForm.value.month.filter(v => v !== parseInt(value)); break;
            case 'book': filterForm.value.book = filterForm.value.book.filter(v => v !== value); break;
            case 'category':
                filterForm.value.category = filterForm.value.category.filter(v => v !== value);
                filterForm.value.tag = [];
                tagOptions.value = allTags.value;
                break;
            case 'tag': filterForm.value.tag = filterForm.value.tag.filter(v => v !== value); break;
            case 'minAmount': filterForm.value.minAmount = null; break;
            case 'maxAmount': filterForm.value.maxAmount = null; break;
            case 'search': filterForm.value.searchQuery = ''; break;
        }
        handleFilter();
    };

    /**
     * 处理类别变更，联动更新标签选项
     */
    const handleCategoryChange = () => {
        filterForm.value.tag = [];
        if (filterForm.value.category?.length) {
            const allTagsForSelected = new Set();
            filterForm.value.category.forEach(c => {
                (categoryTagMap.value[c] || []).forEach(t => allTagsForSelected.add(t));
            });
            tagOptions.value = Array.from(allTagsForSelected);
        } else {
            tagOptions.value = allTags.value;
        }
        handleFilter();
    };

    /**
     * 加载分类元数据（图标、颜色）
     */
    const loadCategoryMeta = async () => {
        try {
            const response = await fetch('/api/categories');
            const data = await response.json();
            if (data.success && data.meta && typeof data.meta === 'object') {
                categoryMeta.value = data.meta;
                return;
            }
        } catch (error) {
            console.warn('加载分类元数据失败:', error);
        }
        categoryMeta.value = {};
    };

    /**
     * 从后端加载数据
     */
    const loadData = async (params = {}) => {
        loading.value = true;
        try {
            const query = new URLSearchParams(params).toString();
            const [response] = await Promise.all([
                fetch(`/api/statistics?${query}`),
                loadCategoryMeta()
            ]);
            const data = await response.json();

            if (data.success) {
                allData.value = data.all_items || [];

                // 提取下拉选项
                const books = new Set();
                const categories = new Set();
                const tags = new Set();
                const catTagMap = {};

                allData.value.forEach(item => {
                    if (item.book) books.add(item.book);
                    if (item.category) {
                        categories.add(item.category);
                        if (item.tag) {
                            if (!catTagMap[item.category]) catTagMap[item.category] = new Set();
                            catTagMap[item.category].add(item.tag);
                        }
                    }
                    if (item.tag) tags.add(item.tag);
                });

                bookOptions.value = Array.from(books).map(b => ({ value: b, label: b }));
                categoryOptions.value = Array.from(categories);
                tagOptions.value = Array.from(tags);
                allTags.value = Array.from(tags);
                Object.keys(catTagMap).forEach(k => catTagMap[k] = Array.from(catTagMap[k]));
                categoryTagMap.value = catTagMap;

                // 自动更新第一笔账单日期 (修复无痕模式下数据为空的问题)
                if (allData.value.length > 0) {
                    // 找到最早的日期
                    const minDate = allData.value.reduce((min, item) => {
                        return (item.date < min) ? item.date : min;
                    }, allData.value[0].date);

                    if (minDate) {
                        localStorage.setItem('firstBillDate', minDate);
                        // 触发界面更新
                        if (typeof initRecordDuration === 'function') {
                            initRecordDuration();
                        }
                    }
                }

                applyFilters();
            } else {
                ElementPlus.ElMessage.error(data.error || '加载数据失败');
            }
        } catch (error) {
            console.error('加载数据失败:', error);
            ElementPlus.ElMessage.error('加载数据失败');
        } finally {
            loading.value = false;
        }
    };

    return {
        allData,
        filteredAllData,
        rawFilteredData,
        loading,
        filterForm,
        yearOptions,
        monthOptions,
        bookOptions,
        categoryOptions,
        tagOptions,
        categoryMeta,
        filterTags,
        loadData,
        handleFilter,
        resetFilter,
        removeFilterTag,
        handleCategoryChange
    };
};
