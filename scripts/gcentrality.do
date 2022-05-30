*********************
*   CENTRALiTY   *
*********************
**Need to run gmatrix for the group-year first

**Example: to run it "do gvotes kcc 2002"

**Takes a matrix for a given year and computes voting rights
set more off
local group="`1'"
local year=`2'

use v`group'`year', replace
replace last=. if last==0
egen m=sum(last)
egen nactive=sum(last~=.)
g averagecontrolall=(m-last)/(nactive-1)

replace last=0 if last~=. //clean variable lastcontrol before starting process
keep firmid average last
sort firmid
g fid=_n

local nf=_N

keep firmid fid average last
forvalues i=1/`nf' {
    save varyct`i', replace
}

*Finding the consistent distribution for each treshold ct
*********************************************************
forvalues firm=1/`nf' {
local step 1
forvalues ct=0(`step')100 {         //loop over control treshold, ct
    use `group'`year', replace
    g stakelast=0

    *eliminate firm `firm'
    forvalues i=0/`nf' {
        replace stake`i'=0 if _n==`firm'
    }
    replace stake`firm'=0

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
    use varyct`firm', replace
    sort fid
    merge 1:1 fid using temp
    replace lastcontrol=`ct' if _merge==3
    drop _merge
    save, replace
}
replace last=. if average==.
replace last=. if _n==`firm'
egen averagewofirm=mean(last)
save cent`group'`year'firm`firm', replace
}
capture noisily erase cent`group'`year'.dta
forvalues firm=1/`nf' {
    use cent`group'`year'firm`firm', replace
    keep if _n==`firm'
    capture append using cent`group'`year'
    save cent`group'`year', replace
}
sort firmid
g central=averagecontrol-averagewofirm
keep firmid fid central
save, replace
