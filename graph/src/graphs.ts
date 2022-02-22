import * as d3 from "d3";

export interface HierarchyDatum {
    name: string;
    distance: number;
    metadata: {
        [key: string]: any;
        _image: string;
        _maskFile?: string;
        _objects?: { [key: string]: number };
    };
    family: boolean;
    familyRoot: boolean;
    children?: Array<HierarchyDatum>;
    merged_children?: d3.HierarchyNode<HierarchyDatum>[];
}

export interface PositionedHierarchyNode
    extends d3.HierarchyNode<HierarchyDatum> {
    x: number;
    y: number;
}

abstract class ClusterGraph {
    protected root: d3.HierarchyNode<HierarchyDatum>;
    protected graph: d3.Selection<SVGGElement, unknown, HTMLElement, any>;
    protected flatteningValueInput: HTMLInputElement;
    protected modelInput: HTMLSelectElement;
    protected models: { [name: string]: HierarchyDatum };
    protected nodeNameInput: HTMLInputElement;
    protected colorNodeInput: HTMLInputElement;
    protected size: [number, number];

    protected nodeSize = 4;
    protected lineWidth = 1;

    protected updateTimeout: number | undefined;

    protected svg: d3.Selection<d3.BaseType, unknown, HTMLElement, any>;
    protected svgBounds: ClientRect | DOMRect;
    protected zoom: d3.ZoomBehavior<Element, unknown>;

    /**
     * Abstract graph
     * @param root: The hierarchy root
     * @param graph: The svg graph element
     * @param flatteningValueInput: The HTML element that controls the flattening distance
     * @param modelInput: The HTML element for available models
     * @param models: The available models to display
     * @param size: Dimensions of the graph
     */
    constructor(
        root: d3.HierarchyNode<HierarchyDatum>,
        graph: d3.Selection<SVGGElement, unknown, HTMLElement, any>,
        flatteningValueInput: HTMLInputElement,
        modelInput: HTMLSelectElement,
        models: { [name: string]: HierarchyDatum },
        size: [number, number]
    ) {
        this.root = root;
        this.graph = graph;
        this.flatteningValueInput = flatteningValueInput;
        this.modelInput = modelInput;
        this.models = models;
        this.size = size;

        // Update graph when flattening changes
        flatteningValueInput.addEventListener("input", () => {
            this.eventDelay(this.updateFlattening.bind(this));
        });

        // Update graph when model changes
        modelInput.addEventListener("change", () => {
            this.eventDelay(this.updateModel.bind(this));
        });

        this.nodeNameInput = document.querySelector(
            "#nodeName"
        ) as HTMLInputElement;
        this.nodeNameInput.addEventListener("keyup", (event) => {
            if (event.key === "Enter")
                this.eventDelay(this.selectCluster.bind(this));
        });
        this.colorNodeInput = document.querySelector(
            "#colorNode"
        ) as HTMLInputElement;
        this.colorNodeInput.addEventListener("keyup", (event) => {
            if (event.key === "Enter")
                this.eventDelay(this.runColorGraph.bind(this));
        });
        // Run first draw
        this.draw(this.root);

        // Add zooming
        this.svg = d3.select("svg");
        this.svgBounds = (
            this.svg.node() as HTMLElement
        ).getBoundingClientRect();
        this.zoom = d3
            .zoom()
            .extent([
                [0, 0],
                [this.svgBounds.width, this.svgBounds.height],
            ])
            .scaleExtent([1, 100])
            .on("zoom", () => {
                const currentTransform = d3.event.transform;

                this.graph
                    .selectAll("circle")
                    .attr("r", this.nodeSize / currentTransform.k);

                this.graph
                    .selectAll("line")
                    .attr("stroke-width", this.lineWidth / currentTransform.k);
                const { transform } = d3.event;
                this.graph.attr("transform", transform);
                this.graph.attr("stroke-width", 1 / transform.k);
            });
        this.svg.call(this.zoom);
        d3.select("#zoomReset").on("click", () => {
            this.svg.call(this.zoom.transform, d3.zoomIdentity.scale(1));
        });
    }

    /**
     * Draw the graph
     */
    abstract draw(root: d3.HierarchyNode<HierarchyDatum>): void;

    /**
     * Re-draw the graph using transitions
     */
    abstract redraw(): void;

    /**
     * Add graph-specific options
     */
    abstract addOptions(): void;

    /**
     * Update the graph based on the flattening distance
     */
    abstract updateFlattening(): void;

    /**
     * Update the graph based on the model
     */
    abstract updateModel(): void;

    /**
     * Update the graph based on the top node number of a cluster
     */
    abstract selectCluster(): void;

    /**
     * run colorGraph
     */
    abstract runColorGraph(): void;

    /**
     * Update the graph based on whether to compact clusters
     */
    abstract updateCompact(): void;

    /**
     * Merge a node's parent with its children when it meets a specified distance
     * @param node
     * @param distance
     */
    protected mergeNode(
        node: d3.HierarchyNode<HierarchyDatum>,
        distance: number
    ) {
        // Validate parent and distance
        const parent = node.parent;
        if (parent !== null && parent.parent !== null) {
            if (parent.data.distance <= distance) {
                if (parent.children === undefined || parent.children === null) {
                    return;
                }

                // Empty children
                parent.data.merged_children = parent.children.slice();
                parent.children = null;
                this.mergeNode(parent, distance);
            }
        }
    }

    /**
     * Generate n colours
     */
    protected colours(n: number) {
        const colours: number[] = [];
        const baseColour = 360 / n;
        for (let i = 0; i < n; i++) {
            // colours.push("hsl(" + (i * baseColour % 360) + ",100%,50%)");
            colours.push((i * baseColour) % 360);
        }
        return colours;
    }

    protected getColour(
        colorMap: { [key: string]: number },
        categoryMap: { [key: string]: number }
    ) {
        let finalColor = 0;
        for (const [key, value] of Object.entries(categoryMap)) {
            if (key == "total") continue;
            finalColor +=
                (categoryMap[key] / categoryMap["total"]) * colorMap[key];
        }
        return "hsl(" + finalColor + ",100%,50%)";
    }

    /**
     * Clear the graph canvas
     */
    protected clear() {
        this.graph.selectAll("*").remove();
    }

    /**
     * Delay events during input
     */
    private eventDelay(callback: () => void) {
        clearTimeout(this.updateTimeout);
        this.updateTimeout = window.setTimeout(() => {
            callback();
        }, 500);
    }
}

export class Dendrogram extends ClusterGraph {
    private tree: d3.ClusterLayout<unknown> = d3.cluster();
    private flatRoot: d3.HierarchyNode<HierarchyDatum> = undefined;

    addOptions() {}

    draw(root: d3.HierarchyNode<HierarchyDatum>) {
        // Create cluster tree
        this.tree = d3.cluster().size(this.size);
        this.tree(root);

        this.createLinks(root);
        this.createNodes(root);

        this.readParams(root);
    }

    /**
     * Create the canvas nodes
     */
    private createNodes(root: d3.HierarchyNode<HierarchyDatum>) {
        let nodeHoverTimer: NodeJS.Timeout;

        // console.log(root)
        this.graph.append("g").classed("nodes", true);
        d3.select("svg g.nodes")
            .selectAll("circle.node")
            .data(root.descendants())
            .enter()
            .append("circle")
            .classed("node", true)
            .attr("cx", (d: PositionedHierarchyNode) => d.x)
            .attr("cy", (d: PositionedHierarchyNode) => d.y)
            .attr("r", this.nodeSize)
            .on("mouseover", (n) => {
                nodeHoverTimer = setTimeout(() => {
                    this.displayMetadata(n);
                    this.colourFamily(n);
                }, 500);
            })
            .on("mouseleave", () => {
                clearTimeout(nodeHoverTimer);
            })
            .on("click", (n) => {
                this.displayMetadata(n);
                this.updateZoom(n);
            });
    }

    /**
     * Create the canvas links
     */
    private createLinks(root: d3.HierarchyNode<HierarchyDatum>) {
        this.graph.append("g").classed("links", true);
        d3.select("svg g.links")
            .selectAll("line.link")
            .data(root.links())
            .enter()
            .append("line")
            .classed("link", true)
            .attr("x1", (d: any) => d.source.x)
            .attr("y1", (d: any) => d.source.y)
            .attr("x2", (d: any) => d.target.x)
            .attr("y2", (d: any) => d.target.y)
            .attr("stroke-width", this.lineWidth);
    }

    redraw() {
        console.log("redraw dendrogram");
    }

    updateCompact() {
        console.log("compact update");
    }

    updateFlattening() {
        // Get flattening value
        const flatDistance = parseFloat(this.flatteningValueInput.value);

        // Create copy of root
        this.flatRoot = d3.hierarchy(this.root.data);
        this.flatRoot.descendants().map((d) => (d.data.merged_children = []));

        // Recursively merge leaves
        const leaves = this.flatRoot.leaves();
        for (const node of leaves) {
            this.mergeNode(node, flatDistance);
        }

        // Draw flattened tree
        this.clear();
        this.draw(this.flatRoot);
    }

    updateModel() {
        // Get flattening value
        this.root = d3.hierarchy(this.models[this.modelInput.value]);

        // Draw flattened tree
        this.clear();
        this.draw(this.root);
    }

    selectCluster() {
        const nodeName = this.nodeNameInput.value;
        if (nodeName) {
            for (const node of this.root.descendants()) {
                if (node.data.name.toString() === nodeName) {
                    d3.select("svg g.nodes")
                        .selectAll("circle.node")
                        // @ts-ignore
                        .filter((n) => n.data.name.toString() === nodeName)
                        .dispatch("mouseover"); // to zoom in, change to 'click'
                    this.displayMetadata(node);
                    // this.updateZoom(node);  // to zoom in
                }
            }
        }
        this.displayMetadata(this.root);
    }

    updateZoom(n: d3.HierarchyNode<HierarchyDatum>) {
        d3.event.stopPropagation();

        const parent = n.parent as PositionedHierarchyNode;
        let x0 = +Infinity;
        let x1 = -Infinity;
        let y0 = +Infinity;
        let y1 = -Infinity;

        function getPositions(node: PositionedHierarchyNode) {
            if (node.x < x0) {
                x0 = node.x;
            }
            if (node.x > x1) {
                x1 = node.x;
            }
            if (node.y < y0) {
                y0 = node.y;
            }
            if (node.y > y1) {
                y1 = node.y;
            }
            if ("children" in node && node.children !== null) {
                for (const child of node.children) {
                    getPositions(child);
                }
            }
        }

        getPositions(parent);

        const scale = Math.min(
            100,
            0.9 /
                Math.max(
                    (x1 - x0) / this.svgBounds.width,
                    (y1 - y0) / this.svgBounds.height
                )
        );
        const translation = [-(x0 + x1) / 2, -(y0 + y1) / 2];

        this.svg
            .transition()
            .duration(1000)
            .call(
                // @ts-ignore
                this.zoom.transform,
                d3.zoomIdentity
                    .translate(
                        this.svgBounds.width / 2,
                        this.svgBounds.height / 2
                    )
                    .scale(scale)
                    .translate(translation[0], translation[1]),
                // @ts-ignore
                d3.mouse(this.svg.node())
            );
    }

    displayMetadata(rootNode: d3.HierarchyNode<HierarchyDatum>) {
        // Update url
        const url = new URL(window.location.href);
        url.searchParams.set("node", rootNode.data.name);
        window.history.pushState("selectNode", "", url.toString());

        // Get descendants
        const descendents: d3.HierarchyNode<HierarchyDatum>[] = [];

        function addDescendents(node: d3.HierarchyNode<HierarchyDatum>) {
            descendents.push(node);
            if ("children" in node && node.children !== null) {
                for (const child of node.children) {
                    addDescendents(child);
                }
            }
            if (
                "merged_children" in node.data &&
                node.data.merged_children !== null
            ) {
                for (const child of node.data.merged_children) {
                    addDescendents(child);
                }
            }
        }
        addDescendents(rootNode);

        // Get options
        const gallerySamplesElement = document.querySelector(
            "#gallerySamples"
        ) as HTMLSelectElement;
        const galleryMasksElement = document.querySelector(
            "#galleryMasks"
        ) as HTMLSelectElement;
        const showSample = gallerySamplesElement.selectedIndex == 0;
        const showMasks = galleryMasksElement.selectedIndex == 1;
        d3.select(gallerySamplesElement).on("change", () => {
            this.displayMetadata(rootNode);
        });
        d3.select(galleryMasksElement).on("change", () => {
            this.displayMetadata(rootNode);
        });

        // Add statistics
        this.nodeNameInput.value = rootNode.data.name;
        document.querySelector("#leafCount").innerHTML =
            descendents.length.toString();
        document.querySelector("#descendantDistance").innerHTML = d3
            .median(
                descendents
                    .filter((n) => n.data.children.length > 0)
                    .map((n) => n.data.distance)
            )
            .toString();

        // Add gallery
        const imageList: string[] = [];
        const imageListLength = 20;
        // const hashTags: Set<string> = new Set();
        // const hashTags: string[] = [];
        const hashTags: { [key: string]: any } = {};
        // //display all keys
        // var metaData: { [key: string]: any } = {};

        // function findMetadataKeys(datum: HierarchyDatum) {
        //     if (datum.children && !datum.children[0].children) {
        //         console.log(datum.children[0].metadata.node);
        //         return datum.children[0].metadata.node;
        //     }
        //     findMetadataKeys(datum.children[0]);
        // }
        // // const keys = findMetadataKeys(rootNode.data)
        // // console.log(keys)
        // metaData = findMetadataKeys(rootNode.data);
        // console.log(metaData);
        var clusterIds: { [key: string]: any } = {};

        function imageToClusterIds(
            node: d3.HierarchyNode<HierarchyDatum>,
            prevClusters: string
        ) {
            if (node.children) {
                for (const child of node.children) {
                    imageToClusterIds(
                        child,
                        prevClusters + "," + node.data.name
                    );
                }
            } else {
                clusterIds[node.data.metadata._mediaPath[0]] =
                    prevClusters + "," + node.data.name;
            }
        }
        // const keys = findMetadataKeys(rootNode.data)
        // console.log(keys)
        imageToClusterIds(rootNode, "");
        // print to console
        for (var key in clusterIds) {
            // check if the property/key is defined in the object itself, not in parent
            console.log(key, clusterIds[key]);
        }
        //export to json
        d3.select("#exportClusterIdsButton").on("click", () => {
            const dlAnchorElem = document.getElementById(
                "downloadAnchorElem"
            ) as HTMLLinkElement;
            dlAnchorElem.href = URL.createObjectURL(
                new Blob([JSON.stringify(clusterIds)], {
                    type: "application/json",
                })
            );
            dlAnchorElem.setAttribute("download", "clusterIds.txt");
            dlAnchorElem.click();
        });

        const findMedia = (datum: HierarchyDatum) => {
            if (showMasks) {
                if (datum.metadata._maskFile) {
                    imageList.push(datum.metadata._maskFile);
                }
            } else {
                if (datum.metadata._mediaPath) {
                    // imageList.push(datum.metadata._image);
                    imageList.push(
                        datum.metadata._mediaPath[0].replace("\\\\", "/")
                    );
                }
                if (datum.metadata.node) {
                    //for other metadata
                    if (datum.metadata.node.all_hashtags) {
                        datum.metadata.node.all_hashtags
                            .split(",")
                            .forEach((item: string) => {
                                if (item == "''") {
                                    return;
                                }
                                item = item.trim().slice(1, -1);
                                var path: String = datum.metadata._mediaPath[0];
                                path = path.split("/").pop().split(".")[0];
                                if (item in hashTags) {
                                    hashTags[item]["counter"] += 1;
                                    hashTags[item]["origin"] = hashTags[item][
                                        "origin"
                                    ].concat([path]);
                                } else {
                                    hashTags[item] = {};
                                    hashTags[item]["counter"] = 1;
                                    hashTags[item]["origin"] = [path];
                                }
                            });
                    }
                }
            }
            if (imageList.length < imageListLength || !showSample) {
                for (const child of datum.children) {
                    findMedia(child);
                }
                if ("merged_children" in datum) {
                    for (const child of datum.merged_children) {
                        findMedia(child.data);
                    }
                }
            }
        };
        findMedia(rootNode.data);
        // // combine hastag key and value
        // for (var key in hashTags) {
        //     // check if the property/key is defined in the object itself, not in parent
        //     console.log(key, hashTags[key]);
        // }
        const hashtags = d3.select("#hashTags");
        hashtags.selectAll("div").remove();
        hashtags
            .selectAll("div")
            .data(Object.keys(hashTags))
            // .data(Array.from(hashTags))
            .enter()
            .append("div")
            .classed("hashtag", true)
            .text((d) => {
                return d + " " + hashTags[d]["counter"];
            })
            .on("mouseover", (d) => {
                hoverTimeout = setTimeout(() => {
                    const highlight = hashTags[d]["origin"];
                    highlight.forEach((e: String) => {
                        d3.select("#" + e).style("border-color", "yellow");
                    });
                }, 100);
            })
            .on("mouseleave", (d) => {
                clearTimeout(hoverTimeout);
                const highlight = hashTags[d]["origin"];
                highlight.forEach((e: String) => {
                    d3.select("#" + e).style("border-color", "#2e2e2e");
                });
            });
        const imageGallery = d3.select("#imageGallery");
        let hoverTimeout: NodeJS.Timeout;
        imageGallery.selectAll("div").remove();
        imageGallery
            .selectAll("div")
            .data(imageList)
            .enter()
            .append("div")
            .on("mouseover", (d) => {
                hoverTimeout = setTimeout(() => {
                    d3.select("#imagePopup")
                        .style("display", "block")
                        .style(
                            "background-image",
                            `url(${d.replace("\\\\", "/")})`
                        );
                }, 500);
            })
            .on("mouseleave", () => {
                clearTimeout(hoverTimeout);
                d3.select("#imagePopup").style("display", "none");
            })
            .append("img")
            .attr("src", (d) => {
                return d;
            })
            .attr("id", (d) => {
                return d.split("/").pop().split(".")[0];
            })
            .attr("loading", "lazy");

        findMedia(rootNode.data);
        // Bind export
        d3.select("#exportButton").on("click", () => {
            console.log("exporting");
            const data = descendents
                .filter((d) => Object.keys(d.data.metadata).length > 0)
                .map((d) => d.data.metadata);

            const dlAnchorElem = document.getElementById(
                "downloadAnchorElem"
            ) as HTMLLinkElement;
            dlAnchorElem.href = URL.createObjectURL(
                new Blob([JSON.stringify(data)], {
                    type: "application/json",
                })
            );
            dlAnchorElem.setAttribute("download", "clusters.json");
            dlAnchorElem.click();
        });

        // Add objects
        const objects: {
            [key: string]: { probabilities: number[]; count: number };
        } = {};
        for (const node of descendents) {
            if ("_objects" in node.data.metadata) {
                for (const object in node.data.metadata._objects) {
                    if (object in objects) {
                        objects[object].count += 1;
                        objects[object].probabilities.push(
                            node.data.metadata._objects[object]
                        );
                    } else {
                        objects[object] = {
                            probabilities: [
                                node.data.metadata._objects[object],
                            ],
                            count: 1,
                        };
                    }
                }
            }
        }

        //TODO
        const objectTableData = d3.select("#objectsTable").select("tbody");
        objectTableData.selectAll("tr").remove();
        const objectTableRows = objectTableData
            .selectAll("tr")
            .data(
                Object.entries(objects).sort((a, b) => b[1].count - a[1].count)
            )
            .enter()
            .append("tr");

        objectTableRows.append("td").html((d) => d[0]);

        objectTableRows.append("td").html((d) => d[1].count.toString());

        objectTableRows
            .append("td")
            .html((d) => d3.median(d[1].probabilities).toString());
    }

    runColorGraph() {
        const attributeName = this.colorNodeInput.value.split(",")[0];
        const colorDimension = parseInt(
            this.colorNodeInput.value.split(",")[1]
        );
        const colors = this.colours(colorDimension);
        const colorMap: { [key: string]: number } = {};
        const nodeCategories: { [key: string]: { [key: string]: any } } = {};
        // d3.select("svg g.nodes")
        //     .selectAll("circle.node")
        //     // @ts-ignore
        //     .filter((n) => n.data.name.toString() === nodeName)
        //     // .dispatch("mouseover"); // to zoom in, change to 'click'
        this.colorGraph(
            this.root.data,
            attributeName,
            nodeCategories,
            colors,
            colorMap
        );
        console.log(nodeCategories);
        console.log(colors);
        console.log(colorMap);
        let legendBox = document.querySelector("#colorCode");
        legendBox.innerHTML = "";
        for (const [key, value] of Object.entries(colorMap)) {
            let node: HTMLDivElement = document.createElement("div");
            let colorBox = document.createElement("div");
            colorBox.id = "colorBox";
            colorBox.style.backgroundColor = "hsl(" + value + ",100%,50%)";
            let keyText = document.createElement("p");
            keyText.innerHTML = key;
            node.appendChild(colorBox);
            node.appendChild(keyText);
            legendBox.appendChild(node);
        }
        d3.select("svg g.nodes")
            .selectAll("circle.node")
            .data(this.root.descendants())
            .style("fill", (n) => {
                if (n.data.metadata.color) {
                    return n.data.metadata.color;
                }
            });
        // this.updateZoom(node);  // to zoom in
    }

    colorGraph(
        datum: HierarchyDatum,
        key_attr: string,
        nodeCategories: { [key: string]: { [key: string]: any } },
        colors: number[],
        colorMap: { [key: string]: number }
    ) {
        // update graph color based on an attribute
        let categories: { [key: string]: any } = { total: 0 };
        // leaf nodes
        if (datum.metadata.node) {
            if (datum.metadata.node[key_attr] != null) {
                String(datum.metadata.node[key_attr])
                    .split(",")
                    .forEach((item: string) => {
                        // claim a color
                        if (!(item in colorMap)) {
                            colorMap[item] = colors.pop();
                        }
                        if (item in categories) {
                            categories[item] += 1;
                        } else {
                            categories[item] = 1;
                        }
                        categories["total"] += 1;
                    });
            }
        }
        // parent
        else {
            // left child
            const leftChild: HierarchyDatum = datum.children[0];
            if (!nodeCategories[leftChild.name]) {
                this.colorGraph(
                    leftChild,
                    key_attr,
                    nodeCategories,
                    colors,
                    colorMap
                );
            }
            const leftCategories = nodeCategories[leftChild.name];
            for (const [key, value] of Object.entries(leftCategories)) {
                if (key in categories) {
                    categories[key] += value;
                } else {
                    categories[key] = value;
                }
                // categories['total'] += value;
            }
            const rightChild: HierarchyDatum = datum.children[1];
            if (!nodeCategories[rightChild.name]) {
                this.colorGraph(
                    rightChild,
                    key_attr,
                    nodeCategories,
                    colors,
                    colorMap
                );
            }
            const rightCategories = nodeCategories[rightChild.name];
            for (const [key, value] of Object.entries(rightCategories)) {
                if (key in categories) {
                    categories[key] += value;
                } else {
                    categories[key] = value;
                }
                // categories['total'] += value;
            }
            // if ("merged_children" in datum) {
            //     for (const child of datum.merged_children) {
            //         this.colorGraph(child.data, key_attr, categories);
            //     }
            // }
        }
        nodeCategories[datum.name] = categories;
        datum.metadata.color = this.getColour(colorMap, categories);
        // console.log(datum.name+" "+this.getColour(colorMap, categories))
    }

    private colourFamily(familyRoot: d3.HierarchyNode<HierarchyDatum>) {
        function nodeColour(
            node: d3.HierarchyNode<HierarchyDatum>,
            family: boolean
        ) {
            let foundFamilyRoot: boolean = false;
            if (!family) {
                if (node === familyRoot) {
                    foundFamilyRoot = true;
                    family = true;
                } else {
                    family = false;
                }
            }
            if (node.children) {
                for (const child of node.children) {
                    nodeColour(child, family);
                }
            }
            node.data.familyRoot = foundFamilyRoot;
            node.data.family = family;
        }
        const root = this.flatRoot ? this.flatRoot : this.root;
        nodeColour(root, false);

        // const colors = this.colours(3);

        d3.select("svg g.nodes")
            .selectAll("circle.node")
            .data(root.descendants())
            .style("fill", (n) => {
                if (n.data.metadata.color) {
                    return n.data.metadata.color;
                } else if (n.data.familyRoot) {
                    return "#ff624a";
                } else if (n.data.family) {
                    return "#fff53e";
                } else {
                    return "rgba(255,245,62,0.1)";
                }
            });
        d3.select("svg g.links")
            .selectAll("line.link")
            .data(root.links())
            .style("stroke", (n) => {
                if (n.source.data.familyRoot) {
                    return "#ff624a";
                } else if (n.source.data.family) {
                    return "#ccc";
                } else {
                    return "rgba(204,204,204,0.11)";
                }
            });
    }

    private readParams(root: d3.HierarchyNode<HierarchyDatum>) {
        const url = new URL(window.location.href);
        const nodeName = url.searchParams.get("node");
        if (nodeName) {
            for (const node of root.descendants()) {
                if (node.data.name.toString() === nodeName) {
                    d3.select("svg g.nodes")
                        .selectAll("circle.node")
                        // @ts-ignore
                        .filter((n) => n.data.name.toString() === nodeName)
                        .dispatch("mouseover");
                    this.displayMetadata(node);
                }
            }
        }
        this.displayMetadata(root);
    }
}
