# Importing Libraries
import time
import random
import requests
import asyncio
import os
import re
import json
import uuid
import datetime
from typing import List
from duckduckgo_search import DDGS
from googlesearch import search as google_search
from langchain_core.runnables import RunnableLambda
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from newspaper import Article
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer, util
from playwright.async_api import async_playwright
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY

class ResearchHelpFunctions:
    SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/search"
    ARXIV_BASE_URL = "http://export.arxiv.org/api/query"
    MAX_WORD_LIMIT = 9000
    ARXIV_VALID_REGEX = re.compile(r"https?://arxiv\.org/abs/\d{4}\.\d{5}(v\d+)?")
    BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"

    def __init__(self):
        self.llm = ChatGroq(
            temperature=0.7,
            api_key=os.getenv("SUB_AGENT"),
            model="llama-3.3-70b-versatile"
        )
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.brave_api_key = os.getenv("BRAVE_SEARCH") 
        self._last_brave_call_time = 0                                                                                                                                                                                    

    def extract_search_queries(self, raw_text: str) -> dict:
        think_end_tag = '</think>'
        if think_end_tag in raw_text:
            raw_text = raw_text.split(think_end_tag, 1)[-1].strip()

        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if not json_match:
            raise ValueError("Could not find a complete JSON object in the response.")

        try:
            data = json.loads(json_match.group())
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        if "organizedSearchQueries" not in data:
            if "searchQueries" in data:
                data = {
                    "topic": data.get("topic", ""),
                    "organizedSearchQueries": {
                        "Introduction": {
                            "question": f"What is the beginning of {data.get('topic', 'football')}?",
                            "queries": data["searchQueries"]
                        }
                    }
                }
            else:
                raise ValueError("JSON missing required keys: 'organizedSearchQueries' or 'searchQueries'")

        return data

    def brave_search(self, query):
        now = time.time()
        elapsed = now - self._last_brave_call_time
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)  # Wait to respect 1 request/sec
        self._last_brave_call_time = time.time()

        url = self.BRAVE_SEARCH_URL
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.brave_api_key
        }
        params = {
            "q": query,
            "count": 5,
        }
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            results = response.json()
            if "web" in results and "results" in results["web"]:
                return [r.get("url") for r in results["web"]["results"] if r.get("url")]
            else:
                print("[Brave Search] No valid 'web.results' in response.")
                return []
        except Exception as e:
            print(f"[Brave Search] Failed: {e}")
            return []



    def search_arvix(self, query: str, max_results: int = 3) -> List[str]:
        try:
            params = {"search_query": f"all:{query}", "start": 0, "max_results": max_results}
            response = requests.get(self.ARXIV_BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            entries = response.text.split("<entry>")
            links = []

            query_keywords = set(re.sub(r"[^a-zA-Z0-9 ]", "", query).lower().split())

            for entry in entries:
                if "<id>" in entry and "<title>" in entry:
                    raw_url = entry.split("<id>")[1].split("</id>")[0].replace("/api/", "/abs/")
                    title = entry.split("<title>")[1].split("</title>")[0].lower()

                    # Check if arXiv URL is valid and title is loosely relevant
                    if self.ARXIV_VALID_REGEX.match(raw_url):
                        title_words = set(re.sub(r"[^a-zA-Z0-9 ]", "", title).split())
                        if len(query_keywords & title_words) > 0:  # simple intersection logic
                            links.append(raw_url)

            return links
        except Exception as e:
            print(f"[arXiv] Failed: {e}")
            return []


    def semantic_search_scholar(self, query: str, max_results: int = 3) -> List[str]:
        try:
            params = {"query": query, "limit": max_results, "fields": "title,url"}
            response = requests.get(self.SEMANTIC_SCHOLAR_API, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return [paper["url"] for paper in data.get("data", []) if "url" in paper]
        except Exception as e:
            print(f"[Semantic Scholar] Failed: {e}")
            return []

    def search_duckduckgo(self, query: str, num_results: int = 3, retries: int = 3, delay_range=(7, 15)) -> List[str]:
        for attempt in range(retries):
            try:
                time.sleep(random.uniform(*delay_range))
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=num_results))
                    return [r['href'] for r in results if 'href' in r]
            except Exception as e:
                print(f"[DuckDuckGo Attempt {attempt + 1}] Failed: {e}")
        return []

    def search_google(self, query: str, num_results: int = 3) -> List[str]:
        try:
            return list(google_search(query, num_results=num_results, lang="en"))
        except Exception as e:
            print(f"[Google Search] Failed: {e}")
            return []

    def robust_search(self, query: str, num_results: int = 3) -> List[str]:
        urls = []
        search_functions = [
            lambda q: self.brave_search(q),
            lambda q: self.search_arvix(q, num_results),
            lambda q: self.semantic_search_scholar(q, num_results),
            lambda q: self.search_duckduckgo(q, num_results),
            lambda q: self.search_google(q, num_results)
        ]
        for fn in search_functions:
            try:
                new_urls = fn(query)
                for url in new_urls:
                    if "arxiv.org/abs/" in url and not self.ARXIV_VALID_REGEX.match(url):
                        print(f"[Malformed Arxiv URL] {url} — retrying with another engine")
                        continue
                    urls.append(url)
                if urls:
                    time.sleep(5)
                    break
            except Exception as e:
                print(f"[{fn.__name__ if hasattr(fn, '__name__') else 'search_function'}] Unexpected failure: {e}")
        return urls

    async def fetch_full_text(self, url: str, timeout: int = 10) -> str:
        if "arxiv.org/abs/" in url and not self.ARXIV_VALID_REGEX.match(url):
            print(f"[Invalid Arxiv URL Skipped] {url}")
            return ""

        headers = {"User-Agent": "Mozilla/5.0", "Accept": "text/html"}
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                return "\n".join(p.get_text() for p in soup.find_all("p") if p.get_text().strip())
        except Exception as e:
            print(f"[Requests] Error: {e}")

        try:
            article = Article(url)
            article.download()
            article.parse()
            return article.text
        except Exception as e:
            print(f"[newspaper3k] Failed: {e}")

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                await page.goto(url)
                content = await page.content()
                soup = BeautifulSoup(content, "html.parser")
                await browser.close()
                return "\n".join(p.get_text() for p in soup.find_all("p") if p.get_text().strip())
        except Exception as e:
            print(f"[Playwright] Failed: {e}")
        return ""

    def truncate_context(self, text: str) -> str:
        words = text.split()
        return " ".join(words[:self.MAX_WORD_LIMIT]) + ("\n\n...[TRUNCATED]" if len(words) > self.MAX_WORD_LIMIT else "")

    def rank_and_select_contexts(self, query: str, docs: List[str]) -> str:
        query_emb = self.embedder.encode(query, convert_to_tensor=True)
        ranked = []
        for doc in docs:
            doc_emb = self.embedder.encode(doc, convert_to_tensor=True)
            score = util.cos_sim(query_emb, doc_emb).item()
            ranked.append((score, doc))
        ranked.sort(reverse=True, key=lambda x: x[0])

        selected, total_words = [], 0
        for _, doc in ranked:
            words = doc.split()
            if total_words + len(words) > self.MAX_WORD_LIMIT:
                break
            selected.append(doc)
            total_words += len(words)

        return "\n\n".join(selected)

    def create_sub_agents(self, name: str) -> RunnableLambda:
        prompt = ChatPromptTemplate.from_template(
            """
            You are {name}, an expert researcher.

            Here is research content:

            {context}

            Write a well-structured content based on this.
            """
        )

        async def sub_agent_fn(query: str) -> dict:
            urls = self.robust_search(query)
            if not urls:
                return {"result": f"{name}: No useful links found for query: {query}", "sources": []}

            contents = []
            sites = []
            for url in urls[:2]:
                try:
                    content = await self.fetch_full_text(url)
                    if content:
                        contents.append(content)
                        sites.append(url)
                    await asyncio.sleep(3)
                except Exception as e:
                    print(f"[Scrape Fail] {url}: {e}")

            if not contents:
                return {"result": f"{name}: No content scraped for: {query}", "sources": sites}

            full_context = self.rank_and_select_contexts(query, contents)
            safe_context = self.truncate_context(full_context)

            try:
                final_prompt = prompt.invoke({"name": name, "context": safe_context})
                response = await self.llm.ainvoke(final_prompt)
                answer = response.content if hasattr(response, "content") else str(response)
            except Exception as e:
                answer = f"{name}: LLM failed to respond due to: {e}"

            return {"result": answer, "sources": sites}

        return RunnableLambda(sub_agent_fn)

    def save_final_report_as_pdf(self, final_report: dict, query: str, output_path: str = None):
        # Generate a timestamp and unique suffix
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_suffix = uuid.uuid4().hex[:6]

        # Safe query for filename
        safe_query = query.replace(" ", "_")

        # Build filename
        filename = f"Generated_research_for_{safe_query}_{timestamp}_{unique_suffix}.pdf"

        # Define output path if not provided
        if output_path is None:
            downloads_folder = os.path.join(os.getcwd(), "downloads")
            os.makedirs(downloads_folder, exist_ok=True)
            doc_path = os.path.join(downloads_folder, filename)
        else:
            doc_path = output_path

        # Setup document
        doc = SimpleDocTemplate(doc_path, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        section_title_style = styles['Heading2']
        subheading_style = styles['Heading3']
        paragraph_style = ParagraphStyle(
            name="Justified", parent=styles["BodyText"],
            fontSize=12, leading=18, alignment=TA_JUSTIFY
        )

        # Begin story
        story = [Paragraph(f"Final Research Report: {query}", title_style), Spacer(1, 0.2 * inch)]

        for section_title, content in final_report.items():
            if section_title == "Sources Section":
                continue

            story.append(Paragraph(section_title, section_title_style))
            story.append(Spacer(1, 0.1 * inch))

            if hasattr(content, 'content'):
                text = content.content
            else:
                text = str(content)

            paragraphs = text.split("\n\n")
            for para in paragraphs:
                story.append(Paragraph(para.strip(), paragraph_style))
                story.append(Spacer(1, 0.15 * inch))

            story.append(Spacer(1, 0.3 * inch))

        # Add sources
        story.append(Paragraph("Sources", section_title_style))
        story.append(Spacer(1, 0.1 * inch))

        sources_list = final_report.get("Sources Section", [])
        section_names = ["Introduction", "Background", "Research Findings", "Application", "Conclusion"]

        # Validate sources_list
        if not isinstance(sources_list, list) or any(not isinstance(s, list) for s in sources_list):
            sources_list = [[] for _ in section_names]

        while len(sources_list) < len(section_names):
            sources_list.append([])

        for section_name, urls in zip(section_names, sources_list):
            story.append(Paragraph(f"{section_name} Sources:", subheading_style))
            if urls:
                for i, url in enumerate(urls, 1):
                    story.append(Paragraph(f"{i}. {url}", paragraph_style))
            else:
                story.append(Paragraph("No sources available.", paragraph_style))
            story.append(Spacer(1, 0.2 * inch))

        # Build PDF
        doc.build(story)
        print(f"PDF saved at: {doc_path}")
        