#!/bin/bash                                                                                              



awk -v num="$1" '{
    
    if($4=="TERMINATED" && $5=="NORMALLY")
        {
        exit;
        }

    if($4=="TERMINATED" && $5=="-ABNORMALLY-")
        {
        print("err")
        exit;
        }


    if($5=="quit" && $6=="unexpectedly.")
        {
        print("err")
        exit;
        }

    if(NR == num)
        {
        print("err")
        exit;
        }

    }' "$2"
