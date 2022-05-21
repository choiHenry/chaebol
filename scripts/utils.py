import requests
import numpy as np
import pandas as pd
import re
import math

def download(url, path):
    with open(path, "wb") as f:
        response = requests.get(url)
        f.write(response.content)

def catOwn(row):
    if row['동일인과의관계2'] == '동일인':
        return 0
    elif row['동일인과의관계2'] == '친족' and row['동일인과의관계3'] == '친족합계':
        return 0
    elif row['동일인과의관계2'] == '계열회사(국내+해외)':
        return 1
    elif row['동일인과의관계2'] == '계열회사':
        return 1
    elif row['동일인과의관계'] == '기타주주':
        return 99

def catOwn2(row):
    if row['동일인과의관계2'] in ['동일인', '비영리법인', '등기된임원', '자기주식']:
        return 0
    elif row['동일인과의관계2'] == '친족' and row['동일인과의관계3'] == '친족합계':
        return 0
    elif row['동일인과의관계2'] == '계열회사(국내+해외)':
        return 1
    elif row['동일인과의관계2'] == '계열회사':
        return 1
    elif row['동일인과의관계'] == '기타주주':
        return 99

def cleanColNm(colNm):
    colNm = colNm.str.replace(' ', '', regex=True)
    colNm = colNm.str.replace('㈜', '', regex=True)
    colNm = colNm.str.replace('\(주\)', '', regex=True)
    colNm = colNm.str.replace('\(유\)', '', regex=True)
    colNm = colNm.str.replace('주식회사', '', regex=True)
    colNm = colNm.str.replace('\(유\)', '', regex=True)
    colNm = colNm.str.replace('\(합\)', '', regex=True)
    colNm = colNm.str.replace('국내계열회사계', '국내계열사계', regex=True)
    colNm = colNm.str.replace('해외계열회사계', '해외계열사계', regex=True)
    colNm = colNm.str.replace('^해외계열사계$', '해외계열사계(매출액)', regex=True)
    colNm = colNm.str.replace('^국내계열사계$', '국내계열사계(매출액)', regex=True)
    colNm = colNm.str.replace('소속사', '', regex=True)
    colNm = colNm.str.replace('^\(매출액\)$', '해외계열사계(매출액)', regex=True)
    colNm = colNm.str.replace('^국내$', '국내매출액', regex=True)
    colNm = colNm.str.replace('^해외$', '해외매출액', regex=True)
    colNm = colNm.str.replace('국내매출액전체', '국내매출액', regex=True)
    colNm = colNm.str.replace('해외매출액전체', '해외매출액', regex=True)
    colNm = colNm.str.replace('\*주\d+', '', regex=True)
    colNm = colNm.str.replace('\(\*\d+\)', '', regex=True)
    colNm = colNm.str.replace('\*', '', regex=True)
    
    return colNm

def cleanCmpnyNm(df):
    df = df.replace(' ', '', regex=True)
    df = df.replace('합자회사', '', regex=True)
    df = df.replace('전문회사', '', regex=True)
    df = df.replace('유한회사', '', regex=True)
    df = df.replace('㈜', '', regex=True)
    # (주), (주1) 등 제거
    df = df.replace('\(주\d*\)', '', regex=True)
    df = df.replace('\(유\)', '', regex=True)
    df = df.replace('\(자\)', '', regex=True)
    df = df.replace('주식회사', '', regex=True)
    df = df.replace('\（*유\）', '', regex=True)
    df = df.replace('\（유\）', '', regex=True)
    df = df.replace('\(합\)', '', regex=True)
    df = df.replace('^\(구\)', '', regex=True)
    df = df.replace('^舊', '', regex=True)
    df = df.replace('^舊', '', regex=True)
    # ('18.10.10계열제외), (2019.04.30해산), (2019.04.30흡수합병해산) 등 제거
    df = df.replace("\('*\d+\.\d+\.\d+[\u3131-\u314e|\u314f-\u3163|\uac00-\ud7a3]+\)", '', regex=True)
    # (구,퍼니파우), (舊),한화첨단소재, (舊 한화테크윈), 舊한화지상방산 등 제거
    df = df.replace('(?<!^)[\(\（]*[舊구]+[\.\s]*[\),]*[\u3131-\u314e|\u314f-\u3163|\uac00-\ud7a3]*[\)\）]*', '', regex=True)
    df = df.replace('(?<!^)[\(\（]*[舊구]+[\.\s]*[\),]*[\w,\.]*[\)\）]*', '', regex=True)
    df = df.replace('\(구\)', '', regex=True)
    df = df.replace('\(\*\d+\)', '', regex=True)
    df = df.replace('\*', '', regex=True)
    df = df.replace('⑩', '', regex=True)
    df = df.replace('\.\d+', '', regex=True)
    df = df.replace('\.\d+', '', regex=True)
    df = df.replace('\\xa0', '', regex=True)
    

    return df

    # df = df.replace("\('\d+.\d+.\d+계열제외\)", '', regex=True)
    # df = df.replace("\('18.10.10계열제외\)", '', regex=True)
    # df = df.replace("\(\d+.\d+.\d+흡수합병해산\)", '', regex=True)
    # df = df.replace("\(2019.04.30흡수합병해산\)", '', regex=True)
    # df = df.replace("\(\d+.\d+.\d+해산\)", '', regex=True)
    # df = df.replace("\(2019.04.30해산\)", '', regex=True)
    # df = df.replace("\(2020.03.31해산\)", '', regex=True)
    # df = df.replace("\(2020.10.30해산\)", '', regex=True)
    # df = df.replace("\(\d+.\d+.\d+계열제외\)", '', regex=True)
    # df = df.replace("\(2018.8.27계열제외\)", '', regex=True)
    # df = df.replace("\(2018.11.23계열제외\)", '', regex=True)
    # df = df.replace("\(2018.12.13계열제외\)", '', regex=True)
    # df = df.replace("\(2019.2.14계열제외\)", '', regex=True)
    # df = df.replace("\(2018.6.11계열제외\)", '', regex=True)

    # df = df.replace('\(구,\s*[\u3131-\u314e|\u314f-\u3163|\uac00-\ud7a3]*\)', '', regex=True)
    # df = df.replace('\(구,퍼니파우\)', '', regex=True)
    # df = df.replace('\(구,넷마블블루\)', '', regex=True)
    # df = df.replace('\(구,천백십일\)', '', regex=True)
    # df = df.replace('\(舊\),한화첨단소재', '', regex=True)
    # df = df.replace('\(舊[\uac00-\ud7a3]*\)', '', regex=True)
    # df = df.replace('\(*舊\s*[\),]*[\u3131-\u314e|\u314f-\u3163|\uac00-\ud7a3]*\)*', '', regex=True)
    # df = df.replace('\(舊 한화테크윈\)', '', regex=True)
    # df = df.replace('\(舊 양주환경\)', '', regex=True)
    # df = df.replace('舊한화지상방산', '', regex=True)
    # df = df.replace('\（舊\s*[\u3131-\u314e|\u314f-\u3163|\uac00-\ud7a3]*\）', '', regex=True)
    # df = df.replace('\(舊\s*[\u3131-\u314e|\u314f-\u3163|\uac00-\ud7a3]*\）', '', regex=True)
    # df = df.replace('\(구[\uac00-\ud7a3]*\)', '', regex=True)
    # df = df.replace('舊', '', regex=True)
    # df = df.replace('\(주\d+\)', '', regex=True)
    # df = df.replace('\*주\d+', '', regex=True)


def convColNm(colNm):
    newColNm = []
    col_1 = None
    for colMul in list(colNm):
        for col in colMul:
            if (isinstance(col, float) and math.isnan(col)) or ('Unnamed:' in col):
                print(f"Null value found at {colMul}.")
                newColNm.append(colMul[-1])
                break
            col = re.sub(r"\s*", "", col)
            col = re.sub(r"\*", "", col)
            if ('매출회사' in col) or ('매도회사' in col) or ('매입회사' in col):
                newColNm.append('매출회사')
                col_1 = col
                break
            elif (col == '국내계열회사') or (col == '해외계열회사') or (col == '해외계열사회사') \
            or (col == '해외계열사') or (col == '매출액총계') or (col == '국내계열사계(매출액)') \
            or (col == '해외계열사계(매출액)') or (col == '계열회사') or (col == '매출액') \
            or (col == '국내계열사계') or (col == '해외계열사계') or (col == '해외계열회사계') \
            or (col == '기타'): # 유진기업(2020) - *기타: 매입자가 유진그룹 소속회사로 계열편입되기 전 직전사업연도 중 발생한 매출임.
                newColNm.append(colMul[-1])
                col_1 = col
                break
            elif (col == '금융회사') or (col == '비금융회사'):
                newColNm.append(colMul[-1])
                col_1 = col
                break
            elif (col == '(소속회사)'):
                newColNm.append('매출회사')
                break
            else:
                print(col)
    return newColNm

def cleanseTransWide(dfWide):

    # exclude a financial dummy variable for sales company
    dfWideT = dfWide.T
    dfWideV2 = dfWideT[~dfWideT[0].replace(' ', '', regex=True).isin(['금융회사', '비금융회사'])]
    dfWideV2 = dfWideV2.T

    # convert multiIndex column names to normal column names
    dfWideV2.columns = convColNm(dfWideV2.columns)

    # clean column names
    dfWideV2.columns = cleanColNm(dfWideV2.columns)
    
    # if there are multiple columns with the same name '매출회사' drop the others except the first one
    if isinstance(dfWideV2['매출회사'], pd.DataFrame):
        srSales = dfWideV2['매출회사'].iloc[:,0]
        dfWideV2 = dfWideV2.drop(columns=['매출회사'])
        dfWideV2['매출회사'] = srSales
    
    # exclude row that contains aggregate data
    dfWideV2 = dfWideV2[~dfWideV2['매출회사'].duplicated()]
    dfWideV2 = dfWideV2[dfWideV2['매출회사'] != '소계']
    dfWideV2 = dfWideV2[dfWideV2['매출회사'] != '합계']

    # exclude row that contains aggregate information
    dfWideV2T = dfWideV2.T.reset_index()
    dfWideV2T = dfWideV2T[~dfWideV2T['index'].isin(['소계', '합계', '계', '거래업체수', '해외계열사업체수'])]
    dfWideV3 = dfWideV2T.set_index('index').T

    # clean sales data
    dfWideV3 = cleanSalesData(dfWideV3)

    # clean company name
    cleanCmpnyNm(dfWideV3['매출회사'])
    dfWideV3 = dfWideV3[~dfWideV3['매출회사'].isna()]

    # split wide to rhs / lhs
    dfRhs = dfWideV3.loc[:, ['매출회사', '국내계열사계(매출액)', '해외계열사계(매출액)', '국내매출액', '해외매출액']]
    dfLhs = dfWideV3.drop(columns=['국내계열사계(매출액)', '해외계열사계(매출액)', '국내매출액', '해외매출액'])

    # convert wide to long
    dfLhs = dfLhs.set_index('매출회사').stack().reset_index()
    dfLhs.columns = ['매출회사', '매입회사', '매출액']

    # merge long with rhs
    dfMrgd = dfLhs.merge(dfRhs, on='매출회사', how='left')
    
    # clean company name once more
    dfMrgd.loc[:, '매출회사'] = cleanCmpnyNm(dfMrgd['매출회사'])
    dfMrgd.loc[:, '매입회사'] = cleanCmpnyNm(dfMrgd['매입회사'])

    return dfMrgd

def getGrpCmpnyDict(year):
    
    dfAppnGroupSttus = pd.read_excel(f'../data/grpSumry/appnGroupSttus/appnGroupSttus{year}.xlsx')
    dfAppnGroupSttus = dfAppnGroupSttus[dfAppnGroupSttus['smerNm'].str.len() <= 3]
    dfAppnGroupSttus = dfAppnGroupSttus.reset_index().drop(columns=['index'])
    dfAppnGroupSttus['repreCmpny'] = cleanCmpnyNm(dfAppnGroupSttus['repreCmpny'])
    
    dfAppnGroupSttus['repreCmpny'].replace('에스케이', 'SK', regex=True, inplace=True)
    dfAppnGroupSttus['repreCmpny'].replace('엘지', 'LG', regex=True, inplace=True)
    dfAppnGroupSttus['repreCmpny'].replace('지에스', 'GS', regex=True, inplace=True)
    dfAppnGroupSttus['repreCmpny'].replace('한진칼', '대한항공', regex=True, inplace=True)
    dfAppnGroupSttus['repreCmpny'].replace('씨제이', 'CJ', regex=True, inplace=True)
    dfAppnGroupSttus['repreCmpny'].replace('엘에스', 'LS', regex=True, inplace=True)
    dfAppnGroupSttus['repreCmpny'].replace('네이버', 'NAVER', regex=True, inplace=True)
    dfAppnGroupSttus['repreCmpny'].replace('에이치디씨', 'HDC', regex=True, inplace=True)
    dfAppnGroupSttus['repreCmpny'].replace('디엘', 'DL', regex=True, inplace=True)
    dfAppnGroupSttus['repreCmpny'].replace('에쓰-오일', 'S-Oil', regex=True, inplace=True)
    dfAppnGroupSttus['repreCmpny'].replace('오씨아이', 'OCI', regex=True, inplace=True)
    dfAppnGroupSttus['repreCmpny'].replace('한국투자금융지주', '한국금융지주', regex=True, inplace=True)
    dfAppnGroupSttus['repreCmpny'].replace('디비아이엔씨', 'DB', regex=True, inplace=True)
    dfAppnGroupSttus['repreCmpny'].replace('에이케이홀딩스', 'AK홀딩스', regex=True, inplace=True)
    dfAppnGroupSttus['repreCmpny'].replace('케이지케미칼', 'KG케미칼', regex=True, inplace=True)
    dfAppnGroupSttus['repreCmpny'].replace('현대해상화재보험', '현대해상', regex=True, inplace=True)
    
    dGrpCmpny = {}
    for i in range(len(dfAppnGroupSttus)):
        dGrpCmpny[dfAppnGroupSttus.loc[i, 'unityGrupNm']] = dfAppnGroupSttus.loc[i, 'repreCmpny']
    
    return dGrpCmpny

def makeHeader(df, firmNm, year):
    nHeaders = 0
    for data in df[0]:
        if ('매출회사' in data) or ('매도회사' in data) or ('매입회사' in data):
            nHeaders += 1
        else:
            break
    if nHeaders <= 0:
        if (firmNm == 'OCI' and year == 2020):
            nHeaders = 3
        elif (firmNm == 'OCI' and year == 2021):
            nHeaders = 2
        else:
            raise Exception("Sales company name column not found. Please check the original document.")
    df.columns = list(zip(*df.iloc[list(range(nHeaders)), :].values))
    df = df.drop(list(range(nHeaders)))
    df.reset_index(inplace=True)
    df.drop(columns=['index'], inplace=True)
    return df

def cleanSalesData(df):

    df.set_index('매출회사', inplace=True)

    df.replace('-+', np.nan, regex=True, inplace=True)
    df.replace('_', np.nan, regex=True, inplace=True)
    df.replace(',', np.nan, regex=True, inplace=True)
    df.replace('"*해당사항\s*없음"*', np.nan, regex=True, inplace=True)
    # df.replace('"해당사항없음', np.nan, inplace=True)
    # df.replace('"해당사항없음"', np.nan, inplace=True)
    # df.replace('해당사항없음', np.nan, inplace=True)
    df.replace("\(주\d\)", np.nan, regex=True, inplace=True)
    df.replace("\((\d+)\)", '-\\1', regex=True, inplace=True)
    df.replace('', np.nan, inplace=True) # regex keyword is set to False
    # df.replace("\(주2\)", np.nan, regex=True, inplace=True)
    df = df.astype('float')

    df = df.reset_index()

    return df