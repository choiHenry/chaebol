import requests
import zipfile
import xml.etree.ElementTree as ET
import os
import pickle
import re
from utils import download, cleanCmpnyNm, cleanColNm, cleanSalesData, catOwn, catOwn2, \
getGrpCmpnyDict, cleanseTransWide, makeHeader
from selenium import webdriver
import chromedriver_autoinstaller
import numpy as np
import pandas as pd
from time import sleep
from os import path
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

chromedriver_autoinstaller.install(path="../utils/")

class Api:
    
    def __init__(self, apiKey):
        
        self.apiKey = apiKey
        self.corpCode = None

    def getCorpCode(self, path):

        url = "https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key=" + self.apiKey
        download(url, path)

        with zipfile.ZipFile(path, 'r') as zipObj:
            fileList = zipObj.namelist()
            target = fileList[0]
        
        loc = os.path.normpath(path)
        loc = loc.split(os.sep)
        loc = '/'.join(loc[:-1])
        
        with zipfile.ZipFile(path, 'r') as zipRef:
            zipRef.extractall(loc)

        self.corpCode = loc + '/' + target
        print(f'Corporation Code File downloaded to {self.corpCode}')

    def findCorpCode(self, corpNm):
        
        if not self.corpCode:
            print('No corporation code file found. Downloading the code file...')
            self.getCorpCode('../data/raw/opendart/corpCode/CORPCODE.zip')

        xml = ET.parse(self.corpCode)
        root = xml.getroot()

        lists = root.findall('list')

        codeList = []
        for list in lists:
            if (list.find('corp_name').text == corpNm):
                codeList.append(list.find('corp_code').text)
                
        return codeList

    def findCorpCode(self, corpNm):
        
        if not self.corpCode:
            print('No corporation code file found. Downloading the code file...')
            self.getCorpCode('../data/raw/opendart/corpCode/CORPCODE.zip')

        xml = ET.parse(self.corpCode)
        root = xml.getroot()

        lists = root.findall('list')

        codeList = []
        for list in lists:
            if (list.find('corp_name').text == corpNm):
                codeList.append(list.find('corp_code').text)
        return codeList

    def findRceptNum(self, corpNm, year):

        codeList = self.findCorpCode(corpNm)
        pblntfTy = 'j'
        pblntfDetailTy = "J004"
        pgCnt = "50"
        bgnDe = str(year) + '0501'
        endDe = str(year+1) + '0430'
        if (corpNm in ['아모레퍼시픽그룹'] and year == 2020) or (corpNm in ['아이엠엠인베스트먼트'] and year == 2020):
            bgnDe = str(year) + '0501'
            endDe = str(year+1) + '0830'

        # find the firm that submitted reports to FTC whose name is <firmname>
        for corpCode in codeList:
            url = "https://opendart.fss.or.kr/api/list.json?corp_code=" + corpCode + "&crtfc_key=" + self.apiKey \
            + "&bgn_de=" + bgnDe + "&end_de=" + endDe + "&last_reprt_at=Y" + "&pblntf_ty=" + pblntfTy + \
            "&pblntf_detail_ty=" + pblntfDetailTy + "&page_count=" + pgCnt
            res = requests.get(url)
            content = res.json()
            if 'list' in content:
                break
        
        else:
            raise ValueError(f"{corpNm}: no report found for {bgnDe} ~ {endDe}")


        # find all the reports whose names contain the string '대규모기업집단현황공시[연1회공시및1/4분기용' and save as a list
        # and return rcept_no of the last report in the list
        receptNums = [report['rcept_no'] for report in content['list'] if ('대규모기업집단현황공시[연1회공시및1/4분기용(대표회사)]' \
                        in report['report_nm'])]
        
        if (corpNm in ['아모레퍼시픽그룹', '아이엠엠인베스트먼트'] and year == 2021) \
        or (corpNm in ['교보생명보험'] and year == 2019) \
        or (corpNm in ['한국앤컴퍼니'] and year == 2020) \
        or (corpNm in ['아모레퍼시픽그룹'] and year == 2019) \
        :
            receptNums = [receptNums[0]] # select the last report received
        elif (corpNm in ['아모레퍼시픽그룹', '아이엠엠인베스트먼트'] and year == 2020):
            receptNums = [receptNums[1]] # select the first report received
        
        assert len(receptNums) >= 1, f'{corpNm}: no 대규모기업집단현황공시[연1회공시및1/4분기용(대표회사)] found for {bgnDe} ~ {endDe}'
        assert len(receptNums) <= 1, f'{corpNm}: Too many 대규모기업집단현황공시[연1회공시및1/4분기용(대표회사)] report found'

        return receptNums[0]

    def getSharesUrl(self, corpNm, year):

        rceptNum = self.findRceptNum(corpNm, year)
        driver = webdriver.Chrome()
        driver.implicitly_wait(3)
        url = "http://dart.fss.or.kr/dsaf001/main.do?rcpNo=" + rceptNum
        driver.get(url)

        # In the navigation menu click the link that contains the string '소유지분현황'
        driver.find_element_by_partial_link_text('소유지분현황').click()

        # get the url of the '소유지분현황' page and return it
        sharesURL = driver.find_element_by_id('ifrm').get_attribute('src')
        
        # quit
        driver.quit()

        return sharesURL

    def getSharesTable(self, corpNm, year):
        
        # get shares url
        url = self.getSharesUrl(corpNm, year)
        
        # parse html tables which includes string data '동일인'(the same person in Korean) with thousands delimiter ',' 
        tables = pd.read_html(url, match='동일인', thousands=',')
        
        # convert column names
        for table in tables:
            if len(table.columns) != 12:
                print(table.head())
                
            if len(table.columns) == 11 and corpNm == '미래에셋캐피탈' and year == 2021:
                table.insert(4, '금융회사', np.nan)
            elif len(table.columns) == 10 and corpNm == '미래에셋캐피탈' and year == 2021:
                table.insert(2, '동일인과의관계', '동일인측')
                table.insert(4, '동일인과의관계3', '계열회사(국내+해외)')
            elif len(table.columns) == 9 and corpNm == '미래에셋캐피탈' and year == 2021:
                table.insert(4, '금융회사', np.nan)
                table.insert(8, '우선주주식수', np.nan)
                table.insert(9, '우선주지분율', np.nan)
                
            table.columns = ['금융회사', '소속회사명', '동일인과의관계', '동일인과의관계2', '동일인과의관계3', '성명', \
                             '보통주주식수', '보통주지분율', '우선주주식수', '우선주지분율', '합계주식수', '합계지분율']
            
        # concat tables
        df = pd.concat(tables)
        df.reset_index(inplace=True)
        df.drop(columns=['index'], inplace=True)
        df = df[df['소속회사명'] != '소속회사명']
        
        # data cleaning
        clean(df['소속회사명'])
        clean(df['성명'])
        df[['동일인과의관계', '동일인과의관계2', '동일인과의관계3']] = df[['동일인과의관계', '동일인과의관계2', '동일인과의관계3']].replace(' ', '', regex=True)
        df[['동일인과의관계', '동일인과의관계2', '동일인과의관계3']] = df[['동일인과의관계', '동일인과의관계2', '동일인과의관계3']].replace('⑧', '', regex=True)
        df[['동일인과의관계', '동일인과의관계2', '동일인과의관계3']] = df[['동일인과의관계', '동일인과의관계2', '동일인과의관계3']].replace('⑨', '', regex=True)
        df['합계주식수'].replace('^-$', '', regex=True, inplace=True)
        df['합계주식수'] = df['합계주식수'].copy().replace('', np.nan,regex=True)
        df['합계주식수'] = df['합계주식수'].copy().astype(float)

        return df
    
    def getSharesTableAll(self, year):
        
        dGrpCmpny = getGrpCmpnyDict(year)
        
        for grp, cmpny in dGrpCmpny.items():
            dfShares = api.getSharesTable(cmpny, year)
            # save the data in the after_cleansing folder
            if not os.path.exists(f'../data/ownership-status/raw/{year}'):
                os.makedirs(f'../data/ownership-status/raw/{year}')
            dfShares.to_excel(f'../data/ownership-status/raw/{year}/{grp}.xlsx', index=False)
            print("="* 15 + cmpny + "=" * 15)
            print(dfShares.head())
            print(dfShares.tail())
            print(dfShares['동일인과의관계'].unique())
            print(dfShares['동일인과의관계2'].unique())
            print(dfShares['동일인과의관계3'].unique())
            print("="* 15 + cmpny + "=" * 15)
            
    def getTransUrl(self, firmNm, year):
        
        rceptNo = self.findRceptNum(firmNm, year)
        driver = webdriver.Chrome()
        driver.maximize_window()
        driver.implicitly_wait(3)
        url = "http://dart.fss.or.kr/dsaf001/main.do?rcpNo=" + rceptNo

        driver.get(url)
        action = ActionChains(driver)
        action.move_to_element(driver.find_element(By.ID, '30')).perform()
        btn = driver.find_element(By.PARTIAL_LINK_TEXT, '계열회사간 상품ㆍ용역거래 현황')
        btn.click()

        # scrape the url of '계열회사간 상품ㆍ용역거래 현황' page
        transUrl = driver.find_element(By.ID, 'ifrm').get_attribute('src')
        driver.quit()
        
        return transUrl
    
    def getTransTableTest(self, firmNm, year):
        
        if not os.path.exists(f'./data/transactions{year}'):
            os.makedirs(f'./data/transactions{year}')
        
        rceptNo = self.findRceptNum(firmNm, year)
        driver = webdriver.Chrome()
        driver.maximize_window()
        driver.implicitly_wait(3)
        url = "http://dart.fss.or.kr/dsaf001/main.do?rcpNo=" + rceptNo

        driver.get(url)
        action = ActionChains(driver)
        action.move_to_element(driver.find_element(By.ID, '30')).perform()
        btn = driver.find_element(By.PARTIAL_LINK_TEXT, '계열회사간 상품ㆍ용역거래 현황')
        btn.click()
        transUrl = driver.find_element_by_id('ifrm').get_attribute('src')
        
        driver.get(transUrl)
        
        
        # get table elements which are following siblings of p elements that contains text '대표회사'

        tables = driver.find_elements(By.XPATH, "/html/body/table[@border='1']")
        
#             dfTables = [pd.read_html(table.get_attribute('outerHTML'), header=[0, 1, 2])[0] for table in tables]
#         else:    
        dfTables = [pd.read_html(table.get_attribute('outerHTML'))[0] for table in tables]
        if ((firmNm == "SK") and (year == 2021)) or ((firmNm == "롯데지주") and (year in [2019, 2020, 2021]))\
        or ((firmNm == "미래에셋캐피탈") and (year in [2019, 2020, 2021])) \
        or ((firmNm == "NAVER") and (year in [2020, 2021])) \
        or ((firmNm == "효성") and (year in [2019, 2020, 2021])):
            dfTables = [makeHeader(table) for table in dfTables]
        dfTables = [dfTable for dfTable in dfTables if len(dfTable) > 5]
        dfWide = pd.concat(dfTables, axis=1)
        driver.quit()
        
        return dfWide

    def getTransTable(self, firmNm, year):

        if not os.path.exists(f'./data/transactions{year}'):
            os.makedirs(f'./data/transactions{year}')
        
        rceptNo = self.findRceptNum(firmNm, year)
        driver = webdriver.Chrome()
        driver.maximize_window()
        driver.implicitly_wait(3)
        url = "http://dart.fss.or.kr/dsaf001/main.do?rcpNo=" + rceptNo

        driver.get(url)
        action = ActionChains(driver)
        action.move_to_element(driver.find_element(By.ID, '30')).perform()
        btn = driver.find_element(By.PARTIAL_LINK_TEXT, '계열회사간 상품ㆍ용역거래 현황')
        btn.click()
        transUrl = driver.find_element_by_id('ifrm').get_attribute('src')
        
        driver.get(transUrl)
        
        
        # get table elements which are following siblings of p elements that contains text '대표회사'

        tables = driver.find_elements(By.XPATH, "/html/body/table[@border='1']")
        
#             dfTables = [pd.read_html(table.get_attribute('outerHTML'), header=[0, 1, 2])[0] for table in tables]
#         else:    
        dfTables = [pd.read_html(table.get_attribute('outerHTML'))[0] for table in tables]
        if ((firmNm == "SK") and (year == 2021)) or ((firmNm == "롯데지주") and (year in [2019, 2020, 2021]))\
        or ((firmNm == "미래에셋캐피탈") and (year in [2019, 2020, 2021])) \
        or ((firmNm == "NAVER") and (year in [2020, 2021])) \
        or ((firmNm == "효성") and (year in [2019, 2020, 2021])) \
        or ((firmNm == "하림지주") and (year in [2019, 2020, 2021])) \
        or ((firmNm == "OCI") and (year in [2020, 2021])) \
        or ((firmNm == "티케이케미칼") and (year in [2019, 2020])) \
        or ((firmNm == "이랜드월드") and (year in [2019])) \
        or ((firmNm == "장금상선") and (year in [2020])):
            dfTables = [makeHeader(table, firmNm, year) for table in dfTables]
        dfTables = [dfTable for dfTable in dfTables if len(dfTable) > 5]
        dfWide = pd.concat(dfTables, axis=1)
        driver.quit()
        
        dfLong = cleanseTransWide(dfWide)
        
        dfLong = dfLong[~dfLong['매출회사'].isin(['소계', '합계', '계', '거래업체수', '해외계열사업체수', '계열회사합계매입액', \
                                             '비금융소계', '금융회사', '기타', '해외계열사수', '해외계열사계매출액한화', \
                                             '기타(루셈등)', '계열회사합계(매입액)', '⑩소계'])]
        dfLong = dfLong[~dfLong['매입회사'].isin(['소계', '합계', '계', '거래업체수', '해외계열사업체수', '해외계열회사업체수', \
                                             '비금융소계', '금융회사', '기타', '해외계열사수', '해외계열사계매출액한화', \
                                              '기타(루셈등)', '계열회사합계(매입액)', '⑩소계'])]
        
        return dfLong
    
    def getTransTableAll(self, year):
        
        dGrpCmpny = getGrpCmpnyDict(year)
        
        cont = True
        for grp, cmpny in dGrpCmpny.items():
            print("="* 15 + grp + "=" * 15)
            
            if grp == '삼성':
                cont = False
            
            if cont:
                continue
                
            dfTransLong = api.getTransTable(cmpny, year)
            # save the data in the after_cleansing folder
            if not os.path.exists(f'../data/transactions/{year}'):
                os.makedirs(f'../data/transactions/{year}')
            dfTransLong.to_excel(f'../data/transactions/{year}/{grp}.xlsx', index=False)
            
            print(dfTransLong['매출회사'].unique())
            print(dfTransLong['매입회사'].unique())
            print(dfTransLong.head())
            print(dfTransLong.tail())
            print("="* 15 + grp + "=" * 15)

    def scrapeKiscode(self, year, username, password):

        df = pd.read_excel(f'../data/cmpnySumry/cmpnySumry{year}Eng.xlsx')
        if 'rcmgCode' in df.columns:
            raise ValueError(f'Rcmg code already exists in cmpnySumry{year}Eng.xlsx')

        df_1 = pd.read_excel(f'../data/cmpnySumry/cmpnySumry{year+1}Eng.xlsx')
        if 'rcmgCode' in df_1.columns:
            df = df.merge(df_1[['jurirno', 'rcmgCode']], on='jurirno', how='left')
            dfTrgt = df[df['rcmgCode'].isna()]
            dfTrgt.drop(columns=['rcmgCode'], inplace=True)
        else:
            dfTrgt = df

        print(f"Rcmg code missing for {len(dfTrgt)} companies")

        driver = webdriver.Chrome()
        driver.implicitly_wait(3)

        grsrch_url = 'https://www.kisline.com/cm/CM0100M00GE00.nice'
        driver.get(grsrch_url)
        driver.find_element(By.CLASS_NAME'btn_close_layer').click()
        driver.find_element(By.ID, 'lgnuid').send_keys(username)
        driver.find_element(By.ID, 'tmp_lgnupassword').click()
        driver.find_element(By.ID, 'lgnupassword').send_keys(password)
        driver.find_element(By.CLASS_NAME'btn_log_in').click()
        driver.implicitly_wait(3)
        sleep(1)

        dKiscode = dict()
        inputElem = driver.find_element_by_id('q')

        for i, jurirno in enumerate(dfTrgt['jurirno']):

            inputElem.send_keys(jurirno)
            driver.find_element_by_id('searchView').click()
            driver.implicitly_wait(3)
            try:
                target_row = driver.find_element_by_xpath('//*[@id="eprTable"]/tbody/tr/td[2]')
                kiscode = target_row.get_attribute('data-kiscode')
                dKiscode[i] = [jurirno, kiscode]
                print(f"Found kiscode for {jurirno}: {kiscode}")
            except:
                dKiscode[i] = [jurirno, np.nan]
                print(f"No company found for {jurirno}. Continuing...")
            sleep(3)
            inputElem = driver.find_element_by_id('q')
            inputElem.clear()

        sleep(3)
        driver.find_element_by_link_text('로그아웃').click()
        sleep(1)
        driver.quit()

        dfKiscode = pd.DataFrame.from_dict(dKiscode, orient='index')
        dfKiscode.columns = ['jurirno', 'kiscode']
        
        dfCharToInt = pd.read_excel('../data/utils/char-to-int.xlsx')
        dfKiscode['rcmgCode'] = dfKiscode['kiscode']
        for i in range(len(dfCharToInt)):
            dfKiscode['rcmgCode'] = dfKiscode['rcmgCode'].replace(dfCharToInt.iloc[i, 0], str(dfCharToInt.iloc[i, 1]), regex=True)
        dfLhs = df[~df['rcmgCode'].isna()]

        dfRhs = dfTrgt.merge(dfKiscode[['jurirno', 'rcmgCode']], on='jurirno', how='left')

        dfMrgd = pd.concat([dfLhs, dfRhs], axis=0)
        dfMrgd.reset_index(inplace=True)
        dfMrgd.drop(columns=['index'], inplace=True)

        print(dfMrgd[dfMrgd['rcmgCode'].isna()])

        dfMrgd.to_excel(f'../data/cmpnySumry/cmpnySumry{year}Eng.xlsx', index=False)

        return dfMrgd


if __name__ == '__main__':
    apiKey = "7946dcde119af7656afc01157071c0ab9488b9ad"
    api = Api(apiKey)
    api.scrapeKiscode(2018, 'wonbok', 'gkrtkrhk5034!')