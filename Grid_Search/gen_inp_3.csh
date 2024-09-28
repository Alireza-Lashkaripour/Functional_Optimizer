#!/bin/csh

# Define the ranges for a2 and b2
set a2_values = `seq 0.5 0.01 0.8`
set b2_values = `seq -0.1 0.01 0.1`

# Define the fixed values for a1 and b1
set a1_fixed = "0.5"
set b1_fixed = "-0.2"

# Loop over a2 values
foreach a2 ($a2_values)
    # Loop over b2 values
    foreach b2 ($b2_values)
        # Construct the directory name using the current a2 and b2 values
        set name = "a1_${a1_fixed}_b1_${b1_fixed}_a2_${a2}_b2_${b2}_S"
        mkdir -p ${name}
        cd ${name}

        # Loop over your molecules
        foreach iii (Heptazine Cyclazine Molecule3 Molecule4 Molecule5 Molecule6 Molecule7 Molecule8 Molecule9 Molecule10)
            set inp="${iii}_${name}"

            # Create the input file with the current parameters
            echo "" \$CONTRL " SCFTYP=ROHF RUNTYP=energy DFTTYP=camb3lyp ICHARG=0" > $inp.inp
            echo " TDDFT=MRSF MAXIT=200 MULT=3 ISPHER=0 UNITS=BOHR " \$END >> $inp.inp
            echo "" \$TDDFT " NSTATE=3 IROOT=1 MULT=1 mralp=$a2 mrbet=$b2 "  \$END >> $inp.inp
            echo "" \$DFT " alphac=$a1_fixed betac=$b1_fixed " \$END >> $inp.inp
            echo "" \$SCF " DIRSCF=.t. diis=.f. damp=.t. "  >> $inp.inp
            echo " soscf=.f. shift=.t. FDIFF=.t. " \$END >> $inp.inp
            echo "" \$BASIS " GBASIS=N31 NGAUSS=6 NDFUNC=1 " \$END >> $inp.inp
            echo "" \$SYSTEM " TIMLIM=999999100 MWORDS=500 kdiag=1 " \$END >> $inp.inp
            echo "" \$DATA >> $inp.inp
            echo " $iii " >> $inp.inp
            echo " C1" >> $inp.inp
            ../gen_geo.sh $iii ../../GW_binding_energy_geom.txt >> $inp.inp
            echo " "\$END >> $inp.inp

            # Submit the job
            gms_sbatch -p r630 -i $inp.inp
        end

        # Return to the parent directory
        cd ..
    end
end
