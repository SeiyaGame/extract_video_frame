# Image Extraction Script
This script allows you to extract images from TV shows and upload them to slow.pics (In the future)

## Requirements
- Python 3
- moviepy library
## Usage
The script can be run from the command line with the following arguments:

```
usage: main.py [-h] [-t FILE_TYPE] [-n NUM_SHOWS] [-f NUM_FRAMES] [-e EPISODE]
               folder_path

Extracts images from TV shows and uploads them to slow.pics.

positional arguments:
  folder_path           The path of the folder containing the TV show files

optional arguments:
  -h, --help            show this help message and exit
  -t FILE_TYPE, --file_type FILE_TYPE
                        The file type of the TV show files (e.g. mp4, avi, default: mkv)
  -n NUM_SHOWS, --num_shows NUM_SHOWS
                        The number of TV shows to extract images from
  -f NUM_FRAMES, --num_frames NUM_FRAMES
                        The number of frames to extract from the same TV show
  -e EPISODE, --episode EPISODE
                        The episode number to extract images from
```

- The `folder_path` argument is required and should be the path of the folder containing the TV show files. 
- The `file_type` argument is optional and defaults to 'mkv'. 
- The `num_shows` argument is optional and defaults to 1. 
- The `num_frames` argument is optional and defaults to 1. 
- The `episode` argument is optional and defaults to None.

For example, to extract 1 image from a random episode of a TV show in the 'TV_shows' folder with the file type 'mkv', you would run the following command:
```
python main.py TV_shows
```

To extract 2 images from a random episode of a TV show in the 'TV_shows' folder with the file type 'avi', you would run the following command:
```
python main.py TV_shows -t avi -n 2
```

To extract 2 images from episode 5 of a TV show in the 'TV_shows' folder with the file type 'mkv', you would run the following command:
```
python main.py TV_shows -e 5 -n 2
```

# Output
The script will extract the specified number of images from the TV show and save them in the same folder as the script with the format `{human_timecode}_{filename}-{human_timecode}-{episode_number}.jpg`. 
The timecode of the extracted image is selected randomly if not specified.

# Note
The script assumes that the TV show files have their episode number in the file name. If it can't find the episode number in the file name, it will return an error message and exit.