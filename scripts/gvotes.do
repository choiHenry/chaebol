*********************
*   VOTING RIGHTS   *
*********************
**To run it "do gvotesp kcc 2002"


**Takes a matrix for a given year and computes voting rights

local group="`1'"
local year=`2'

set more off
use `group'`year', replace
keep firmid fid
g lastcontrol=0
save varyct, replace


*Finding the consistent distribution for each threshold ct
***********************************************************
local step 1
forvalues ct=0(`step')100 {         //loop over control treshold, ct
    use `group'`year', replace
	g stakelast=0
    local tresh=`ct'/100

    g done=0
    g control=0
    while done[1]==0 & _N>0 {   //loop until all firms have sum>ct

        *sum of stakes
        egen sum=rsum(stake0-stakelast)

        *determine which firms are controlled
        replace control=0
        replace control=1 if sum>=`tresh'

        *generate done variable =1 if done
        drop done
        egen done=min(control)
        drop sum

        if done[1]==0 {
            *drop columns that belong to firms with control==0
            local i 1
            while `i'<=_N {
                if control[`i']==0 {
                    local j=fid[`i']
                    drop stake`j'
                }
                local i=`i'+1
            }
            *drop rows with control==0
            drop if control==0
        }
    }
    keep fid
    sort fid
    save temp, replace
    use varyct, replace
    sort fid
    merge 1:1 fid using temp
    replace lastcontrol=`ct' if _merge==3
    drop _merge
    save, replace
}

drop fid
sort firmid
merge 1:1 firmid using `group'`year'
drop _merge
gen stakelast=0
egen affil = rsum(stake1-stakelast)
keep firmid lastcontrol grpname grpname2 grpcode stake0 affil
save v`group'`year', replace
