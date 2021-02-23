/* *********************************************************** TREE *************************************************************** */

function displayTree(dataTree){
  d3.select("#chart1 svg").remove();

  dataClonotypes = dataTree;

  var abCheckbox = document.getElementById("showAbundance"); // checkbox element
  var data = d3.hierarchy(dataTree); //data structure that represente a hieratchy

  if(firstTime){
    //store the most abundant clonotypes and the value of the longest branch of the tree
    treeBranches = findMostAbundantClonotypes(data, selectedNode);

    distancesRepresentation(selectedNode);
      
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

  // declares a tree layout and assigns the size
  var tree = d3.tree()	//creating the tree layout 
          .size([width, height])
          //.separation(function(a, b) { return ((a.depth >= 2) && (b.depth >= 2)) ? 1 : 5; });

  var duration = 0, i=0;
  data.x0 = height / 2;
  data.y0 = 0;
    
  if(abCheckbox.checked){
    var maxSizeNode = Math.pow((width/(data.leaves().length+1)),2), 
        minSizeNode = Math.pow((width/(data.leaves().length+1))*0.3,2),
        //maxSizeNode = Math.min(maxSizeWidth,maxSizeHeight)
        nodeSizeFactor = (maxSizeNode-minSizeNode)/parseFloat(selectedNode[0].data.value),  //abundance scale unit
        yUnit = (height-Math.sqrt((treeBranches[2]*nodeSizeFactor)+(minSizeNode*(treeBranches[0]+1))))/treeBranches[1];  //value of a nucleotide in pixel
  }else{
    var minSizeNode = Math.pow((width/(data.leaves().length+1))*0.5,2), 
        nodeSizeFactor = 0,  //abundance scale unit
        yUnit = (height-Math.sqrt(treeBranches[0]*minSizeNode))/treeBranches[1];  //value of a nucleotide in pixel
  }

  updateTree(data);

  function updateTree(source){

    //assign properties to the data (coordinates, depth, ...)
    var root = tree(data);

    determineNodeCoord(root, (width/(data.leaves().length)), nodeSizeFactor, yUnit, minSizeNode);

    // Compute the new tree layout.
    var nodes = root.descendants(),
        links = root.descendants().slice(1);

    // ********* Creation of the nodes *********

    //add each node as a group
    var node = svg1.selectAll('g.nodeTree').data(nodes, function(d) {return d.id || (d.id = ++i); });

    var nodeEnter = node.enter().append("g")
                 .attr('class', 'nodeTree')
                 .attr("transform", function(d) { return "translate(" + source.x0 + "," + source.y0 + ")"; })	//position the nodes
                 .on('click', selectClonotype)
                 .on("mousemove",function(d){ if(d.data.name!="ighv"){ return showClonotype(d); } })
                 .on("mouseout",hideClonotype);

    // adds the circle to the node
    nodeEnter.append("path")
             .attr('class', 'nodeTree')
             .style("fill", function(d){ return d.data.color; })
             .style("stroke", function(d){ return d.data.stroke; })
             .style("stroke-dasharray", function(d){ return d.data.style; })
             .attr("d", d3.symbol().size(function(d) { return d.data.value? (nodeSizeFactor*parseFloat(d.data.value))+minSizeNode : 0 } )
                                   .type(function(d) { if(d.data.name=="ighv"){return d3.symbolTriangle;
                                                       }else if(d._children==true){return d3.symbolSquare;
                                                       }else{return d3.symbolCircle;} }));
    //add text to the node
    nodeEnter.append("text")
             .attr('font-size', 12) //set the size of the text
             .attr("dy", function(d) { return 15+(Math.sqrt((nodeSizeFactor*parseFloat(d.data.value))+minSizeNode)/2)})	//set the emplacement of the text
             .attr("dx", 15)
             .attr("text-anchor", "middle")
             .text(function(d) { if(clonotypesName.indexOf(d.data.name)!=-1){return d.data.name;}})
             .clone(true).lower()
             .attr("stroke", "white");

    //display the clone selected
    nodeEnter.filter(function (d, i) { if((clonotypesName.indexOf(d.data.name)!=-1) || (clonotypesDistances.indexOf(d.data.name)!=-1) ){ return d.data.name; }})
             .style("font-weight", "bold")
             .classed("selected",true)
             .selectAll("path.nodeTree").style("stroke-width", 3);

    var nodeUpdate = nodeEnter.merge(node);

    //transition to the proper position for the node
    nodeUpdate.transition()
              .duration(duration)
              .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });

    nodeUpdate.select('path.nodeTree')
              .attr("d", d3.symbol().size(function(d) { return d.data.value? (nodeSizeFactor*parseFloat(d.data.value))+minSizeNode : 0 })
                                    .type(function(d) { if(d.data.name=="ighv"){return d3.symbolTriangle;
                                                        }else if(d.data._children){return d3.symbolSquare;
                                                        }else{return d3.symbolCircle;}}))
              .attr('cursor', function(d){ if(d.data.name!="ighv"){return 'pointer';} });

    //remove any exiting nodes
    var nodeExit = node.exit().transition()
                .duration(duration)
                .attr("transform", function(d) { return "translate(" + source.x + "," + source.y + ")"; })
                .remove();

    //reduce the node circles size to 0
    nodeExit.select('path.nodeTree').attr("d", d3.symbol().size(0));


    // ********* Creation of links *********

    //add the links between the nodes
    var link = svg1.selectAll("path.linkTree").data(links, function(d) { return d.id; });
              
    var linkEnter = link.enter().insert('path',"g")	//SVG path allow to draw shape
                 .attr("class", "linkTree")
                 .style("fill", "none")
                 .style("stroke-width", function(d){if(clonotypesDistances.indexOf(d.data.name)!=-1){ return 4;}else{return 2;}})
                 .style("stroke", function(d){if(clonotypesDistances.indexOf(d.data.name)!=-1){ return "#000";}else{return "#555";}})
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

  //action performes when nodes are selected or deselected
  function selectClonotype(d){
    if (!d3.select(this).classed("selected")) {
      if(selectedNode.length==8){
        alert("Can't show the distance of more than 8 clonotypes")
      }else{
        if(d.data.name!="ighv"){
          selectedNode.push(d); //add the clonotype selected in the array containing all the element selected
          d3.select(this).style("font-weight", "bold").classed("selected",true)	//change the style of the selected clonotype                      
          d3.select(this).selectAll("path.nodeTree").style("stroke-width", 3);
          d3.select(this).append("text")	// add the name of the clonotype
                         .attr('font-size', 12) //set the size of the text
                         .attr("dy", function(d) { return 15+(Math.sqrt((nodeSizeFactor*parseFloat(d.data.value))+minSizeNode)/2)})	//set the emplacement of the text
                         .attr("dx", 15)
                         .attr("text-anchor", "middle")
                         .text(d.data.name)
                         .clone(true).lower()
                         .attr("stroke", "white"); 
        }
      }
    }else{
      clonotypesName = selectedNode.map(function(d){ return d.data.name });
      index = clonotypesName.indexOf(d.data.name);
      d3.select(this).style("font-weight", "normal").classed("selected",false);	//change the style of the deselected clonotype
      d3.select(this).selectAll("path.nodeTree").style("stroke-width", 1);
      d3.select(this).selectAll("text").remove(); // remove the name of the clonotype
      selectedNode.splice(index,1); 	//delete the clonotype from the array with all the selected element
    }
    d3.select("#chart2 svg").remove();
    distancesRepresentation(selectedNode);
  }

  function showClonotype(d) {
    clonotypeTooltip.style("left", ((d3.event.pageX + 10)+"px"))
                    .style("top", ((d3.event.pageY + 15)+"px"))
                    .style('display', 'inline-block')
                    .html("Name : "+d.data.name + "<br> Abundance : "+ Math.round(d.data.value*100*100) / 100 + "%<br>Productivity : "+ d.data.productivity);
  }

  function hideClonotype() {
    clonotypeTooltip.style('display', 'none');
  }

}