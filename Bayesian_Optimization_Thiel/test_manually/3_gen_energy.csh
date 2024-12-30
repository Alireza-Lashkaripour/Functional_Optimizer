#!/bin/csh                                                                                             

mkdir 0_results
rm 0_results/*.tbl

#foreach a1 (0.30 0.40 0.50 0.60 0.70)
#    foreach b1 (-0.60 -0.50 -0.40 -0.30 -0.20 -0.10 0.00 0.10 0.20 0.30 0.40 0.50 0.60)
foreach a1 (0.60)
    foreach b1 (0.20)
        foreach a2 (0.50)
            foreach b2 (0.00)
                foreach mu (0.33)
                mkdir mu-{$mu}_a1-{$a1}_b1-{$b1}_a2-{$a2}_b2-{$b2}
                cd mu-{$mu}_a1-{$a1}_b1-{$b1}_a2-{$a2}_b2-{$b2}
            
                    foreach mol (Ethene E-Butadiene all-E-Hexatriene all-E-Octatetraene Cyclopropene Cyclopentadiene Norbornadiene Benzene Naphthalene Furan Pyrrole Imidazole Pyridine Pyrazine Pyrimidine Pyridazine s-Triazine s-Tetrazine Formaldehyde Acetone p-Benzoquinone Formamide Acetamide Propanamide Cytosine Thymine Uracil Adenine)
                        set inp="{$mol}_{$mu}_a1-{$a1}_b1-{$b1}_a2-{$a2}_b2-{$b2}_631gs_VEE"
                        ../3_read.sh $mol $inp.log >> mu-{$mu}_a1-"$a1"_b1-"$b1"_a2-"$a2"_b2-"$b2".tbl

                    end
                mv mu-{$mu}_a1-"$a1"_b1-"$b1"_a2-"$a2"_b2-"$b2".tbl ../0_results/.
                cd ../
                end
            end
        end
    end
end
