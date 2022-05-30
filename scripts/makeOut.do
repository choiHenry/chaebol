// clear
// cd "/Users/choidamian/Chaebol/data/ownership-input-id/2021in/삼성"
// import excel "삼성2021raw.xlsx", first
// save "./삼성2021raw.dta"
// clear
// do gmatrix 삼성 2021
// do gcflowsap 삼성 2021
// do gvotes 삼성 2021
// do gcentrality 삼성 2021
// clear
// use "/Users/choidamian/Chaebol/data/ownership-input-id/2021in/삼성/cent삼성2021.dta"
// merge m:m firmid using "/Users/choidamian/Chaebol/data/ownership-input-id/2021in/삼성/cflow삼성2021.dta"
// drop _merge
// merge m:m firmid using "/Users/choidamian/Chaebol/data/ownership-input-id/2021in/삼성/v삼성2021.dta"
// drop _merge
// merge m:m firmid using "/Users/choidamian/Chaebol/data/ownership-input-id/2021in/삼성/cent삼성2021.dta"
// drop _merge
// keep firmid fid ultown avpos sd step loop lastcontrol central
// gen grpname2 = "삼성"
// save "/Users/choidamian/Chaebol/data/ownership-input-id/2021out/삼성2021.dta"

local 기업집단_local 삼성 현대자동차 에스케이 엘지 롯데 한화 지에스 현대중공업 신세계 씨제이 한진 두산 엘에스 부영 카카오 DL 미래에셋 현대백화점 금호아시아나 셀트리온 한국투자금융 교보생명보험 네이버 에이치디씨 효성 영풍 하림 케이씨씨 넥슨 넷마블 호반건설 SM DB 코오롱 한국타이어 오씨아이 태영 이랜드 세아 중흥건설 태광 동원 한라 아모레퍼시픽 IMM인베스트먼트 삼천리 금호석유화학 다우키움 장금상선 동국제강 애경 반도홀딩스 유진 하이트진로 삼양 대방건설 현대해상화재보험 엠디엠 아이에스지주 중앙

foreach 기업집단 of local 기업집단_local {
	clear
	cd `"/Users/choidamian/Chaebol/data/ownership-input-id/2021in/`기업집단'"'
	import excel `"./`기업집단'2021raw.xlsx"', first
	save `"./`기업집단'2021raw.dta"', replace
	clear
	do gmatrix `기업집단' 2021
	do gcflowsap `기업집단' 2021
	do gvotes `기업집단' 2021
	do gcentrality `기업집단' 2021
	clear
	use `"./`기업집단'2021.dta"'
	merge m:m firmid using `"./cflow`기업집단'2021.dta"'
	drop _merge
	merge m:m firmid using `"./v`기업집단'2021.dta"'
	drop _merge
	merge m:m firmid using `"./cent`기업집단'2021.dta"'
	drop _merge
	keep firmid fid ultown avpos sd step loop lastcontrol central
	gen grpname2 = "`기업집단'"
	save `"/Users/choidamian/Chaebol/data/ownership-input-id/2021out/`기업집단'2021.dta"', replace
 }
