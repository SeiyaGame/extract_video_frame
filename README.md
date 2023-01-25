# Image Extraction Script
This script allows you to extract images from TV shows and upload them to slow.pics (In the future)

## Requirements
- Python 3
- ffmpeg-python
- ffmpeg

### Installing ffmpeg-python
The latest version of ffmpeg-python can be acquired via a typical pip install:
```
pip install ffmpeg-python
```

### Installing ffmpeg

There are a variety of ways to install FFmpeg, such as the [official download links](https://ffmpeg.org/download.html), or using your package manager of choice (e.g. `apt install ffmpeg` on Debian/Ubuntu, `brew install ffmpeg` on OS X, etc.).
Otherwise you can put the binaries in the root of the project


## Usage
The script can be run from the command line with the following arguments:

```
usage: extract_frame.py [-h] [-c COMPARISONS_SOURCE [COMPARISONS_SOURCE ...]] [-t FILE_TYPE] [-e EPISODES [EPISODES ...]] [--num_frames NUM_FRAMES] source

Extracts images from TV shows and uploads them to slow.pics.(In the future)

positional arguments:
  source                The path of the folder/file containing the TV show files

options:
  -h, --help            show this help message and exit
  -c COMPARISONS_SOURCE [COMPARISONS_SOURCE ...], --comparisons_source COMPARISONS_SOURCE [COMPARISONS_SOURCE ...]
                        The path of the folder/file containing the TV show files you want to compare
  -t FILE_TYPE, --file_type FILE_TYPE
                        The file type of the TV show files (e.g. mp4, avi, default: mkv)
  -e EPISODES [EPISODES ...], --episodes EPISODES [EPISODES ...]
                        A list of episode numbers to extract images from (e.g. 1 2 3) (Default: All)
  --num_frames NUM_FRAMES
                        The number of frames to extract from the same TV show
```

- The `source` argument is required and should be the path of the folder/files containing the TV show files of the first source.
- The `comparisons_source` argument is optional and should be the path of the folder/files containing the TV show files you want to compare. 
- The `file_type` argument is optional and defaults to 'mkv'.
- The `episodes` argument is optional and defaults to None.
- The `num_frames` argument is optional and defaults to 1.

For example, to extract 1 image from a random episode of a TV show in the 'folder_path' folder with the file type 'mkv', you would run the following command:
```
python extract_frame.py folder_path
```

To extract 1 images from episode 5,6,7,9 of a TV show with the file type 'mkv' and with one comparison, you would run the following command:
```
python extract_frame.py folder_path -c folder_comparison -e 5 6 7 9
```

To extract 3 images from episode 5,6,7,9 of a TV show with the file type 'mkv' and with one comparison, you would run the following command:
```
python extract_frame.py folder_path -c folder_comparison -e 5 6 7 9 --num_frames 3
```

# Output
The script will extract the specified number of images from the TV show and save them in the same folder as the script with the format `{human_timecode}_{filename}-{episode_number}.{type}.png`. 
The timecode of the extracted image is selected randomly for the moment.

# Note
The script assumes that the TV show files have their episode number in the file name. If it can't find the episode number in the file name, it will return an error message and exit.