import sys
sys.path.append('../scripts')

import requests
import zipfile
import xml.etree.ElementTree as ET
import os
import pickle
from utils import download, clean, catOwn, catOwn2
from selenium import webdriver
import chromedriver_autoinstaller
import numpy as np
import pandas as pd

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
        
        if (corpNm in ['아모레퍼시픽그룹', '아이엠엠인베스트먼트'] and year == 2021):
            receptNums = [receptNums[0]] # select the last report received
        
        assert len(receptNums) >= 1, f'{corpNm}: no 대규모기업집단현황공시[연1회공시및1/4분기용(대표회사)] found for {bgnDe} ~ {endDe}'
        assert len(receptNums) <= 1, f'{corpNm}: Too many 대규모기업집단현황공시[연1회공시및1/4분기용(대표회사)] report found'

        return receptNums[0]

    def getSharesURL(self, corpNm, year):

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
        url = self.getSharesURL(corpNm, year)
        
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

        # save the data in the after_cleansing folder
        if not os.path.exists(f'../data/ownership-status/raw/{year}'):
            os.makedirs(f'../data/ownership-status/raw/{year}')
        df.to_excel(f'../data/ownership-status/raw/{year}/{corpNm}.xlsx', index=False)

        return df
    
    def getSharesTableAll(self, year):
        
        dfAppnGroupSttus = pd.read_excel(f'../data/grpSumry/appnGroupSttus/appnGroupSttus{year}.xlsx')
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
        dfAppnGroupSttus['repreCmpny'].replace('현대해상화재보험', '현대해상', regex=True, inplace=True)
        clean(dfAppnGroupSttus)
        
        with open(f'../data/utils/gNonChaebol{year}.pkl', 'rb') as f:
            gNonChaebol = pickle.load(f)
        
        for cmpny in dfAppnGroupSttus['repreCmpny']:
            if cmpny in gNonChaebol['cmpny']:
                continue
            dfShares = api.getSharesTable(cmpny, year)
            print("="* 15 + cmpny + "=" * 15)
            print(dfShares.head())
            print(dfShares.tail())
            print(dfShares['동일인과의관계'].unique())
            print(dfShares['동일인과의관계2'].unique())
            print(dfShares['동일인과의관계3'].unique())
            print("="* 15 + cmpny + "=" * 15)

if __name__ == '__main__':
    apiKey = "7946dcde119af7656afc01157071c0ab9488b9ad"
    api = Api(apiKey)