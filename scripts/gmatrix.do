
**Example: to run it "do gmatrix kcc 2002"
** This program creates the ownership matrix that is an input to the other programs
** WARNING: this program is provided for illustration purposes only as the data each researcher has will
** come in different

** Assumes input is of the form
** Data contains: year groupid firmid ownerid own type

**type: 0=family member, 1=other firm, 99=rows that should not be considered (i.e., people unrelated to family)

clear
set more off
local group="`1'"
local year=`2'

*Create file with temporary ids and correspondence
use `group'`year'raw, replace
keep firmid
sort firmid
by firmid: keep if _n==1
g id=_n
local nf=_N         //keep number of firms
g double ownerid=firmid
save `group'id, replace

**** Attach temporary ids (for firmid and ownerid)
use `group'id, replace
sort firmid
save, replace

use `group'`year'raw, replace
sort firmid
merge firmid using `group'id, keep(id) uniqusing        //firms that are not present this year will have a column with missing
rename id fid
drop _merge
save temp, replace

use `group'id
sort ownerid
save, replace

use temp
sort ownerid
merge ownerid using `group'id, nokeep keep(id) uniqusing
rename id oid
drop _merge



**Create ownership matrix

keep if type~=0|type~=1

*place family stake in variable s0
egen stake0=max(own*(type==0)), by(firmid)

*generate variables stake`i'
*Create an 'nf' X `'nf' matrix of zeroes
matrix A = I(`nf')-I(`nf')

*create the ownership matrix
sort fid
local nn=_N
forval n=1/`nn' {                   //n is current observation
    local i=fid[`n']                //i contains the firms that is owned
    local j=oid[`n']                //j contains the owner
    if `i'>=1 & `i'<=`nf' & `j'>=1 & `j'<=`nf' {
        matrix A[`i',`j']=own[`n']
    }
}
by fid: keep if _n==1
svmat A, names(stake)

drop ownerid own oid type

save `group'`year', replace
