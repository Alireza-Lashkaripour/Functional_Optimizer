#!/bin/csh                                                                                             


#foreach a1 (0.30 0.40 0.50 0.60 0.70)
    #foreach b1 (-0.60 -0.50 -0.40 -0.30 -0.20 -0.10 0.00 0.10 0.20 0.30 0.40 0.50 0.60)
foreach a1 (0.60)
    foreach b1 (0.20)
        foreach a2 (0.50)
            foreach b2 (0.00)
                foreach mu (0.33)
                mkdir mu-{$mu}_a1-{$a1}_b1-{$b1}_a2-{$a2}_b2-{$b2}
                cd mu-{$mu}_a1-{$a1}_b1-{$b1}_a2-{$a2}_b2-{$b2}
            
                    foreach mol (Ethene E-Butadiene all-E-Hexatriene all-E-Octatetraene Cyclopropene Cyclopentadiene Norbornadiene Benzene Naphthalene Furan Pyrrole Imidazole Pyridine Pyrazine Pyrimidine Pyridazine s-Triazine s-Tetrazine Formaldehyde Acetone p-Benzoquinone Formamide Acetamide Propanamide Cytosine Thymine Uracil Adenine)

                        set inp="{$mol}_{$mu}_a1-{$a1}_b1-{$b1}_a2-{$a2}_b2-{$b2}_631gs_VEE"
                        set line=`../2_line.sh $inp.log`
                        set check=`../2_check.sh $line $inp.log`
                        if ($check == "err") then
                            echo $inp
                            #sed -i 's/diis=.f. soscf=.t./diis=.t. soscf=.f./g' $inp.inp
                            #gms_sbatch -p trd -c 32 -i $inp.inp
                            #gms_sbatch -p trpro,xeon,chc3,chc4 -c 32 -i $inp.inp


                            #set norb = `../2_norb.sh $inp.log`
                            #echo "" \$guess "guess=moread norb=$norb " \$END >> $inp.inp
                            #sed -i 's/diis=.f. soscf=.t./diis=.t. soscf=.f./g' $inp.inp
                            ##sed -i 's/diis=.t. soscf=.f./diis=.f. soscf=.t./g' $inp.inp
                            #sed -n '/$VEC/,$p' ~/scr/$inp.dat >> $inp.inp
                            #gms_sbatch -p trd -c 32 -i $inp.inp
                            #gms_sbatch -p trpro,xeon,chc3,chc4 -c 32 -i $inp.inp

                        endif
                        
                        
                    end
                cd ../
                end
            end
        end
    end
end
