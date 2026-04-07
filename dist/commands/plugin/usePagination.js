import { useCallback, useMemo, useRef } from 'react';
const DEFAULT_MAX_VISIBLE = 5;
export function usePagination({ totalItems, maxVisible = DEFAULT_MAX_VISIBLE, selectedIndex = 0, }) {
    const needsPagination = totalItems > maxVisible;
    // Use a ref to track the previous scroll offset for smooth scrolling
    const scrollOffsetRef = useRef(0);
    // Compute the scroll offset based on selectedIndex
    // This ensures the selected item is always visible
    const scrollOffset = useMemo(() => {
        if (!needsPagination)
            return 0;
        const prevOffset = scrollOffsetRef.current;
        // If selected item is above the visible window, scroll up
        if (selectedIndex < prevOffset) {
            scrollOffsetRef.current = selectedIndex;
            return selectedIndex;
        }
        // If selected item is below the visible window, scroll down
        if (selectedIndex >= prevOffset + maxVisible) {
            const newOffset = selectedIndex - maxVisible + 1;
            scrollOffsetRef.current = newOffset;
            return newOffset;
        }
        // Selected item is within visible window, keep current offset
        // But ensure offset is still valid
        const maxOffset = Math.max(0, totalItems - maxVisible);
        const clampedOffset = Math.min(prevOffset, maxOffset);
        scrollOffsetRef.current = clampedOffset;
        return clampedOffset;
    }, [selectedIndex, maxVisible, needsPagination, totalItems]);
    const startIndex = scrollOffset;
    const endIndex = Math.min(scrollOffset + maxVisible, totalItems);
    const getVisibleItems = useCallback((items) => {
        if (!needsPagination)
            return items;
        return items.slice(startIndex, endIndex);
    }, [needsPagination, startIndex, endIndex]);
    const toActualIndex = useCallback((visibleIndex) => {
        return startIndex + visibleIndex;
    }, [startIndex]);
    const isOnCurrentPage = useCallback((actualIndex) => {
        return actualIndex >= startIndex && actualIndex < endIndex;
    }, [startIndex, endIndex]);
    // These are mostly no-ops for continuous scrolling but kept for API compatibility
    const goToPage = useCallback((_page) => {
        // No-op - scrolling is controlled by selectedIndex
    }, []);
    const nextPage = useCallback(() => {
        // No-op - scrolling is controlled by selectedIndex
    }, []);
    const prevPage = useCallback(() => {
        // No-op - scrolling is controlled by selectedIndex
    }, []);
    // Simple selection handler - just updates the index
    // Scrolling happens automatically via the useMemo above
    const handleSelectionChange = useCallback((newIndex, setSelectedIndex) => {
        const clampedIndex = Math.max(0, Math.min(newIndex, totalItems - 1));
        setSelectedIndex(clampedIndex);
    }, [totalItems]);
    // Page navigation - disabled for continuous scrolling
    const handlePageNavigation = useCallback((_direction, _setSelectedIndex) => {
        return false;
    }, []);
    // Calculate page-like values for backwards compatibility
    const totalPages = Math.max(1, Math.ceil(totalItems / maxVisible));
    const currentPage = Math.floor(scrollOffset / maxVisible);
    return {
        currentPage,
        totalPages,
        startIndex,
        endIndex,
        needsPagination,
        pageSize: maxVisible,
        getVisibleItems,
        toActualIndex,
        isOnCurrentPage,
        goToPage,
        nextPage,
        prevPage,
        handleSelectionChange,
        handlePageNavigation,
        scrollPosition: {
            current: selectedIndex + 1,
            total: totalItems,
            canScrollUp: scrollOffset > 0,
            canScrollDown: scrollOffset + maxVisible < totalItems,
        },
    };
}
