import os
import copy
import time
import gc
import queue
import requests
import threading
import hashlib
import cv2
import base64
import subprocess
import matplotlib
import matplotlib.pyplot as plt
import multiprocessing
import logging
import numpy as np
from collections import deque
from urllib.parse import unquote

import config
import properties
# matplotlib.use('agg')


def download(url, save_folder, info=True):
    """
    Downloads a file from the given URL and saves it to the specified folder.

    Parameters:
        url (str): The URL of the file to be downloaded.
        save_folder (str): The folder where the downloaded file will be saved.
        info (bool, optional): Whether to print information about the download progress. 
            Defaults to True.

    Returns:
        str: The file path of the downloaded file.
    """
    if info: print("Downloading file:", url)
    r = requests.get(url)
    file_name = get_download_file_name(url, r.headers)
    file_path = os.path.join(save_folder, file_name)
    file = open(file_path, "wb")
    file.write(r.content)
    file.close()
    if info: print("Finished download:", str(file_path))
    return file_path


def get_download_file_name(url, headers):
    """
    Get the download file name from the given URL and headers.

    Parameters:
        url (str): The URL of the file to be downloaded.
        headers (dict): The headers of the HTTP response.

    Returns:
        str: The download file name extracted from the URL and headers, or the current timestamp if no file name is found.
    """
    filename = ''
    if 'Content-Disposition' in headers and headers['Content-Disposition']:
        disposition_split = headers['Content-Disposition'].split(';')
        if len(disposition_split) > 1:
            if disposition_split[1].strip().lower().startswith('filename='):
                file_name = disposition_split[1].split('=')
                if len(file_name) > 1:
                    filename = unquote(file_name[1]).replace("\"", "").replace("\'", "")
    if not filename and os.path.basename(url):
        filename = os.path.basename(url).split("?")[0]
    if not filename:
        return time.time()
    return filename


def post(url, data, info=True, logger=None):
        """
        This function is responsible for making a POST request to the specified URL in a new thread.

        Parameters:
            url (str): The URL to which the POST request should be made.
            data (dict): The data to be sent in the POST request.
            info (bool, optional): Whether or not to print the response and its text. Defaults to True.
        """
        # 开新线程进行post
        def post_func(url, data, info=True, logger=None):
            r = requests.post(url, json=data, headers={'content-type':'application/json'})
            if info:
                if logger is not None:
                    if isinstance(logger, str):
                        logger = logging.getLogger(logger)
                    logger.info(f'{r} {r.text}')
                else:
                    print(f'{r} {r.text}')
        post_thread = threading.Thread(target=post_func, args=(url, data, info, logger))
        post_thread.start()


def post_file(url, file_path, data=None, info=True):
    """
    Post a file to a specified URL.

    Parameters:
        url (str): The URL to post the file to.
        file_path (str): The path to the file to be posted.
        data (Optional[Dict[str, Any]]): Additional data to be included in the post request. Default is None.
        info (bool): Flag indicating whether to print additional information about the post request. Default is True.

    Returns:
        None
    """
    # 开新线程进行post
    def post_func(url, data, files, info=True):
        print("Uploading:", str(files["file"]))
        r = requests.post(url, data=data, files=files)
        print("Finished upload")
        if info:
            print(r)
            print(r.text)

    files = {"file": open(file_path, "rb")}

    post_thread = threading.Thread(target=post_func, args=(url, data, files, info))
    post_thread.start()


def generate_md5_checksum(input_string):
    """
    Generates an MD5 checksum string from a given input string.

    Args:
        input_string (str): The input string to generate the MD5 checksum for.

    Returns:
        str: The MD5 checksum string.
    """
    md5_hash = hashlib.md5()
    md5_hash.update(input_string.encode('utf-8'))
    checksum = md5_hash.hexdigest()
    return checksum

