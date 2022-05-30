**Takes a matrix for a given year and computes ultimate cash flow rights and average position

**Example: to run it "do gcflowsap example 2002"

set more off
local group="`1'"
local year=`2'

use `group'`year', replace

*Create matrices for formulas
local nf=_N                 //number of firms in the group
matrix I = I(`nf')          //nf X nf identity matrix
mkmat stake1-stake`nf', matrix (temp)
matrix A = temp'            //This is matrix A in the paper. Matrix of intercompany holdings
mkmat stake0, matrix (f)    //This is vector f in the paper. Vector of direct family holdings
matrix D=inv(I - A)        //useful intermediate matrix. It shows up in formulas for cash flow rights and position
drop stake0-stake`nf'       //drop ownership matrix from dataset. It is now in the matrices


****************************************
** Cash flow rights and average position
****************************************

*Cash flow rights
matrix ultown = (f'*D)'     //Formula in the paper
matrix colnames ultown = ultown //change the column name of the ultown matrix to ultown

*Average position
matrix inter = (f'*D*D)'    //Almost there. Only need to divided by ultown
matrix colnames inter = inter //change the column name of the inter matrix to inter

*Place information in dataset
svmat ultown
svmat inter
g avpos=inter/ultown        //we divide by ultown to get average position (see formula)
keep ultown1 firmid avpos
rename ultown1 ultown

*******************************
** Shortest distance and loops
*******************************

*round number in matrix A and in matrix f
forvalues i=1/`nf' {
    forvalues j=1/`nf' {
        matrix A[`i',`j']=round(A[`i',`j']*10000)/10000
    }
}
forvalues i=1/`nf' {
    matrix f[`i',1]=round(f[`i',1]*10000)/10000
}

** Construct cash flow received by family in round t from a dollar originating in firm j.
** cf`t' is a row vector (1 X nf) in which the jth correspond to the
** amount the family receives in round i from a dollar of dividend paid by firm j

matrix B=I                  //Initial dividend is 1 dollar paid by each firm
forvalues t=1/`nf' {
    matrix cf`t'=f'*B      //This is what the family receives in this round of dividends
    matrix       B=A*B     //This is what the group firms receive, which will be the dividend next round
}


** Create shortest distance
g sd=.
forvalues t=1/`nf' {
    forvalues firm=1/`nf' {
        replace sd=`t' if cf`t'[1,`firm']>0.00001 & _n==`firm' & sd==.
    }
}


**Create: firm part of loop and shortest loop
forvalues i=1/`nf' {
    matrix A[`i',`i']=0 // Eliminate entries in the diagonals (treasury stock) -- otherwise it looks as if there are loops
}

g steps=.
matrix C=I
forvalues i=1/`nf' {
        matrix C=C*A
    replace steps=`i' if C[_n,_n]>0 & steps[_n]==.
}
generate loop=0 if sd~=.
replace loop=1 if steps~=.

save cflow`group'`year', replace
