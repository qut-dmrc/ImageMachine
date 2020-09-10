class FlatteningValue {
    private element: HTMLElement;
    private values: number[];
    private readonly min: number;
    private readonly max: number;

    constructor(element: HTMLElement, values: number[]) {
        this.element = element;
        this.values = values;

        values.sort((a, b) => a - b);

        this.min = 0;
        for (const value of values) {
            if (value > 0) {
                this.min = value;
                break;
            }
        }
        this.max = values[values.length - 1];

        this.createElements()
    }

    private createElements() {
    }
}
