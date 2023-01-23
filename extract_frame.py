import argparse
import datetime
import os
import random
import re

# https://github.com/kkroening/ffmpeg-python/tree/master/examples
import ffmpeg


# Convert all timecode formats to seconds
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
    episode_number_match = re.search(r"(?:(?:\b|_)(?:ep?[ .]?)?(\d{2,3})(-\d{2,3})?(?:[_ ]?v\d)?[\s_.]+)", filename,
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


# Return only episodes files wanted
def get_episode_file(episodes, files):
    missing_episodes = set(episodes) - set(get_episode_number(f) for f in files)
    if missing_episodes:
        missing_episodes = [str(ep) for ep in missing_episodes]
        print(f"Episodes {', '.join(missing_episodes)} not found in the list of files.")
    return [f for f in files if get_episode_number(f) in episodes]


def get_all_episodes(files):
    episodes = set(get_episode_number(f) for f in files if get_episode_number(f) != "NA")
    return [f for f in files if get_episode_number(f) in episodes]


# Return timecode in seconds
def get_timecode_secs(duration, fps, timecode=None):
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
            exit(0)

        if timecode <= duration:
            timecode = cvsecs(timecode)
        else:
            print(f"Error: The timecode is not valid: {timecode}")
            exit(0)

    return timecode


# Return duration and FPS of shows
def extract_show_info(filepath):
    probe = ffmpeg.probe(filepath)
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    probe_format = probe['format']

    duration = cvsecs(probe_format['duration'])
    fps = eval(video_stream['r_frame_rate'])

    return duration, fps


# Return a list of files
def get_files_source(filepath, file_type):
    files = []

    # Get a list of all files in the folder with the specified file type
    if os.path.isdir(filepath):
        files = [f for f in os.listdir(filepath) if f.endswith(file_type)]
    elif os.path.isfile(filepath) and filepath.endswith(file_type):
        files.append(filepath)

    return files


def extract_frame(filepath, timecode, output_dir, file_type="png"):
    filename, file_extension = os.path.splitext(os.path.basename(filepath))
    episode_number = get_episode_number(filename)

    if episode_number == 'NA':
        print(f"Error: Can't find episode number in the file name: {filename}")
        return

    # Pas trs propre mais fonctionne :D
    td = datetime.timedelta(seconds=timecode)
    human_timecode = td.__str__().replace(':', '_')
    print(f"The timecode is: {td}")

    path_name = f"{human_timecode}-{filename}-{episode_number}.{file_type}"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_path = os.path.join(output_dir, path_name)

    (
        ffmpeg
        .input(filepath, ss=timecode)
        .output(output_path, vframes=1)
        .overwrite_output()
        # .run_async(pipe_stdin=True, quiet=True)
        .run(quiet=True)
    )

    print("Frame extracted and saved to", output_path)


def main():
    parser = argparse.ArgumentParser(
        description='Extracts images from TV shows and uploads them to slow.pics.(In the future)')
    parser.add_argument('sourceA', type=str,
                        help='The path of the folder/file containing the TV show files of the first source')
    parser.add_argument('sourceB', type=str,
                        help='The path of the folder/file containing the TV show files of the second source')
    parser.add_argument('-t', '--file_type', default='mkv', type=str,
                        help='The file type of the TV show files (e.g. mp4, avi, default: mkv)')
    parser.add_argument('-e', '--episodes', nargs='+', default=None, type=int,
                        help='A list of episode numbers to extract images from (e.g. 1 2 3) (Default: All)')
    args = parser.parse_args()

    sourceA, sourceB = args.sourceA, args.sourceB

    file_type = args.file_type
    episodes = args.episodes

    for source in [sourceA, sourceB]:
        if not os.path.exists(source):
            print(f"Error: The folder/file path '{source}' does not exist.")
            return

    if sourceA == sourceB:
        print("The path of source A cannot be the same as that of source B !")
        return

    # Get a list of all files in the folder with the specified file type
    sourceA_files, sourceB_files = get_files_source(sourceA, file_type), get_files_source(sourceB, file_type)

    if episodes:
        # Filter the list of files to only include the specified episode
        sourceA_files, sourceB_files = get_episode_file(episodes, sourceA_files), get_episode_file(episodes,
                                                                                                   sourceB_files)
    else:
        sourceA_files, sourceB_files = get_all_episodes(sourceA_files), get_all_episodes(sourceB_files)

    # print(f"sourceA_files: {len(sourceA_files)}")
    # print(f"sourceB_files: {len(sourceB_files)}")
    if len(sourceA_files) != len(sourceB_files):
        print(f"Error: source A({len(sourceA_files)}) and source B({len(sourceB_files)}) do not contain the same number of files ! Use the --episodes")
        return

    for i, j in zip(sourceA_files, sourceB_files):

        filepath_sourceA, filepath_sourceB = os.path.join(sourceA, i), os.path.join(sourceB, j)

        duration_sourceA, fps_sourceA = extract_show_info(filepath_sourceA)
        duration_sourceB, fps_sourceB = extract_show_info(filepath_sourceB)

        if duration_sourceA != duration_sourceB or fps_sourceA != fps_sourceB:
            print(f"WARNING: {i} and {j} do not have the same duration and fps !")
            # print(f"duration_sourceA: {duration_sourceA}, duration_sourceB: {duration_sourceB}")
            # print(f"fps_sourceA: {fps_sourceA}, fps_sourceB: {fps_sourceB}")

        timecode = get_timecode_secs(duration_sourceA, fps_sourceA)

        output_dirA, output_dirB = "sourceA", "sourceB"
        if len(sourceA_files) == 1 and len(sourceB_files) == 1:
            output_dirA, output_dirB = os.path.abspath("./"), os.path.abspath("./")

        # Call the extract_frame function on the chosen file
        extract_frame(filepath_sourceA, timecode, output_dirA)
        extract_frame(filepath_sourceB, timecode, output_dirB)

    print("Finished extracting images.")


if __name__ == '__main__':
    main()