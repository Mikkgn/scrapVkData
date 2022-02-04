import os
import re
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from http import HTTPStatus
from pathlib import Path
from typing import IO, Generator

import requests
import typer
from bs4 import BeautifulSoup
from tenacity import TryAgain, retry, stop_after_attempt

HTML_FILES_PATTERN = '**/*.html'
OUT_DIR = 'out'
IN_DIR = 'messages'
DIV_ATTACHMENT_CLASS = 'attachment__description'
LINK_ATTACHMENT_CLASS = 'attachment__link'


@contextmanager
def open_html(path: Path) -> Generator[IO, None, None]:
    with open(path, 'rb') as file:
        yield file.read()


def get_html_files_path(directory_path: str) -> Generator[Path, None, None]:
    for path in Path(directory_path).glob(HTML_FILES_PATTERN):
        yield path


def get_image_links(html_data: IO) -> Generator[str, None, None]:
    soup = BeautifulSoup(html_data, 'html.parser')
    divs_with_attachment = soup.find_all('div', class_=DIV_ATTACHMENT_CLASS)
    for div in divs_with_attachment:
        if div.get_text() != 'Photo':
            continue
        image_link = div.find_next_sibling('a', class_=LINK_ATTACHMENT_CLASS).get_text()
        yield image_link


def return_none(*args, **kwargs) -> None:
    return None


@retry(stop=stop_after_attempt(3), reraise=False, retry_error_callback=return_none)
def save_image(link: str, path_to_save: str) -> None:
    try:
        r = requests.get(link, stream=True)
    except Exception as exc:
        typer.echo(f'Exception {exc} on link {link}', err=True)
        raise exc
    else:
        if r.status_code == HTTPStatus.OK:
            typer.echo(f'Saving {path_to_save}')
            with open(path_to_save, 'wb') as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
        else:
            raise TryAgain


def get_links_from_messages(html_file_path: Path) -> Generator[str, None, None]:
    with open_html(html_file_path) as data:
        yield from get_image_links(data)


def get_conversation_id_and_link(
    messages_dir: str,
) -> Generator[tuple[str, str], None, None]:
    for html_file_path in get_html_files_path(messages_dir):
        if 'index-messages.html' in html_file_path.parts:
            continue
        conversation_id = html_file_path.parts[-2]
        for link in get_links_from_messages(html_file_path):
            yield conversation_id, link


def get_dir_name(name_by_conv: dict[str, str], conversation_id: str) -> str:
    name = name_by_conv[conversation_id]
    return f'{name}-{conversation_id}'


def process_messages(
    messages_dir: str = typer.Argument(
        ..., help='Path to your messages directory in data copy'
    ),
    out_dir: str = typer.Argument(OUT_DIR, help='Path to save out data'),
    threads: int = typer.Option(4, help="Number of parallel threads to save data")
) -> None:
    start_time = time.monotonic()
    name_by_conv = get_name_by_conversation_map(messages_dir)
    prev_conversation_id = None
    index = 0

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = []
        for conversation_id, link in get_conversation_id_and_link(messages_dir):
            if conversation_id != prev_conversation_id:
                prev_conversation_id = conversation_id
                index = 0

            dir_name = get_dir_name(name_by_conv, conversation_id)

            if not os.path.exists(f'{out_dir}/{dir_name}'):
                os.mkdir(f'{out_dir}/{dir_name}')

            future = executor.submit(
                save_image,
                link=link,
                path_to_save=f'{out_dir}/{dir_name}/{index}.jpg',
            )
            futures.append(future)
            index += 1

        for _ in as_completed(futures):
            pass

    typer.echo(f'Elapsed {time.monotonic() - start_time} sec')


def get_name_by_conversation_map(messages_dir: str) -> dict:
    pattern = re.compile(r'[-+]?[\d]+/messages.*')
    mapping = {}
    uniq_names = set()
    with open_html(Path(f'{messages_dir}/index-messages.html')) as data:
        soup = BeautifulSoup(data, 'html.parser')
        for link in soup.find_all('a', href=True):
            if not pattern.match(link['href']):
                continue
            conversation_id = link['href'].split('/')[0]
            conv_name = link.get_text()
            if conv_name in uniq_names:
                conv_name = f'{conv_name}-{str(uuid.uuid4())[:4]}'

            mapping[conversation_id] = conv_name
            uniq_names.add(conv_name)

    return mapping


typer.run(process_messages)
