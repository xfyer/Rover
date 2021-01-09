#!/usr/bin/python

# https://opensourceseo.org/find-list-old-urls-domain-using-wayback-cdx-api/
# https://web.archive.org/web/20090420095939/https://twitter.com/realDonaldTrump
# https://web.archive.org/cdx/search/cdx?url=twitter.com/realDonaldTrump
# https://archive.org/web/researcher/cdx_file_format.php

# Format Of Files
# ---------------
# Canonized URL
# Date
# IP
# Original URL
# Mime Type of Original Document
# Response Code
# Old Style Checksum
# New Style Checksum

# 20090420095939
# For Unmodified Pages - https://web.archive.org/web/20090420095939id_/http://twitter.com:80/realDonaldTrump
# May Want Modified Pages For Media

# For Tweet 1346928882595885058
# https://web.archive.org/web/20210106212653/https://video.twimg.com/ext_tw_video/1346928794456776705/pu/vid/1280x720/xJsJiUTRa-ggqL1D.mp4

import os
import pandas as pd

list_folder: str = "archive-me"
files: list = os.listdir(list_folder)

# Remove Non-URL Files
for file in files:
    if ".url" not in file:
        files.remove(file)

if not os.path.exists('working/wayback'):
    os.makedirs('working/wayback')

for file in files:
    download_folder_stripped: str = str(file).rstrip(".url")
    download_folder: str = os.path.join('working/wayback', download_folder_stripped)
    if not os.path.exists(download_folder):
        print(f"Creating: {download_folder}")
        os.makedirs(download_folder)

    print(f"Downloading Archives For {download_folder_stripped}")

    contents: pd.DataFrame = pd.read_csv(filepath_or_buffer=os.path.join(list_folder, file),
                                         header=None,
                                         delimiter=" ",
                                         usecols=[0, 1, 2, 3, 4, 5, 6],
                                         names=["canonized_url",
                                                "date",
                                                "original_url",
                                                "mime_type",
                                                "response_code",
                                                "old_checksum",
                                                "new_checksum"])

    print(contents)
    contents.to_csv(path_or_buf=os.path.join(list_folder, download_folder_stripped + ".csv"))
