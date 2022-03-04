#!/usr/bin/env python3
#-*-coding:Utf-8-*-

#Recover the informations contained for the tree representation (color, name, abundance value, cdr3, ...)
#Four files must be pass in argument : a file containing the sequences of the clonotypes, a nk format file, a csv file containing the distance between the clonotypes and a file containing html colors

import sys
import os
import json
from optparse import OptionParser
from newick import load

#transform the class format of the tree into dictionary format and add the abundance value
def change_format(newick_tree, abundances, silent_node, prev_node):
	tree = {}
	global num_silent_node
	if(newick_tree.name=="germline" or newick_tree.name=="naive"):
		add_germline_info(tree)
		prev_node = newick_tree.name
		
	elif newick_tree.name in abundances.keys():	#add the value of abundance if the name of the clone is find in the dictionary of abundance
		add_clonotype_info(tree, abundances, newick_tree.name, prev_node, silent_node)	
		silent_node = 0
		prev_node = newick_tree.name

	else :
		add_silent_node_info (tree, newick_tree.name)
		silent_node+=1
		num_silent_node = num_silent_node + 1

	color_index = change_index(len(colors),len(stroke_style))	#update the values of the index
	if(newick_tree.descendants!=[]) :	
		tree["children"]=newick_tree.descendants	
		for i in range(len(newick_tree.descendants)): 
			clonotype_info = change_format(newick_tree.descendants[i], abundances, silent_node, prev_node)	#repeat the same actions as its parents (name, value, length)
			tree["children"][i] = clonotype_info	
	return tree	

# ------------------------------------------------------------------------------------
	
def add_clonotype_info (tree, abundances, node_name, prev_node, silent_node) :	
	tree["name"]=node_name
	tree["value"]=(abundances[node_name]*100)/abundances["total"]
	tree["color"]=colors[color_index[0]]
	tree["stroke"]=colors[color_index[1]]
	tree["style"]=colors[color_index[2]]
	del abundances[node_name]
	tree["length"] = branch_length (prev_node, node_name, silent_node) 
	
# ------------------------------------------------------------------------------------

def add_germline_info (tree) :
	tree["name"]="naive"
	tree["value"]=1
	tree["color"]="#808080"
	tree["stroke"]="#808080"
	tree["style"]="none"
	tree["seq"]="germline"

# ------------------------------------------------------------------------------------

def add_silent_node_info (tree, node_name) :
	tree["value"]=1
	tree["name"]="ni"+ str(num_silent_node)
	tree["color"]="#FFFFFF"
	tree["stroke"]="#808080"
	tree["style"]="2,2"
	tree["length"]=1

# ------------------------------------------------------------------------------------

def branch_length (prev_node, current_node, silent_node) :
	if((prev_node, current_node) in branches.keys()):
		length = str(float(branches[(prev_node, current_node)])-silent_node)
		del branches[(prev_node, current_node)]
		return length
	else:
		return "0"

# ------------------------------------------------------------------------------------

def save_json_format(file_name, data):
	output_file = open(file_name+".json", "w")
	json.dump(data, output_file, indent = 4, sort_keys = False)
	output_file.close()

# ------------------------------------------------------------------------------------

def color_list(file):
	global colors
	colors = []
	with open(file) as f:
		for line in f :
			colors.append(line.split("\n")[0])

# ------------------------------------------------------------------------------------

#change the index of the color, stroke and style
def change_index(nb_colors,nb_stroke):

	if(color_index[0]!=nb_colors-1):
		color_index[0] += 1
	elif(color_index[1]!=nb_colors-1):
		color_index[0] = 0
		color_index[1] += 1
	elif(color_index[2]!=nb_stroke-1):
		color_index[0] = 0
		color_index[1] = 0
		color_index[2] += 1
	else:
		color_index[0] = 0
		color_index[1] = 0
		color_index[2] = 0

	return color_index

# ------------------------------------------------------------------------------------

def read_newick_file (file) :
	with open(file) as f :
		return load(f)

# ------------------------------------------------------------------------------------

def get_tree_branches (file) :
	global branches
	branches = {}
	branch_length = ["","",0]
	if (os.path.isfile(file)) :
		with open(file) as f :
			for line in f :
				branch_length = line.split("\n")[0].split(",")
				branches[(branch_length[0],branch_length[1])]=branch_length[2]

# ------------------------------------------------------------------------------------

def get_abundance (file) :
	abundance = {}
	abundance["total"] = 0
	if (os.path.isfile(file)) :
		with open(file) as f:
			for line in f :
				if(line[0] == ">"):
					seq = line.split("\n")[0]
					seq_info = seq.split("@")
					seq_name = seq_info[0][1:]
					if(len(seq_info) == 2) :
						number_seq = int(seq_info[1])
						abundance[seq_name] = number_seq
						abundance["total"] += number_seq
					else :
						if seq_name in abundance :
							abundance[seq_name] += 1
							abundance["total"] += 1
						else :
							abundance[seq_name] = 1
							abundance["total"] += 1
	return abundance


# ------------------------------------------------------------------------------------

def main():
	usage = usage = "python clonotype_informations_json.py -f <fasta_file> -n <newick_file> -l <csv_file> -c <colors> \n"
	parser = OptionParser(usage)
	parser.add_option("-f", "--fasta_file", dest="fasta_file",  help="sequences in fasta format")
	parser.add_option("-n", "--newick_file", dest="newick_file",  help="tree in newick format")
	parser.add_option("-l", "--csv_file", dest="csv_file",  help="csv file containing length between nodes")
	parser.add_option("-c", "--colors", dest="colors",  help="file containing the colors")
	
	(options, args) = parser.parse_args()
	
	if len(sys.argv) != 9:
		parser.error("incorrect number of arguments")
	
	fasta_file = options.fasta_file
	newick_file = options.newick_file
	csv_file = options.csv_file
	colors_file = options.colors

	global stroke_style, color_index, num_silent_node
	stroke_style = ["none", "10,10", "1,5"]
	color_index = [0,0,0]
	num_silent_node = 0
	newick_tree = read_newick_file(newick_file)
	get_tree_branches(csv_file)
	abundances = get_abundance(fasta_file)
	color_list(colors_file)
	
	tree = change_format(newick_tree[0].descendants[0], abundances, 0, "germline")	#change the format of the tree to export it in JSON format
	
	basename = os.path.basename(newick_file)
	file_name = os.path.splitext(basename)[0]

	save_json_format(file_name+"_tree", tree)
	
	print("Done")

# ------------------------------------------------------------------------------------

if __name__ == "__main__" :
	main()
	
