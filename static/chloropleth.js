// chloropleth.js

function drawChoropleth(dataJson, geoJson) {
    const width = 960, height = 600;
    const data = JSON.parse(dataJson);
    const geoData = JSON.parse(geoJson);

    const svg = d3.select("#map").append("svg")
        .attr("width", width)
        .attr("height", height);

    const projection = d3.geoMercator()
        .scale(150)
        .translate([width / 2, height / 1.5]);

    const path = d3.geoPath().projection(projection);

    const colorScale = d3.scaleSequential()
        .domain([0, d3.max(Object.values(data))])
        .interpolator(d3.interpolateBlues);

    svg.selectAll("path")
        .data(geoData.features)
        .enter()
        .append("path")
        .attr("d", path)
        .attr("class", "country")
        .attr("fill", function(d) {
            const value = data[d.properties.name];
            return value ? colorScale(value) : "#ccc";
        });

    // Legend settings
    const legendWidth = 300;
    const legendHeight = 10;

    const legend = svg.append("g")
        .attr("transform", "translate(50, 550)");

    const gradient = svg.append("defs")
        .append("linearGradient")
        .attr("id", "legend-gradient")
        .attr("x1", "0%")
        .attr("x2", "100%")
        .attr("y1", "0%")
        .attr("y2", "0%");

    gradient.append("stop")
        .attr("offset", "0%")
        .attr("stop-color", d3.interpolateBlues(0));

    gradient.append("stop")
        .attr("offset", "100%")
        .attr("stop-color", d3.interpolateBlues(1));

    legend.append("rect")
        .attr("width", legendWidth)
        .attr("height", legendHeight)
        .style("fill", "url(#legend-gradient)");

    // Legend axis
    const legendScale = d3.scaleLinear()
        .domain([0, d3.max(Object.values(data))])
        .range([0, legendWidth]);

    const legendAxis = d3.axisBottom(legendScale)
        .ticks(5)
        .tickSize(legendHeight);

    legend.append("g")
        .attr("transform", `translate(0, legendHeight)`)
        .call(legendAxis)
        .select(".domain").remove();
}