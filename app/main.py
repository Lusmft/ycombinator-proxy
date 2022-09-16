"""Тестовое задание для CodeReview."""
import os
import re

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI()


@app.get('/', response_class=HTMLResponse)
async def index(request: Request) -> str:
    """Return main page."""
    return await proxy_page(request, '')


@app.get('/{address}', response_class=HTMLResponse)
async def proxy_page(request: Request, address: str) -> str:
    """Proxy for Hacker News site."""
    params = request._query_params
    request_params = {}
    for param in params:
        request_params[param] = params[param]
    url = os.getenv('SITE_URL', 'https://news.ycombinator.com/')
    page = requests.get(f'{url}{address}', params=request_params)
    if page.status_code == 403:
        return RedirectResponse(page.url)
    soup = BeautifulSoup(page.text, 'html.parser')
    soup = await change_headers(soup, url)
    soup = await change_urls(soup, url)
    return await change_comments(str(soup))


async def change_headers(soup: BeautifulSoup, url: str) -> BeautifulSoup:
    """Return page with changed headers."""
    a_urls = soup.find_all('a', text=True)
    for a_url in a_urls:
        a_url.string = ' '.join(
            [
                i + '™' if len(i) == 6 and i.isalnum() else i
                for i in a_url.text.split(' ')
            ],
        )
    tds = soup.find_all(('td', 'span'), text=True, href=False)
    for td in tds:
        if not td.a:
            td.string = ' '.join(
                [
                    i + '™' if len(i) == 6 and i.isalnum() else i
                    for i in td.text.split(' ')
                ],
            )
    return soup


async def change_urls(soup: BeautifulSoup, url: str) -> BeautifulSoup:
    """Return page with changed urls."""
    hrefs = soup.find_all(True, href=True)
    for href in hrefs:
        if href['href'].startswith(url):
            href['href'] = href['href'].split(url)[1]
        elif 'css' in href['href']:
            href['href'] = url + href['href']
    srcs = soup.find_all(True, src=True)
    for src in srcs:
        if not src['src'].startswith(('http', 'item', '#')):
            src['src'] = url + src['src']
        elif src['src'].startswith(url):
            src['src'] = src['src'].split(url)[1]
    return soup


async def change_comments(html_page: str) -> str:
    """Return page with adding ™ symbol to the words with length 6."""
    comments = re.findall(r'<span class="commtext c00">.+</span>', html_page)
    for comment in comments:
        html_page = html_page.replace(
            comment,
            ' '.join(
                [
                    i + '™' if len(i) == 6 and i.isalnum() else i
                    for i in comment.split(' ')
                ],
            ),
        )
    return html_page
