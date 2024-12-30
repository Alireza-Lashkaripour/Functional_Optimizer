#!/bin/bash                                                                                              



awk -v name="$1" '{
    if($1=="SCF" && $2=="DID")
        {
        print(name" has problem")
        }

    if(name == "Ethene")
        {
        if($1 == "1" && $2 == "AG")
            {
            bu=0
            AG[1] = $3
            }

        if($1 != "0" && $2== "B1U")
            {
            bu += 1
            B1U[bu] = $3 
            }

        if($4 == "TERMINATED" && $5 == "NORMALLY")
            {
            print(name, (B1U[1] - AG[1])*27.2114 )
            }
        }


    if(name == "E-Butadiene" || name =="all-E-Hexatriene" || name == "all-E-Octatetraene")
        {
        if($1 == "1" && $2 == "AG")
            {
            bu=0
            ag=1
            AG[ag] = $3
            }

        if($1 != "0" && $2== "BU")
            {
            bu += 1
            BU[bu] = $3 
            }

        if($1 != "1" && $2== "AG")
            {
            ag += 1
            AG[ag] = $3 
            }

        if($4 == "TERMINATED" && $5 == "NORMALLY")
            {
            print(name, (BU[1] - AG[1])*27.2114 )
            print(name, (AG[2] - AG[1])*27.2114 )
            }
        }


    if(name == "Cyclopropene")
        {
        if($1 == "1" && $2 == "A1")
            {
            ao = 1
            bo = 0
            bt = 0
            A1[ao] = $3
            }

        if($1 != "0" && $2== "B1")
            {
            bo += 1
            B1[bo] = $3 
            }

        if($1 != "0" && $2== "B2")
            {
            bt += 1
            B2[bt] = $3 
            }

        if($4 == "TERMINATED" && $5 == "NORMALLY")
            {
            print(name, (B1[1] - A1[1])*27.2114 )
            print(name, (B2[1] - A1[1])*27.2114 )
            }
        }


    if(name == "Cyclopentadiene")
        {
        if($1 == "1" && $2 == "A1")
            {
            ao = 1
            bo = 0
            bt = 0
            A1[ao] = $3
            }

        if($1 != "0" && $1 != "1" && $2== "A1")
            {
            ao += 1
            A1[ao] = $3 
            }

        if($1 != "0" && $2== "B2")
            {
            bt += 1
            B2[bt] = $3 
            }

        if($4 == "TERMINATED" && $5 == "NORMALLY")
            {
            print(name, (B2[1] - A1[1])*27.2114 )
            print(name, (A1[2] - A1[1])*27.2114 )
            #print( (A1[3] - A1[1])*27.2114 )
            }

        }



    if(name == "Norbornadiene")
        {
        if($1 == "1" && $2 == "A1")
            {
            ao = 1
            at = 0
            bo = 0
            bt = 0
            A1[ao] = $3
            }

        if($1 != "0" && $1 != "1" && $2== "A2")
            {
            at += 1
            A2[at] = $3 
            }

        if($1 != "0" && $2== "B2")
            {
            bt += 1
            B2[bt] = $3 
            }

        if($4 == "TERMINATED" && $5 == "NORMALLY")
            {
            print(name, (A2[1] - A1[1])*27.2114 )
            print(name, (B2[1] - A1[1])*27.2114 )
            }
        }



    if(name == "Naphthalene")
        {
        if($1 == "1" && $2 == "AG")
            {
            ag = 1
            b3u = 0
            b2u = 0
            b1g = 0
            AG[ag] = $3
            }

        if($1 != "0" && $2== "B3U")
            {
            b3u += 1
            B3U[b3u] = $3 
            }

        if($1 != "0" && $2== "B2U")
            {
            b2u += 1
            B2U[b2u] = $3 
            }

        if($1 != "0" && $1 != "1" && $2== "AG")
            {
            ag += 1
            AG[ag] = $3 
            }

        if($1 != "0" && $2== "B1G")
            {
            b1g += 1
            B1G[b1g] = $3 
            }

        if($4 == "TERMINATED" && $5 == "NORMALLY")
            {
            print(name, (B3U[1] - AG[1])*27.2114 )
            print(name, (B2U[1] - AG[1])*27.2114 )
            print(name, (AG[2] - AG[1])*27.2114 )
            print(name, (B1G[1] - AG[1])*27.2114 )
            print(name, (B3U[2] - AG[1])*27.2114 )
            print(name, (B1G[2] - AG[1])*27.2114 )
            print(name, (B2U[2] - AG[1])*27.2114 )
            print(name, (AG[3] - AG[1])*27.2114 )
            }
        }



    if(name == "Furan")
        {
        if($1 == "1" && $2 == "A1")
            {
            ao = 1
            at = 0
            bo = 0
            bt = 0
            A1[ao] = $3
            }

        if($1 != "0" && $1 != "1" && $2== "A1")
            {
            ao += 1
            A1[ao] = $3 
            }

        if($1 != "0" && $2== "B2")
            {
            bt += 1
            B2[bt] = $3 
            }

        if($4 == "TERMINATED" && $5 == "NORMALLY")
            {
            print(name, (B2[1] - A1[1])*27.2114 )
            print(name, (A1[2] - A1[1])*27.2114 )
            print(name, (A1[3] - A1[1])*27.2114 )
            }
        }

    if(name == "Pyrrole")
        {
        if($1 == "1" && $2 == "A1")
            {
            ao = 1
            at = 0
            bo = 0
            bt = 0
            A1[ao] = $3
            }

        if($1 != "0" && $1 != "1" && $2== "A1")
            {
            ao += 1
            A1[ao] = $3 
            }

        if($1 != "0" && $2== "B2")
            {
            bt += 1
            B2[bt] = $3 
            }

        if($4 == "TERMINATED" && $5 == "NORMALLY")
            {
            print(name, (A1[2] - A1[1])*27.2114 )
            print(name, (B2[1] - A1[1])*27.2114 )
            print(name, (A1[3] - A1[1])*27.2114 )
            }
        }

    if(name == "Imidazole")
        {
        if($1 == "1" && length($2) == 2 && length($3) == 15 && length($5) == 6)
            {
            ap = 1
            app = 0
            AP[ap] = $3
            }

        if($1 != "1" && $1 != "0" && length($2) == 2 && length($3) == 15 && length($5) == 6)
            {
            ap += 1
            AP[ap] = $3
            }

        if($1 != "1" && $1 != "0" && length($2) == 3 && length($3) == 15 && length($5) == 6)
            {
            app += 1
            APP[app] = $3
            }

        if($4 == "TERMINATED" && $5 == "NORMALLY")
            {
            print(name, (APP[1] - AP[1])*27.2114 )
            print(name, (AP[2] - AP[1])*27.2114 )
            print(name, (AP[3] - AP[1])*27.2114 )
            }
        }

    if(name == "Pyridine")
        {
        if($1 == "1" && $2 == "A1")
            {
            ao = 1
            at = 0
            bo = 0
            bt = 0
            A1[ao] = $3
            }

        if($1 != "0" && $1 != "1" && $2== "A1")
            {
            ao += 1
            A1[ao] = $3 
            }

        if($1 != "0" && $1 != "1" && $2== "A2")
            {
            at += 1
            A2[at] = $3 
            }

        if($1 != "0" && $1 != "1" && $2== "B1")
            {
            bo += 1
            B1[bo] = $3 
            }

        if($1 != "0" && $1 != "1" && $2== "B2")
            {
            bt += 1
            B2[bt] = $3 
            }

        if($4 == "TERMINATED" && $5 == "NORMALLY")
            {
            print(name, (B2[1] - A1[1])*27.2114 )
            print(name, (B1[1] - A1[1])*27.2114 )
            print(name, (B2[2] - A1[1])*27.2114 )
            }
        }

    if(name == "Pyrazine")
        {
        if($1 == "1" && $2 == "AG")
            {
            ag = 1
            b3u = 0
            au = 0
            b2g = 0
            b2u = 0
            b1u = 0
            b1g = 0
            AG[ag] = $3
            }

        if($1 != "0" && $2== "B3U")
            {
            b3u += 1
            B3U[b3u] = $3 
            }

        if($1 != "0" && $2== "AU")
            {
            au += 1
            AU[au] = $3 
            }

        if($1 != "0" && $2== "B2G")
            {
            b2g += 1
            B2G[b2g] = $3 
            }

        if($1 != "0" && $2== "B2U")
            {
            b2u += 1
            B2U[b2u] = $3 
            }

        if($1 != "0" && $2== "B1U")
            {
            b1u += 1
            B1U[b1u] = $3 
            }

        if($1 != "0" && $2== "B1G")
            {
            b1g += 1
            B1G[b1g] = $3 
            }

        if($1 != "0" && $1 != "1" && $2== "AG")
            {
            ag += 1
            AG[ag] = $3 
            }

        if($4 == "TERMINATED" && $5 == "NORMALLY")
            {
            print(name, (B3U[1] - AG[1])*27.2114 )
            print(name, (AU[1] - AG[1])*27.2114 )
            print(name, (B2U[1] - AG[1])*27.2114 )
            print(name, (B2G[1] - AG[1])*27.2114 )
            print(name, (B1G[1] - AG[1])*27.2114 )
            print(name, (B1U[1] - AG[1])*27.2114 )
            print(name, (B1U[2] - AG[1])*27.2114 )
            print(name, (B2U[2] - AG[1])*27.2114 )
            }
        }

    if(name == "Pyrimidine")
        {
        if($1 == "1" && $2 == "A1")
            {
            ao = 1
            at = 0
            bo = 0
            bt = 0
            A1[ao] = $3
            }

        if($1 != "0" && $1 != "1" && $2== "A1")
            {
            ao += 1
            A1[ao] = $3 
            }

        if($1 != "0" && $1 != "1" && $2== "A2")
            {
            at += 1
            A2[at] = $3 
            }

        if($1 != "0" && $1 != "1" && $2== "B1")
            {
            bo += 1
            B1[bo] = $3 
            }

        if($1 != "0" && $1 != "1" && $2== "B2")
            {
            bt += 1
            B2[bt] = $3 
            }

        if($4 == "TERMINATED" && $5 == "NORMALLY")
            {
            print(name, (B1[1] - A1[1])*27.2114 )
            print(name, (A2[1] - A1[1])*27.2114 )
            print(name, (B2[1] - A1[1])*27.2114 )
            print(name, (A1[2] - A1[1])*27.2114 )
            }
        }

    if(name == "Pyridazine")
        {
        if($1 == "1" && $2 == "A1")
            {
            ao = 1
            at = 0
            bo = 0
            bt = 0
            A1[ao] = $3
            }

        if($1 != "0" && $1 != "1" && $2== "A1")
            {
            ao += 1
            A1[ao] = $3 
            }

        if($1 != "0" && $1 != "1" && $2== "A2")
            {
            at += 1
            A2[at] = $3 
            }

        if($1 != "0" && $1 != "1" && $2== "B1")
            {
            bo += 1
            B1[bo] = $3 
            }

        if($1 != "0" && $1 != "1" && $2== "B2")
            {
            bt += 1
            B2[bt] = $3 
            }

        if($4 == "TERMINATED" && $5 == "NORMALLY")
            {
            print(name, (B1[1] - A1[1])*27.2114 )
            print(name, (A2[1] - A1[1])*27.2114 )
            print(name, (A1[2] - A1[1])*27.2114 )
            print(name, (A2[2] - A1[1])*27.2114 )
            }
        }

    if(name == "s-Triazine")
        {
        }

    if(name == "s-Tetrazine")
        {
        if($1 == "1" && $2 == "AG")
            {
            ag = 1
            b3u = 0
            au = 0
            b1g = 0
            b2u = 0
            b2g = 0
            b3g = 0
            AG[ag] = $3
            }

        if($1 != "0" && $2== "B3U")
            {
            b3u += 1
            B3U[b3u] = $3 
            }

        if($1 != "0" && $2== "AU")
            {
            au += 1
            AU[au] = $3 
            }

        if($1 != "0" && $2== "B1G")
            {
            b1g += 1
            B1G[b1g] = $3 
            }

        if($1 != "0" && $2== "B2U")
            {
            b2u += 1
            B2U[b2u] = $3 
            }

        if($1 != "0" && $2== "B2G")
            {
            b2g += 1
            B2G[b2g] = $3 
            }

        if($1 != "0" && $2== "B3G")
            {
            b3g += 1
            B3G[b3g] = $3 
            }

        if($1 != "0" && $1 != "1" && $2== "AG")
            {
            ag += 1
            AG[ag] = $3 
            }

        if($4 == "TERMINATED" && $5 == "NORMALLY")
            {
            print(name, (B3U[1] - AG[1])*27.2114 )
            print(name, (AU[1] - AG[1])*27.2114 )
            print(name, (B1G[1] - AG[1])*27.2114 )
            print(name, (B2U[1] - AG[1])*27.2114 )
            print(name, (B2G[1] - AG[1])*27.2114 )
            print(name, (AU[2] - AG[1])*27.2114 )
            print(name, (B3G[2] - AG[1])*27.2114 )
            }

        }

    if(name == "Formaldehyde")
        {
        if($1 == "1" && $2 == "A1")
            {
            ao = 1
            at = 0
            bo = 0
            bt = 0
            A1[ao] = $3
            }

        if($1 != "0" && $1 != "1" && $2== "A1")
            {
            ao += 1
            A1[ao] = $3 
            }

        if($1 != "0" && $1 != "1" && $2== "A2")
            {
            at += 1
            A2[at] = $3 
            }

        if($1 != "0" && $1 != "1" && $2== "B1")
            {
            bo += 1
            B1[bo] = $3 
            }

        if($1 != "0" && $1 != "1" && $2== "B2")
            {
            bt += 1
            B2[bt] = $3 
            }

        if($4 == "TERMINATED" && $5 == "NORMALLY")
            {
            print(name, (A2[1] - A1[1])*27.2114 )
            print(name, (B1[1] - A1[1])*27.2114 )
            print(name, (A1[2] - A1[1])*27.2114 )
            }
        }

    if(name == "Acetone")
        {
        if($1 == "1" && $2 == "A1")
            {
            ao = 1
            at = 0
            bo = 0
            bt = 0
            A1[ao] = $3
            }

        if($1 != "0" && $1 != "1" && $2== "A1")
            {
            ao += 1
            A1[ao] = $3 
            }

        if($1 != "0" && $1 != "1" && $2== "A2")
            {
            at += 1
            A2[at] = $3 
            }

        if($1 != "0" && $1 != "1" && $2== "B1")
            {
            bo += 1
            B1[bo] = $3 
            }

        if($1 != "0" && $1 != "1" && $2== "B2")
            {
            bt += 1
            B2[bt] = $3 
            }

        if($4 == "TERMINATED" && $5 == "NORMALLY")
            {
            print(name, (A2[1] - A1[1])*27.2114 )
            print(name, (B1[1] - A1[1])*27.2114 )
            print(name, (A1[2] - A1[1])*27.2114 )
            }
        }

    if(name == "p-Benzoquinone")
        {
        if($1 == "1" && $2 == "AG")
            {
            ag = 1
            au = 0
            b1g = 0
            b3g = 0
            b1u = 0
            b3u = 0
            AG[ag] = $3
            }

        if($1 != "0" && $2== "AU")
            {
            au += 1
            AU[au] = $3 
            }

        if($1 != "0" && $2== "B1G")
            {
            b1g += 1
            B1G[b1g] = $3 
            }

        if($1 != "0" && $2== "B3G")
            {
            b3g += 1
            B3G[b3g] = $3 
            }

        if($1 != "0" && $2== "B1U")
            {
            b1u += 1
            B1U[b1u] = $3 
            }

        if($1 != "0" && $2== "B3U")
            {
            b3u += 1
            B3U[b3u] = $3 
            }


        if($1 != "0" && $1 != "1" && $2== "AG")
            {
            ag += 1
            AG[ag] = $3 
            }

        if($4 == "TERMINATED" && $5 == "NORMALLY")
            {
            print(name, (AU[1] - AG[1])*27.2114 )
            print(name, (B1G[1] - AG[1])*27.2114 )
            print(name, (B3G[1] - AG[1])*27.2114 )
            print(name, (B1U[1] - AG[1])*27.2114 )
            print(name, (B3U[1] - AG[1])*27.2114 )
            }
        }

    if(name == "Formamide")
        {
        if($1 == "1" && length($2) == 2 && length($3) == 15 && length($5) == 6)
            {
            ap = 1
            app = 0
            AP[ap] = $3
            }

        if($1 != "1" && $1 != "0" && length($2) == 2 && length($3) == 15 && length($5) == 6)
            {
            ap += 1
            AP[ap] = $3
            }

        if($1 != "1" && $1 != "0" && length($2) == 3 && length($3) == 15 && length($5) == 6)
            {
            app += 1
            APP[app] = $3
            }

        if($4 == "TERMINATED" && $5 == "NORMALLY")
            {
            print(name, (APP[1] - AP[1])*27.2114 )
            print(name, (AP[2] - AP[1])*27.2114 )
            }
        }

    if(name == "Acetamide")
        {
        if($1 == "1" && length($2) == 2 && length($3) == 15 && length($5) == 6)
            {
            ap = 1
            app = 0
            AP[ap] = $3
            }

        if($1 != "1" && $1 != "0" && length($2) == 2 && length($3) == 15 && length($5) == 6)
            {
            ap += 1
            AP[ap] = $3
            }

        if($1 != "1" && $1 != "0" && length($2) == 3 && length($3) == 15 && length($5) == 6)
            {
            app += 1
            APP[app] = $3
            }

        if($4 == "TERMINATED" && $5 == "NORMALLY")
            {
            print(name, (APP[1] - AP[1])*27.2114 )
            print(name, (AP[2] - AP[1])*27.2114 )
            }
        }

    if(name == "Propanamide")
        {
        if($1 == "1" && length($2) == 2 && length($3) == 15 && length($5) == 6)
            {
            ap = 1
            app = 0
            AP[ap] = $3
            }

        if($1 != "1" && $1 != "0" && length($2) == 2 && length($3) == 15 && length($5) == 6)
            {
            ap += 1
            AP[ap] = $3
            }

        if($1 != "1" && $1 != "0" && length($2) == 3 && length($3) == 15 && length($5) == 6)
            {
            app += 1
            APP[app] = $3
            }

        if($4 == "TERMINATED" && $5 == "NORMALLY")
            {
            print(name, (APP[1] - AP[1])*27.2114 )
            print(name, (AP[2] - AP[1])*27.2114 )
            }
        }

    if(name == "Cytosine")
        {
        if($1 == "1" && length($2) == 2 && length($3) == 15 && length($5) == 6)
            {
            ap = 1
            app = 0
            AP[ap] = $3
            }

        if($1 != "1" && $1 != "0" && length($2) == 2 && length($3) == 15 && length($5) == 6)
            {
            ap += 1
            AP[ap] = $3
            }

        if($1 != "1" && $1 != "0" && length($2) == 3 && length($3) == 15 && length($5) == 6)
            {
            app += 1
            APP[app] = $3
            }

        if($4 == "TERMINATED" && $5 == "NORMALLY")
            {
            print(name, (AP[2] - AP[1])*27.2114 )
            print(name, (APP[1] - AP[1])*27.2114 )
            print(name, (APP[2] - AP[1])*27.2114 )
            print(name, (AP[3] - AP[1])*27.2114 )
            }
        }

    if(name == "Thymine")
        {
        if($1 == "1" && length($2) == 2 && length($3) == 15 && length($5) == 6)
            {
            ap = 1
            app = 0
            AP[ap] = $3
            }

        if($1 != "1" && $1 != "0" && length($2) == 2 && length($3) == 15 && length($5) == 6)
            {
            ap += 1
            AP[ap] = $3
            }

        if($1 != "1" && $1 != "0" && length($2) == 3 && length($3) == 15 && length($5) == 6)
            {
            app += 1
            APP[app] = $3
            }

        if($4 == "TERMINATED" && $5 == "NORMALLY")
            {
            print(name, (APP[1] - AP[1])*27.2114 )
            print(name, (AP[2] - AP[1])*27.2114 )
            print(name, (AP[3] - AP[1])*27.2114 )
            print(name, (APP[2] - AP[1])*27.2114 )
            print(name, (AP[4] - AP[1])*27.2114 )
            }
        }

    if(name == "Uracil")
        {
        if($1 == "1" && length($2) == 2 && length($3) == 15 && length($5) == 6)
            {
            ap = 1
            app = 0
            AP[ap] = $3
            }

        if($1 != "1" && $1 != "0" && length($2) == 2 && length($3) == 15 && length($5) == 6)
            {
            ap += 1
            AP[ap] = $3
            }

        if($1 != "1" && $1 != "0" && length($2) == 3 && length($3) == 15 && length($5) == 6)
            {
            app += 1
            APP[app] = $3
            }

        if($4 == "TERMINATED" && $5 == "NORMALLY")
            {
            print(name, (APP[1] - AP[1])*27.2114 )
            print(name, (AP[2] - AP[1])*27.2114 )
            print(name, (AP[3] - AP[1])*27.2114 )
            print(name, (APP[2] - AP[1])*27.2114 )
            print(name, (APP[3] - AP[1])*27.2114 )
            print(name, (AP[4] - AP[1])*27.2114 )
            }
        }

    if(name == "Adenine")
        {
        if($1 == "1" && length($2) == 2 && length($3) == 15 && length($5) == 6)
            {
            ap = 1
            app = 0
            AP[ap] = $3
            }

        if($1 != "1" && $1 != "0" && length($2) == 2 && length($3) == 15 && length($5) == 6)
            {
            ap += 1
            AP[ap] = $3
            }

        if($1 != "1" && $1 != "0" && length($2) == 3 && length($3) == 15 && length($5) == 6)
            {
            app += 1
            APP[app] = $3
            }

        if($4 == "TERMINATED" && $5 == "NORMALLY")
            {
            print(name, (AP[2] - AP[1])*27.2114 )
            print(name, (AP[3] - AP[1])*27.2114 )
            print(name, (APP[1] - AP[1])*27.2114 )
            print(name, (APP[2] - AP[1])*27.2114 )
            }
        }


    }' "$2"
