import { ClusterGraph, Dendrogram, HierarchyDatum } from "./graphs";
// import { BubbleGraph } from "./bubble";
import * as d3 from "d3";

/**
 * Manage graph
 */
class ClusterGraphContainer {
    // Raw JSON data
    private data: HierarchyDatum = {
        name: "",
        distance: 0,
        children: [],
        metadata: {
            _image: "",
        },
        family: false,
        familyRoot: false,
    };

    private models: { [name: string]: HierarchyDatum };

    // Hierarchy root
    private root = d3.hierarchy(this.data);

    // Graph container
    private container = d3.select("#left");

    // Container size
    private containerNode = <HTMLElement>this.container.node();

    private containerSize: [number, number] = [
        this.containerNode.offsetWidth,
        this.containerNode.offsetHeight,
    ];

    // Graph elements
    private svg = this.container.append("svg");

    private graph = this.svg.append("g");

    // Input elements
    private flatValueElement = <HTMLInputElement>(
        document.querySelector("#flatValue")
    );
    // private compactElement = <HTMLInputElement>document.querySelector("#compactCheck");

    // Cluster visualiser
    private clusterElement = <HTMLDivElement>(
        document.querySelector("#clusters")
    );
    private modelElement = <HTMLSelectElement>(
        document.querySelector("#models-dropdown")
    );

    // Viz options container
    private vizOptions = document.querySelectorAll(
        ".viz-nav a"
    ) as NodeListOf<HTMLAnchorElement>;

    // private dendogram: Dendrogram;

    // private bubblegraph: BubbleGraph;

    public async run() {
        // this.setupVizTypeListener();
        await this.getData();
        this.createData();
        this.maxClusterDistance();
        new Dendrogram(
            this.root,
            this.graph,
            this.flatValueElement,
            this.modelElement,
            this.models,
            this.containerSize
        );
    }

    // /**
    //  * Set up visualisation type listener
    //  */
    // private setupVizTypeListener() {
    //     this.vizOptions.forEach((viz) => {
    //         viz.addEventListener("click", (e) => {
    //             e.preventDefault();
    //             this.selectViz(viz);
    //         });
    //     });
    // }

    // private selectViz(vizOption: HTMLAnchorElement) {
    //     if (!vizOption.classList.contains("selected")) {
    //         let prevViz = [...this.vizOptions].filter((viz) =>
    //             viz.classList.contains("selected")
    //         )[0];
    //         prevViz.classList.toggle("selected");
    //         vizOption.classList.toggle("selected");
    //         //update visualization
    //         this.updateViz(parseInt(vizOption.getAttribute("value")));
    //     }
    // }

    // private updateViz(vizType: Number) {
    //     switch (vizType) {
    //         case 0:
    //             //display dendogram
    //             console.log("dendogram");
    //             this.displayViz("dendogram");
    //             break;
    //         case 1:
    //             //display bubble
    //             console.log("bubble");
    //             this.displayViz("bubble");
    //             break;
    //         default:
    //             //display dendogram
    //             console.log("dendogram");
    //             this.displayViz("dendogram");
    //     }
    // }

    // private displayViz(vizType: String) {
    //     if ((vizType = "dendogram")) {
    //         this.graph.selectAll("*").remove();
    //         this.dendogram.draw(this.root);
    //     }
    //     if ((vizType = "bubble")) {
    //         this.graph.selectAll("*").remove();
    //         this.bubblegraph.draw(this.root);
    //     }
    // }

    /**
     * Retrieve JSON data
     */
    private async getData() {
        const popup = d3.select("#fetchPopup").style("display", "block");
        const timer = setInterval(() => {
            popup.append("span").html(". ");
        }, 1000);
        const response = await fetch("clusters_dendogram.json");
        this.models = await response.json();
        var keys = Object.keys(this.models);
        //available models
        let option;
        for (let i = 0; i < keys.length; i++) {
            option = document.createElement("option");
            option.text = keys[i];
            option.value = keys[i];
            this.modelElement.add(option);
        }
        this.data = this.models[keys[0]];
        popup.style("display", "none");
        clearTimeout(timer);
    }

    /**
     * Create initial data structures
     */
    private createData() {
        this.root = d3.hierarchy(this.data);
    }

    /**
     * Calculate the maximum cluster distance for input slider
     */
    private maxClusterDistance() {
        d3.select("#flatSlider")
            .attr(
                "min",
                d3.min(this.root.descendants(), (d) => d.data.distance) || 0
            )
            .attr(
                "max",
                d3.max(this.root.descendants(), (d) => d.data.distance) || 0
            );
    }

    private createClusterTable(clusters: Array<HierarchyDatum>) {
        const clusterContainer = d3.select(this.clusterElement);
    }
}

window.onload = () => {
    const container = new ClusterGraphContainer();
    (async () => {
        await container.run();
    })();
};
