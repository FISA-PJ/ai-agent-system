import os
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from elasticsearch import Elasticsearch

class LHAnnouncementScraper:
    def __init__(self, chromedriver_path, download_dir="./downloads"):
        self.BASE_URL = "https://apply.lh.or.kr"
        self.LIST_URL = f"{self.BASE_URL}/lhapply/apply/wt/wrtanc/selectWrtancList.do?viewType=srch"
        self.DOWNLOAD_URL = f"{self.BASE_URL}/lhapply/lhFile.do"
        self.HEADERS = {"User-Agent": "Mozilla/5.0"}

        self.download_dir = download_dir
        os.makedirs(self.download_dir, exist_ok=True)

        chrome_opts = Options()
        chrome_opts.add_argument("--headless")
        chrome_opts.add_argument("--disable-gpu")
        chrome_opts.add_argument(f"user-agent={self.HEADERS['User-Agent']}")

        self.driver = webdriver.Chrome(service=Service(chromedriver_path), options=chrome_opts)
        self.wait = WebDriverWait(self.driver, 10)
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def search_list(self):
        Select(self.driver.find_element(By.ID, "srchTypeAisTpCd")).select_by_value("05")
        WebDriverWait(self.driver, 5).until(EC.visibility_of_element_located((By.ID, "aisTpCdData05")))
        Select(self.driver.find_element(By.ID, "aisTpCdData05")).select_by_value("")
        Select(self.driver.find_element(By.ID, "cnpCd")).select_by_value("")
        Select(self.driver.find_element(By.ID, "panSs")).select_by_value("")

        today = datetime.today().date()
        start_input = self.driver.find_element(By.ID, "startDt")
        start_input.send_keys(Keys.CONTROL, "a", Keys.DELETE)
        start_input.send_keys(today.strftime("%Y-%m-%d"))

        end_input = self.driver.find_element(By.ID, "endDt")
        end_input.send_keys(Keys.CONTROL, "a", Keys.DELETE)
        end_input.send_keys(today.strftime("%Y-%m-%d"))

        self.wait.until(EC.element_to_be_clickable((By.ID, "btnSah"))).click()
        time.sleep(3)

    def get_max_page(self):
        self.driver.get(self.LIST_URL)
        time.sleep(1)
        self.search_list()

        row_links = self.driver.find_elements(By.CSS_SELECTOR, "a.wrtancInfoBtn")
        if not row_links:
            print("❌ 공고가 없습니다. 오늘 날짜에는 공고가 없습니다.")
            return 0

        try:
            last_page_btn = self.driver.find_element(By.CSS_SELECTOR, ".bbs_arr.pgeR2")
            onclick = last_page_btn.get_attribute("onclick")
            return int(onclick.split("(")[1].split(")")[0])
        except:
            print("📄 페이지 버튼 없음 → 1페이지만 존재")
            return 1


    def crawl_announcements(self):
        max_page = self.get_max_page()
        url_list = []

        for page in range(1, max_page + 1):
            print(f"\n📄 페이지 {page} 탐색 중")
            self.driver.execute_script(f"goPaging({page});")
            time.sleep(2)

            row_links = self.driver.find_elements(By.CSS_SELECTOR, "a.wrtancInfoBtn")

            for idx in range(len(row_links)):
                try:
                    row_links = self.driver.find_elements(By.CSS_SELECTOR, "a.wrtancInfoBtn")
                    link = row_links[idx]
                    wrtan_no = link.get_attribute("data-id1")
                    link.click()
                    time.sleep(2)

                    try:
                        pub_date_text = self.driver.find_element(By.XPATH, "//li[strong[text()='공고일']]").text
                        pub_date = pub_date_text.replace("공고일", "").strip().replace(".", "")
                    except:
                        pub_date = datetime.today().strftime("%Y%m%d")

                    try:
                        dl = self.driver.find_element(By.CSS_SELECTOR, "dl.col_red")
                        dl.find_element(By.XPATH, ".//dt[text()='공고문']")
                        list_items = dl.find_elements(By.XPATH, ".//dd//ul[contains(@class,'file')]/li")
                    except:
                        print("⚠️ 공고문 없음")
                        self.driver.back()
                        time.sleep(2)
                        self.search_list()
                        continue

                    for li in list_items:
                        try:
                            a_dl = li.find_element(By.XPATH, "./a[1]")
                            filename = a_dl.text.strip()
                            
                            if not filename.lower().endswith('.pdf'):
                                continue
                            
                            href_js = a_dl.get_attribute("href")
                            file_id = href_js.split("'")[1]
                            file_url = f"{self.DOWNLOAD_URL}?fileid={file_id}"

                            url_list.append((file_url, {
                                "wrtan_no": wrtan_no,
                                "pub_date": pub_date,
                                "filename": filename
                            }))

                            # 파일 다운로드 (선택적)
                            response = self.session.get(file_url, headers={
                                "User-Agent": self.HEADERS["User-Agent"],
                                "Referer": self.driver.current_url
                            })
                            response.raise_for_status()

                            save_path = os.path.join(self.download_dir, f"{wrtan_no}_{pub_date}_{filename}")
                            with open(save_path, "wb") as f:
                                f.write(response.content)
                            print(f"✅ 저장 완료: {save_path}")

                        except Exception as e:
                            print(f"⚠️ 파일 오류: {e}")

                    self.driver.back()
                    time.sleep(2)
                    self.search_list()
                
                except Exception as e:
                    print(f"⚠️ 공고 처리 중 오류: {e}")

        return url_list

    def close(self):
        self.driver.quit()

from pdf_processor import pdfProcessor
import tempfile

# 사용 예시
if __name__ == '__main__':
    scraper = LHAnnouncementScraper(chromedriver_path="./chromedriver.exe")
    max_page = scraper.get_max_page()
    if max_page == 0:
        scraper.close()
        exit("🛑 종료: 공고 없음")
    pdf_infos = scraper.crawl_announcements()
    scraper.close()
    
    batch_size = 32
    index_name = 'rag-test2'
    es =  Elasticsearch('http://localhost:9200')
    
    processor = pdfProcessor(es, index_name)
    for url, meta in pdf_infos:
        try:
            resp = scraper.session.get(url, headers={"Referer": scraper.BASE_URL})
            resp.raise_for_status()
            safe_name = f"{meta['wrtan_no']}_{meta['filename']}".replace('/', '_').replace('\\', '_')

            # 1. 임시 PDF 파일로 저장
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(resp.content)
                tmp_file_path = tmp_file.name
            
            # 2. 기존 pdfProcessor의 함수 사용
            text = processor.pdf_parser(tmp_file_path)
            chunks = processor.text_chunking(text)
            embeddings = processor.text_embedding(chunks, batch_size)
            processor.upload_embeddings_to_es(chunks, embeddings, safe_name, batch_size=16)
            
            # 4. 임시 PDF 삭제
            os.remove(tmp_file_path)
            
        except Exception as e:
            print(f"⚠️ {meta['filename']} 실패: {e}")