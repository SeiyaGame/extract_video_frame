import argparse
import datetime
import os
import random
import re

# https://github.com/kkroening/ffmpeg-python/tree/master/examples
import ffmpeg


def cvsecs(time):
    """ Will convert any time into seconds.

    If the type of `time` is not valid,
    it's returned as is.

    Here are the accepted formats::

    >>> cvsecs(15.4)   # seconds
    15.4
    >>> cvsecs((1, 21.5))   # (min,sec)
    81.5
    >>> cvsecs((1, 1, 2))   # (hr, min, sec)
    3662
    >>> cvsecs('01:01:33.045')
    3693.045
    >>> cvsecs('01:01:33,5')    # coma works too
    3693.5
    >>> cvsecs('1:33,5')    # only minutes and secs
    99.5
    >>> cvsecs('33.5')      # only secs
    33.5
    """
    factors = (1, 60, 3600)

    if isinstance(time, str):
        time = [float(f.replace(',', '.')) for f in time.split(':')]

    if not isinstance(time, (tuple, list)):
        return time

    return sum(mult * part for mult, part in zip(factors, reversed(time)))


def get_episode_number(filename):
    # https://regex101.com/r/AEUCmV/1 and https://forum.kodi.tv/showthread.php?tid=51614&page=25
    episode_number_match = re.search(r"(?:(?:\b|_)(?:ep?[ .]?)?(\d{2,3})(-\d{2,3})?(?:[_ ]?v\d)?[\s_.-]+)", filename,
                                     re.IGNORECASE)
    if episode_number_match:
        episode_number = episode_number_match.group(1)
    else:
        episode_number_match = re.search(r"S(\d{1,3})E(\d{1,3})(?:[^\\/]*$)", filename, re.IGNORECASE)
        if episode_number_match:
            episode_number = episode_number_match.group(2)
        else:
            return 'NA'
    return int(episode_number)


def extract_frame(filepath, timecode=None, type='png'):
    filename, file_extension = os.path.splitext(os.path.basename(filepath))
    episode_number = get_episode_number(filename)

    if episode_number == 'NA':
        print(f"Error: Can't find episode number in the file name: {filename}")
        return

    probe = ffmpeg.probe(filepath)
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    probe_format = probe['format']

    duration = cvsecs(probe_format['duration'])
    fps = eval(video_stream['r_frame_rate'])

    if timecode is None:
        timecode = round(random.uniform(0, duration), 2)
    else:
        if "t=" in timecode:
            timecode = timecode[2:]
            timecode = cvsecs(timecode)
        elif "f=" in timecode:
            timecode = int(timecode[2:])
            timecode = round(timecode / fps, 2)
        else:
            print(f"Error: Invalid timecode format. Please use 't=' for duration or 'f=' for frame number.")
            return

        if timecode <= duration:
            timecode = cvsecs(timecode)
        else:
            print(f"Error: The timecode is not valid: {timecode}")
            return

    # Pas tres propre mais fonctionne :D
    td = datetime.timedelta(seconds=timecode)
    human_timecode = td.__str__().replace(':', '_')
    print(f"The timecode is: {td}")

    output_path = f"{human_timecode}-{filename}-{episode_number}.{type}"

    (
        ffmpeg
        .input(filepath, ss=timecode)
        .output(output_path, vframes=1)
        .overwrite_output()
        .run_async(pipe_stdin=True, quiet=True)
    )

    print("Frame extracted and saved to", output_path)


def main():
    parser = argparse.ArgumentParser(description='Extracts images from TV shows and uploads them to slow.pics.')
    parser.add_argument('folder_path', help='The path of the folder containing the TV show files')
    parser.add_argument('-t', '--file_type', default='mkv', type=str,
                        help='The file type of the TV show files (e.g. mp4, avi, default: mkv)')
    parser.add_argument('-n', '--num_shows', default=1, type=int, help='The number of TV shows')
    parser.add_argument('-f', '--num_frames', default=1, type=int,
                        help='The number of frames to extract from the same TV show')
    parser.add_argument('-e', '--episodes', nargs='+', type=int,
                        help='A list of episode numbers to extract images from (e.g. 1 2 3)')
    parser.add_argument('-tc', '--timecode', type=str,
                        help='The timecode of the frame to be extracted (e.g. t=00:23:15.15 for a duration or f=1150 for a frame)')
    args = parser.parse_args()

    folder_path = args.folder_path
    file_type = args.file_type
    num_shows = args.num_shows
    num_frames = args.num_frames
    episodes = args.episodes
    timecode = args.timecode

    if not os.path.exists(folder_path):
        print(f"Error: The folder path '{folder_path}' does not exist.")
        return

    # Get a list of all files in the folder with the specified file type
    files = [f for f in os.listdir(folder_path) if f.endswith(file_type)]

    if len(files) == 0:
        print(f"Error: No files with the type '{file_type}' found in the folder '{folder_path}'.")
        return

    if num_shows > len(files):
        print(
            f"Error: The number of TV shows is greater than the number of available files. Maximum number of files: {len(files)}")
        return

    if episodes:

        # Filter the list of files to only include the specified episode
        files = [f for f in files if get_episode_number(f) in episodes]
        num_shows = len(episodes)

        if len(files) == 0:
            print(f"Error: No files found for episodes: {episodes}")
            return

    for i in range(num_shows):
        # Choose a random file from the list
        chosen_file = random.choice(files)
        filepath = os.path.join(folder_path, chosen_file)

        for j in range(num_frames):
            # Call the extract_frame function on the chosen file
            extract_frame(filepath, timecode)

        # Remove the chosen file from the list to avoid choosing it again
        files.remove(chosen_file)


if __name__ == '__main__':
    main()
