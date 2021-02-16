import sys
from optparse import OptionParser
import operator
import collections
import pandas
import numpy as np
from Bio.Align.Applications import ClustalwCommandline
from Bio import SeqIO
from Bio.Align.Applications import MuscleCommandline
from Bio import AlignIO
#####################################################################

def read_file (nomFi):
	f=open(nomFi,"r")
	lines=f.readlines()
	f.close()
	return lines
#-------------------------------------------------------------------#

def read_AIRR(nomFi):
	col_list = ['sequence_id','sequence','sequence_aa','rev_comp','productive','complete_vdj','vj_in_frame','stop_codon','locus','v_call','d_call','j_call','c_call','sequence_alignment','sequence_alignment_aa','germline_alignment','germline_alignment_aa','junction','junction_aa','np1','np1_aa','np2','np2_aa','cdr1','cdr1_aa','cdr2','cdr2_aa','cdr3','cdr3_aa','fwr1','fwr1_aa','fwr2','fwr2_aa','fwr3','fwr3_aa','fwr4','fwr4_aa','v_score','v_identity','v_support','v_cigar','d_score','d_identity','d_support','d_cigar','j_score','j_identity','j_support','j_cigar','c_score','c_identity','c_support','c_cigar','v_sequence_start','v_sequence_end','v_germline_start','v_germline_end','v_alignment_start','v_alignment_end','d_sequence_start','d_sequence_end','d_germline_start','d_germline_end','d_alignment_start','d_alignment_end','j_sequence_start','j_sequence_end','j_germline_start','j_germline_end','j_alignment_start','j_alignment_end','cdr1_start','cdr1_end','cdr2_start','cdr2_end','cdr3_start','cdr3_end','fwr1_start','fwr1_end','fwr2_start','fwr2_end','fwr3_start','fwr3_end','fwr4_start','fwr4_end','v_sequence_alignment','v_sequence_alignment_aa','d_sequence_alignment','d_sequence_alignment_aa','j_sequence_alignment','j_sequence_alignment_aa','c_sequence_alignment','c_sequence_alignment_aa','v_germline_alignment','v_germline_alignment_aa','d_germline_alignment','d_germline_alignment_aa','j_germline_alignment','j_germline_alignment_aa','c_germline_alignment','c_germline_alignment_aa','junction_length','junction_aa_length','np1_length','np2_length','n1_length','n2_length','p3v_length','p5d_length','p3d_length','p5j_length','consensus_count','duplicate_count','cell_id','clone_id','rearrangement_id','repertoire_id','rearrangement_set_id','sequence_analysis_category','d_number','5prime_trimmed_n_nb','3prime_trimmed_n_nb','insertions','deletions','junction_decryption']
	df = pandas.read_csv(nomFi, sep='\t',usecols=col_list)
	df["whole_seq"] = df["fwr1"].astype(str) + df["cdr1"].astype(str) +df["fwr2"].astype(str)+ df["cdr2"].astype(str)+df["fwr3"].astype(str)+df["cdr3"].astype(str)+df["fwr4"].astype(str)
	df["germline_seq"] = df["v_germline_alignment"].astype(str) + df["np1"].astype(str) + df["d_germline_alignment"].astype(str) + df["np2"].astype(str) + df["j_germline_alignment"].astype(str)
	df['germline_seq'] = df['germline_seq'].str.replace('.','')
	df = df.replace(np.nan, '', regex=True)
	#print(df.loc[22,"v_identity"])
	#print(df.loc[1,"sequence"],"     ",df.loc[1,"germline_seq"])
	return df

#-------------------------------------------------------------------#

def read_seq_info(lines,airr_df,nb_clonotype):
#the seq of each clonotypes
#the most abundant seq ===> germline 
	clonotype_seq = {}
	list_selected_clonotype = []
	for l in lines:
		seq = l.split("\t")
		clonotype = seq[0].split("_")[1]
		if clonotype in clonotype_seq.keys():
			clonotype_seq[clonotype].append(seq[1])
		else: 
			clonotype_seq[clonotype] = [seq[1]]
	major_clonotype = (sorted(clonotype_seq, key=lambda k: len(clonotype_seq[k]), reverse=True)[0])
	germline = airr_df.loc[airr_df['sequence_id'] == clonotype_seq[major_clonotype][0]]["germline_seq"].values[0]
	if nb_clonotype == 'all':
		list_selected_clonotype = list((sorted(clonotype_seq, key=lambda k: len(clonotype_seq[k]), reverse=True)))
	else :
		list_selected_clonotype = list((sorted(clonotype_seq, key=lambda k: len(clonotype_seq[k]), reverse=True)[0:int(nb_clonotype)]))
	return clonotype_seq,germline,list_selected_clonotype,clonotype_seq[major_clonotype][0]

#-------------------------------------------------------------------#

def compare_clonotype_to_germline(region):
	#print('xregion',region)
	region_compered_to_germ = {}
	region_compered_to_germ['germline'] = region['germline']
	germline_seq = region['germline'][0]
	del region['germline']
	for key in region.keys():
		aligned_seq = ''
		for nt in range(len(germline_seq)):
				if germline_seq[nt] == region[key][0][nt]:
					aligned_seq+='.'
				else :
					aligned_seq+= region[key][0][nt]
		region_compered_to_germ[key] = [aligned_seq,region[key][1]]
	#print(region_compered_to_germ)
	return region_compered_to_germ

#-------------------------------------------------------------------#

def write_clonotype_align(region,repertoire_name,coressp_dico,total_seq_clone,airr_df):
	#print(coressp_dico)
	file_name = repertoire_name+"_aligned_regions.txt"
	filetowrite=open(file_name,"w")
	G = "germline"+"\t"+"_"+"\t" + "_" + "\t" +region['germline'][0][0:region['germline'][1][0]]+"\t"+ region['germline'][0][region['germline'][1][0]:region['germline'][1][1]]+"\t"+ region['germline'][0][region['germline'][1][1]:region['germline'][1][2]]+"\t"+ region['germline'][0][region['germline'][1][2]:region['germline'][1][3]]+"\t"+ region['germline'][0][region['germline'][1][3]:region['germline'][1][4]]+"\t"+ region['germline'][0][region['germline'][1][4]:region['germline'][1][5]]+"\t"+ region['germline'][0][region['germline'][1][5]:-1]+"\n"
	filetowrite.write(G)
	for key in region.keys():
		if key != 'germline':
			V_percent = airr_df.loc[airr_df['sequence_id'] == key]["v_identity"].values[0]
			#print(V_percent)
			clonotype_info = key+"\t"+str(len(coressp_dico[key]))+"("+str("%.3f" %(len(coressp_dico[key])/float(total_seq_clone)))+")"+ "\t"+ str(V_percent) + "\t" +region[key][0][0:region[key][1][0]]+"\t"+ region[key][0][region[key][1][0]:region[key][1][1]]+"\t"+ region[key][0][region[key][1][1]:region[key][1][2]]+"\t"+ region[key][0][region[key][1][2]:region[key][1][3]]+"\t"+ region[key][0][region[key][1][3]:region[key][1][4]]+"\t"+ region[key][0][region[key][1][4]:region[key][1][5]]+"\t"+ region[key][0][region[key][1][5]:-1]+"\n"
			filetowrite.write(clonotype_info)
	filetowrite.close()
	return 0

#-------------------------------------------------------------------#

def write_clonaltree_align(clonotype_seq,list_selected_clonotype,airr_df,repertoire_name,germline):
	coressp_dico = {}
	file_name = repertoire_name+"_selected_seq.fasta"
	#file_name_2 = repertoire_name+"_abundance_corresp.txt"
	filetowrite=open(file_name,"w")
	#filetowrite_2=open(file_name_2,"w")
	G = ">germline"+ "\n" +germline+ "\n"
	filetowrite.write(G)
	for clonotype in list_selected_clonotype:
		seq = ">"+str(clonotype_seq[clonotype][0])+"@"+str(len(clonotype_seq[clonotype])) + "\n" + airr_df.loc[airr_df['sequence_id'] == str(clonotype_seq[clonotype][0])]["whole_seq"].values[0]+ "\n"
		#corresp_info = str(clonotype_seq[clonotype][0])+"\t"+str(len(clonotype_seq[clonotype])) + "\n"
		#filetowrite_2.write(corresp_info)
		coressp_dico[clonotype_seq[clonotype][0]] =[]
		for dup in clonotype_seq[clonotype][1:-1]:
			coressp_dico[clonotype_seq[clonotype][0]].append(dup)
		filetowrite.write(seq)
	filetowrite.close()
	return coressp_dico

#-------------------------------------------------------------------#

def alignment(repertoire_name):
	file_name = repertoire_name+"_selected_seq.fasta"
	#clustalw= "/Users/nikaabdollahi/opt/anaconda3/envs/python3.6/bin/clustalw2"
	#cline = ClustalwCommandline(clustalw, infile=file_name, outfile= "nika.aln")
	muscle_cline = MuscleCommandline(input=file_name,out=file_name.split(".")[0]+".aln")
	muscle_cline()
	align = AlignIO.read(file_name.split(".")[0]+".aln", "fasta")
	#print(align)
	count = SeqIO.write(align, file_name.split(".")[0]+"_uniq.aln.fa", "fasta")
	aligned_seq = [(seq_record.id,seq_record.seq) for seq_record in SeqIO.parse(file_name.split(".")[0]+"_uniq.aln.fa","fasta")]
	return aligned_seq


def readFastaMul(nomFi):
	"""read the fasta file of input sequences"""	
	f=open(nomFi,"r")
	lines=f.readlines()
	f.close()

	seq=""
	nom=""
	lesSeq={}
	for l in lines:
		if l[0] == '>':
			if seq != "":
				lesSeq[nom] = seq
			nom=l[1:-1]
			seq=""
		else:
			seq=seq+l[:-1]
	if seq != "":

		lesSeq[nom.rstrip()] = seq.rstrip()
	return lesSeq




def write_all_aligned(repertoire_name,coressp_dico ):
	file_name = repertoire_name+"_all.aln.fa"
	filetowrite=open(file_name,"w")
	dico_fasta =readFastaMul(repertoire_name+"_selected_seq_uniq.aln.fa")
	for seq in dico_fasta.keys():
		sequence = ">"+str(seq)+ "\n" +dico_fasta[seq]+ "\n"
		filetowrite.write(sequence)
		if seq in coressp_dico.keys():
			for dup in coressp_dico[seq]:
				sequence = ">"+str(dup)+ "\n" +dico_fasta[seq]+ "\n"
				filetowrite.write(sequence)
	filetowrite.close()
	return 0

#-------------------------------------------------------------------#

def write_clonotype_align_seq(airr_df,repertoire_name,aligned_seq,major_clonotype_seq_id):
	#print("aligned_seq",aligned_seq)
	#print(airr_df.loc[airr_df['sequence_id'] == "S18121"])

	region = {}
	for seq in aligned_seq:
		#print (seq[0].split("@")[0])
		if seq[0].split("@")[0] != 'germline':
			a = airr_df.loc[airr_df['sequence_id'] == seq[0].split("@")[0]]
			#print("a",a)
			if a["v_sequence_start"].size != 0 and a["cdr3_start"].size !=0 and a["cdr3_end"].size!=0:
				region[seq[0].split("@")[0]] = []
				#print(a['sequence_id'].values[0],"cdr3",a["cdr1_start"].values[0],"vstart",a["v_sequence_start"].values[0])
				startCDR1 = int(a["cdr1_start"].values[0]) - int(a["v_sequence_start"].values[0])
				endCDR1	= int(a["cdr1_end"].values[0]) - int(a["v_sequence_start"].values[0])
				startCDR2 = int(a["cdr2_start"].values[0]) - int(a["v_sequence_start"].values[0])
				endCDR2 = int(a["cdr2_end"].values[0]) - int(a["v_sequence_start"].values[0])
				startCDR3 = int(a["cdr3_start"].values[0]) - int(a["v_sequence_start"].values[0])
				endCDR3 = int(a["cdr3_end"].values[0]) - int(a["v_sequence_start"].values[0])
				lim = column_from_residue_number(str(seq[1]),[startCDR1,endCDR1,startCDR2,endCDR2,startCDR3,endCDR3])
				#print(str(seq[1]),lim)
				region[seq[0].split("@")[0]] = [str(seq[1]),lim]
		else :
			a = airr_df.loc[airr_df['sequence_id'] == major_clonotype_seq_id]
			region['germline'] = []
			startCDR1 = int(a["cdr1_start"].values[0]) - int(a["v_sequence_start"].values[0])
			#print("aaaa",startCDR1)
			endCDR1	= int(a["cdr1_end"].values[0]) - int(a["v_sequence_start"].values[0])
			startCDR2 = int(a["cdr2_start"].values[0]) - int(a["v_sequence_start"].values[0])
			endCDR2 = int(a["cdr2_end"].values[0]) - int(a["v_sequence_start"].values[0])
			startCDR3 = int(a["cdr3_start"].values[0]) - int(a["v_sequence_start"].values[0])
			endCDR3 = int(a["cdr3_end"].values[0]) - int(a["v_sequence_start"].values[0])
			#print("bbbbb",[startCDR1,endCDR1,startCDR2,endCDR2,startCDR3,endCDR3])
			lim2 = column_from_residue_number(str(seq[1]),[startCDR1,endCDR1,startCDR2,endCDR2,startCDR3,endCDR3])
			#print(lim2)
			region[seq[0]] = [str(seq[1]),lim2]
	#print("rerererere",region)
	return region

#-------------------------------------------------------------------#

def column_from_residue_number(seq,res_no_list):
	#print("seq",seq)
	#print("res_no_list",res_no_list)
	"""
	AAAA AA AAAA ===> [3,6]
	A-AAAA-AAAA---A
	A-AAA/A-A /AAA---A ===>[4, 8]
	i=0, 1, 2, 3, 4
	j=0, 0, 1, 2, 3
	"""
	list_region_seq = []
	pos_without_gap = -1
	gap = 0
	for i in range(len(seq)):
		#print ("i =",i)
		if seq[i] != '-' :
			pos_without_gap +=1
			#print("pos_without_gap =",pos_without_gap)
			if pos_without_gap == res_no_list[0]:
				#print(seq[0:i])
				list_region_seq.append(i)
			elif pos_without_gap ==res_no_list[1]:
				#print(seq[list_region_seq[0]:i])
				list_region_seq.append(i)
			elif pos_without_gap ==res_no_list[2]:
				#print(seq[list_region_seq[0]:i])
				list_region_seq.append(i)
			elif pos_without_gap ==res_no_list[3]:
				#print(seq[list_region_seq[0]:i])
				list_region_seq.append(i)
			elif pos_without_gap ==res_no_list[4]:
				#print(seq[list_region_seq[0]:i])
				list_region_seq.append(i)
			elif pos_without_gap ==res_no_list[5]:
				#print(seq[list_region_seq[0]:i])
				list_region_seq.append(i)
	#print(seq[list_region_seq[1]:len(seq)])
	#print("list_region_seq",list_region_seq)
	return list_region_seq 

#####################################################################
def main():
	usage = "usage: alignment_intraconal.py -a AIRR_IMGT_annotation_output -f final_seq_info -n repertoire_name -s number_of_clonotype_to_analyze"
	parser = OptionParser(usage)
	parser.add_option("-a", "--AIRR_IMGT_annotation_output", dest="IMGT_seq_info",
	      help="read data from AIRR_IMGT_annotation_output")
	parser.add_option("-f", "--final_seq_info",dest="final_seq_info",
	      help="read data from final_seq_info")
	parser.add_option("-n", "--repertoire_name",dest="repertoire_name",
	      help="repertoire_name")
	parser.add_option("-s", "--number_of_clonotype_to_analyze",dest="number_of_clonotype_to_analyze",
	      help="the number of clonotype to analyze, if use all, there will be no selection for the analyzing clonotypes otherwise choose the number of n most abondant clonotype ")
	(options, args) = parser.parse_args()
	if len(sys.argv) != 9:
		parser.error("incorrect number of arguments")
	
	IMGT_seq_info = options.IMGT_seq_info
	final_seq_info = options.final_seq_info
	repertoire = options.repertoire_name
	nb_clonotype =  options.number_of_clonotype_to_analyze
	repertoire_name = repertoire+"_"+str(nb_clonotype)
	airr_df = read_AIRR(IMGT_seq_info)
	lines_clonotype_seq = read_file (final_seq_info)

	clonotype_seq,germline,list_selected_clonotype,major_clonotype_seq_id = read_seq_info(lines_clonotype_seq,airr_df,nb_clonotype)
	coressp_dico = write_clonaltree_align(clonotype_seq,list_selected_clonotype,airr_df,repertoire_name,germline)
	aligned_seq = alignment(repertoire_name)
	write_all_aligned(repertoire_name,coressp_dico)

	#column_from_residue_number("A-AAAA-AAAA---A",[3,6])
	region = write_clonotype_align_seq(airr_df,repertoire_name,aligned_seq,major_clonotype_seq_id)
	region_compered_to_germ=compare_clonotype_to_germline(region)
	total_seq_clone =len(lines_clonotype_seq)
	write_clonotype_align(region_compered_to_germ,repertoire_name,coressp_dico,total_seq_clone,airr_df)
#####################################################################
if __name__ == "__main__":
	main()