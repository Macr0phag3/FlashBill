/**
 * 统计页面 - 时间线 Tab 模块
 */
const useTimelineTab = () => {
    const timelineData = Vue.ref({});      // 按日期分组的展示数据
    const timelineArray = Vue.ref([]);      // 扁平化数组（用于分页）
    const timelinePageSize = Vue.ref(3);    // 每次加载3天的数据
    const timelineCurrentPage = Vue.ref(1);
    const timelineTotalPages = Vue.ref(1);
    const isLoadingMore = Vue.ref(false);
    const isAllLoaded = Vue.ref(false);

    /** 更新当前页的展示数据 */
    const updateTimelineDisplay = () => {
        const currentData = {};
        const end = timelineCurrentPage.value * timelinePageSize.value;
        const currentPageData = timelineArray.value.slice(0, end);

        currentPageData.forEach(entry => {
            currentData[entry.dateStr] = {
                total: entry.total,
                items: entry.items
            };
        });

        timelineData.value = currentData;
        isAllLoaded.value = timelineCurrentPage.value >= timelineTotalPages.value;
    };

    /** 处理原始数据为时间线格式 */
    const updateTimelineData = (data) => {
        // 按日期分组
        const groupedData = {};
        data.forEach(item => {
            if (!item.date) return;
            const dateKey = formatDate(item.date);
            if (!groupedData[dateKey]) {
                groupedData[dateKey] = { total: 0, items: [] };
            }
            groupedData[dateKey].items.push(item);
            groupedData[dateKey].total += Math.abs(Number(item.amount) || 0);
        });

        // 按日期倒序排列
        const dateEntries = Object.entries(groupedData).map(([dateStr, entryData]) => ({
            date: new Date(dateStr),
            dateStr: dateStr,
            total: entryData.total,
            items: entryData.items
        }));
        dateEntries.sort((a, b) => b.date - a.date);

        // 每天内按时间倒序排列
        dateEntries.forEach(entry => {
            entry.items.sort((a, b) => new Date(b.date) - new Date(a.date));
        });

        timelineArray.value = dateEntries;
        timelineTotalPages.value = Math.ceil(dateEntries.length / timelinePageSize.value) || 1;
        timelineCurrentPage.value = 1;
        isAllLoaded.value = false;
        updateTimelineDisplay();
    };

    /** 加载更多数据 */
    const loadMoreData = () => {
        if (isLoadingMore.value || isAllLoaded.value) return;

        isLoadingMore.value = true;
        setTimeout(() => {
            timelineCurrentPage.value++;
            updateTimelineDisplay();
            isLoadingMore.value = false;
        }, 500);
    };

    /** 滚动事件处理（无限滚动） */
    const handleScroll = (event) => {
        const { scrollTop, scrollHeight, clientHeight } = event.target;
        if (scrollHeight - scrollTop - clientHeight < 200) {
            loadMoreData();
        }
    };

    return {
        timelineData,
        timelineArray,
        timelinePageSize,
        timelineCurrentPage,
        timelineTotalPages,
        isLoadingMore,
        isAllLoaded,
        updateTimelineDisplay,
        updateTimelineData,
        loadMoreData,
        handleScroll
    };
};
