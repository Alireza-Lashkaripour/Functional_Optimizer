#!/bin/bash                                                                                              



awk '{
    if($1=="NUMBER" && $3=="CARTESIAN")
        {
        print($8)
        }
    }' "$1"
