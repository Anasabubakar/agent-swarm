export default class OptionMap extends Map {
    first;
    last;
    constructor(options) {
        const items = [];
        let firstItem;
        let lastItem;
        let previous;
        let index = 0;
        for (const option of options) {
            const item = {
                label: option.label,
                value: option.value,
                description: option.description,
                previous,
                next: undefined,
                index,
            };
            if (previous) {
                previous.next = item;
            }
            firstItem ||= item;
            lastItem = item;
            items.push([option.value, item]);
            index++;
            previous = item;
        }
        super(items);
        this.first = firstItem;
        this.last = lastItem;
    }
}
