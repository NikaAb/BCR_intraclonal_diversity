/* ********************************************************* TREE ************************************************************* */

function displayTree(dataTree){
  d3.select("#chart1 svg").remove();

  dataClonotypes = dataTree;

  var abCheckbox = document.getElementById("showAbundance"); // checkbox element
  var data = d3.hierarchy(dataTree); //data structure that represente a hieratchy

  if(firstTime){
    //store the most abundant clonotypes and the value of the longest branch of the tree
    treeBranches = findMostAbundantClonotypes(data, selectedNode);
    treeBranches[1]["nodeAbundance"].push(1);
    treeBranches[2]["nodeAbundance"].push(1);  
  }

  //retrieve the name of all the clonotypes selected
  var clonotypesName = selectedNode.map(function(d){ return d.data.name });

  var clonotypeTooltip = d3.select("#chart1").append("div")
                      .attr("class","tooltip");

  //create the svg object and the layout depending on the form of the tree
  //set the dimensions and margins of the diagram
  var margin = {top: 50, right: 50, bottom: 50, left: 60},
      width = (document.getElementById('chart1').offsetWidth) - margin.left - margin.right,
      height = (document.getElementById('chart1').offsetHeight) - margin.top - margin.bottom;

  //add an svg object to the chart1 element
  var svg1 = d3.select("#chart1").append("svg")
          .attr("width", width + margin.left + margin.right)
          .attr("height", height + margin.top + margin.bottom)
        .append("g")
          .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  //declares a tree layout and assigns the size
  var tree = d3.tree()	//creating the tree layout 
          .size([width, height]);
          //.separation(function(a, b) { return ((a.depth >= 2) && (b.depth >= 2)) ? 1 : 5; });

  var duration = 0, i=0;
  data.x0 = height / 2;
  data.y0 = 0;

  var maxAbundance = Math.max.apply(null,treeBranches[2]["nodeAbundance"]);

  if(abCheckbox.checked){
    //determine the size of the node depending on the height and the width of the vg object containing the tree
    var sizeNodeWidth = {"max" : Math.pow((width/(data.leaves().length+1)),2), "min" : Math.pow((width/(data.leaves().length+1))*0.2,2) }
        sizeNodeHeight = {"max" : Math.pow(height/5,2), "min" : Math.pow((height/(50)),2)},
        nodeSize = determineNodeSize(sizeNodeWidth,sizeNodeHeight,maxAbundance); //choose the largest node size among the two previous ones
    //calculate the correspondence of a distance of one nucleotide in the svg's absolute value  
    var yUnit = (height-determineLongestBranch(treeBranches,nodeSize,height,"differentSize"))/treeBranches[0];
    var nodeSizeFactor = (nodeSize["max"]-nodeSize["min"])/maxAbundance;
  }else{
    var nodeSize = {"max" : Math.pow((width/(data.leaves().length+1)),2), "min" : Math.pow((width/(data.leaves().length+1))*0.5,2) }; 
    //value of a nucleotide in pixel
    var yUnit = (height-determineLongestBranch(treeBranches,nodeSize,height,"sameSize"))/treeBranches[0];
    var nodeSizeFactor = 0;  //abundance scale unit
  }

  updateTree(data);

  function updateTree(source){

    //assign properties to the data (coordinates, depth, ...)
    var root = tree(data);

    determineNodeCoord(root, (width/(data.leaves().length)), nodeSizeFactor, yUnit, nodeSize["min"]);

    // Compute the new tree layout.
    var nodes = root.descendants(),
        links = root.descendants().slice(1);

    //NODES

    //add each node as a group
    var node = svg1.selectAll('g.nodeTree').data(nodes, function(d) {return d.id || (d.id = ++i); });

    var nodeEnter = node.enter().append("g")
                 .attr('class', 'nodeTree')
                 .attr("transform", function(d) { return "translate(" + source.x0 + "," + source.y0 + ")"; })	//position the nodes
                 .on("mousemove",function(d){ if(d.data.color!="#FFFFFF"){ return showClonotype(d); } })
                 .on("mouseout",hideClonotype);

    //adds the circle to the node
    nodeEnter.append("path")
             .attr('class', 'nodeTree')
             .style("fill", function(d){ return d.data.color; })
             .style("stroke", "#000000")
             .style("stroke-dasharray", function(d){ return d.data.name.startsWith('ni')? d.data.style : "none" })
             .style("opacity", 0.8 )
             .attr("d", d3.symbol().size(function(d) { return d.data.value? d.data.nodeSize : 0 } )
                                   .type(function(d) { if(d.data.name=="naive"){return d3.symbolTriangle;
                                                       }else{return d3.symbolCircle;} }));
    //add text to the node
    nodeEnter.append("text")
             .attr('font-size', 12) //set the size of the text
             .attr("dy", function(d) { if(d.children){ return (Math.sqrt(d.data["nodeSize"]/3))/6 
                                       }else{return 15+(Math.sqrt(d.data["nodeSize"]/3))} })	//set the emplacement of the text
             .attr("dx", function(d) { if(d.children){ return -7-(Math.sqrt(d.data["nodeSize"]/3)); } })
             .attr("text-anchor", "middle")
             //.text(function(d) { if(d.data.name!="naive" && d.data.color!="#FFFFFF"){return d.data.name;}})
             .clone(true).lower()
             .attr("stroke", "white");

    //display the clone selected
    nodeEnter.filter(function (d, i) { if(clonotypesName.indexOf(d.data.name)!=-1){ return d.data.name; }})
             .style("font-weight", "bold")
             .classed("selected",true)
             .selectAll("path.nodeTree").style("stroke-width", 3);

    var nodeUpdate = nodeEnter.merge(node);

    //transition to the proper position for the node
    nodeUpdate.transition()
              .duration(duration)
              .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });

    nodeUpdate.select('path.nodeTree')
              .attr("d", d3.symbol().size(function(d) { return d.data.value? d.data.nodeSize : 0 })
                                    .type(function(d) { if(d.data.name=="naive"){return d3.symbolTriangle;
                                                        }else{return d3.symbolCircle;}}))
              .attr('cursor', function(d){ if(d.data.color!="#FFFFFF"){return 'pointer';} });

    //remove any exiting nodes
    var nodeExit = node.exit().transition()
                .duration(duration)
                .attr("transform", function(d) { return "translate(" + source.x + "," + source.y + ")"; })
                .remove();

    //reduce the node circles size to 0
    nodeExit.select('path.nodeTree').attr("d", d3.symbol().size(0));


    //LINKS

    //add the links between the nodes
    var link = svg1.selectAll("path.linkTree").data(links, function(d) { return d.id; });
              
    var linkEnter = link.enter().insert('path',"g")	//SVG path allow to draw shape
                 .attr("class", "linkTree")
                 .style("fill", "none")
                 .style("stroke-width", "2")
                 .style("stroke", "#555")
                 .attr("d", function(d){ var s = {x : source.x0, y : source.y0}; return branchShape(source, source);});

    //update link
    var linkUpdate = linkEnter.merge(link);

    //transition back to the parent element position
    linkUpdate.transition()
              .duration(duration)
              .attr("d", function(d){ return branchShape(d, d.parent); });

    //remove any exiting links
    var linkExit = link.exit().transition()
                .duration(duration)
                .attr("d", function(d){ var s = {x : source.x, y : source.y}; return branchShape(s, s);})
                .remove();

    nodes.forEach(function(d){d.x0 = d.x; d.y0 = d.y;});

  }

  firstTime = false;

  //tooltip
  function showClonotype(d) {
    clonotypeTooltip.style("left", ((d3.event.pageX + 10)+"px"))
                    .style("top", ((d3.event.pageY + 15)+"px"))
                    .style('display', 'inline-block')
                    .html("Name : "+d.data.name + "<br> Abundance : "+ Math.round(d.data.value*100) / 100 + "%<br>Length : "+ d.data.length);
  }

  function hideClonotype() {
    clonotypeTooltip.style('display', 'none');
  }

}
