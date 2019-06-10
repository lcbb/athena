PDBGen v1.5 Documentation

Written by William P. Bricker
  at Massachusetts Institute of Technology
  last updated May 14, 2019
  
Main function: pdbgen

  Inputs: filename --> name of structure file (omit .cndo)
          abtype --> type of DNA/RNA helical structure ('A' or 'B')
		      note: 'A'-type structure not supported yet
		  natype --> type of nucleic acid ('DNA' or 'RNA')
		      note: 'RNA' structure not supported yet
		  inputdir --> directory that includes input .cndo file (see filename
		               above)
		  outputdir --> directory for PDBGen output files
		  
  Outputs: logfile --> writes to outputdir + filename + '-pdbgen.log'
           standard PDB file --> writes to outputdir + filename + '.pdb'
		   multimodel PDB file --> writes to outputdir + filename + '-multimodel.pdb'
		   segment PDB file --> writes to outputdir + filename + '-chseg.pdb'
		   
Reference average B-DNA Structure is loaded from the class BDNA(), and is based
on the 3DNA parameter set.