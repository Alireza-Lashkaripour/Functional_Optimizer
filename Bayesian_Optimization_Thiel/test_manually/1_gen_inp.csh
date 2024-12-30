#!/bin/csh                                                                                             




foreach a1 (0.30 0.40 0.50 0.60 0.70)
    foreach b1 (-0.60 -0.50 -0.40 -0.30 -0.20 -0.10 0.00 0.10 0.20 0.30 0.40 0.50 0.60)
        foreach a2 (0.50)
            foreach b2 (0.00)
                foreach mu (0.33)
                mkdir mu-{$mu}_a1-{$a1}_b1-{$b1}_a2-{$a2}_b2-{$b2}
                cd mu-{$mu}_a1-{$a1}_b1-{$b1}_a2-{$a2}_b2-{$b2}
                    foreach mol (Ethene E-Butadiene all-E-Hexatriene all-E-Octatetraene Cyclopropene Cyclopentadiene Norbornadiene Benzene Naphthalene Furan Pyrrole Imidazole Pyridine Pyrazine Pyrimidine Pyridazine s-Triazine s-Tetrazine Formaldehyde Acetone p-Benzoquinone Formamide Acetamide Propanamide Cytosine Thymine Uracil Adenine)

                        set inp="{$mol}_{$mu}_a1-{$a1}_b1-{$b1}_a2-{$a2}_b2-{$b2}_631gs_VEE"

                        echo "" \$CONTRL " SCFTYP=ROHF RUNTYP=energy DFTTYP=camb3lyp ICHARG=0" > $inp.inp 
                        echo " TDDFT=MRSF MAXIT=200 MULT=3 ISPHER=0 " \$END >> $inp.inp 
                        echo "" \$TDDFT " NSTATE=50 IROOT=1 MULT=1 tammd=.t.  "  >> $inp.inp 
                        echo " spcp(1)=0.5,0.5,0.5 mralp=$a2 mrbet=$b2 " \$END >> $inp.inp
                        #echo "" \$TDDFT " NSTATE=4 IROOT=1 MULT=1 mrscal=0.5 spcp(1)=0.5,0.5,0.5 " \$END >> $inp.inp 
                        echo "" \$SCF " DIRSCF=.t. diis=.f. soscf=.t. damp=.t. shift=.t. "  >> $inp.inp
                        echo " couple=.t. alpha(1)=0.5,0.5,0.5 beta(1)=0.5,0.5,0.5 " \$END >> $inp.inp
                        echo "" \$DFT "mu=$mu alphac=$a1 betac=$b1 " \$END >> $inp.inp
                        echo "" \$BASIS " GBASIS=N31 NGAUSS=6 NDFUNC=1 " \$END >> $inp.inp 
                        echo "" \$SYSTEM " TIMLIM=999999100 MWORDS=500 kdiag=1 " \$END >> $inp.inp 
                        echo "" \$DATA >> $inp.inp 
                        echo " $mol " >> $inp.inp 
                        ../1_gen_geo.sh $mol ../../../Thiels_set.txt >> $inp.inp
                        echo " "\$END >> $inp.inp
                        
                        #gms_sbatch -p trpro,xeon,chc3,chc4 -c 12 -i $inp.inp
                        gms_sbatch -p def,ryzn,r630 -i $inp.inp
                    end
                cd ../
                end
            end
        end
    end
end
