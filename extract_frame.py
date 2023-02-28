import argparse
import datetime
import os
import pathlib
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
    episode_number_match = re.search(r"S(\d{1,3})E(\d{1,3})(?:[^\\/]*$)", filename, re.IGNORECASE)
    if episode_number_match:
        episode_number = episode_number_match.group(2)
    else:
        # Based on https://forum.kodi.tv/showthread.php?tid=51614&page=25
        # This regex expression can lead to errors, no fix for the moment
        episode_number_match = re.search(r"(?:(?:\b|_)(?:ep?[ .]?)?(\d{2,3})(-\d{2,3})?(?:[_ ]?v\d)?[\s_.]+)",
                                         filename, re.IGNORECASE)
        if episode_number_match:
            episode_number = episode_number_match.group(1)
        else:
            return 'NA'
    return int(episode_number)


# Return only episodes files wanted
def get_episode_file(episodes, files):
    missing_episodes = set(episodes) - set(get_episode_number(os.path.basename(f)) for f in files)
    if missing_episodes:
        missing_episodes = [str(ep) for ep in missing_episodes]
        print(f"Episodes {', '.join(missing_episodes)} not found in the list of files.")
    return [f for f in files if get_episode_number(os.path.basename(f)) in episodes]


def get_all_episodes(files):
    episodes = set(get_episode_number(os.path.basename(f)) for f in files if get_episode_number(os.path.basename(f)) != "NA")
    return [f for f in files if get_episode_number(os.path.basename(f)) in episodes]


# Return timecode in seconds
def get_timecode_in_secs(duration, timecode=None):
    if timecode is None:
        timecode = round(random.uniform(0, duration), 2)
    else:
        timecode = cvsecs(timecode)
        if timecode >= duration:
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


# Return a list of files with specify file_type
def get_files_source(filepath, file_type):
    files = []
    # Get a list of all files in the folder with the specified file type
    if os.path.isdir(filepath):
        files = [str(file) for file in list(pathlib.Path(filepath).rglob(f"*.{file_type}"))]
    elif os.path.isfile(filepath) and filepath.endswith(file_type):
        files.append(filepath)

    return files


def extract_frame(filepath, timecode, output_dir, file_type="png"):
    filename, file_extension = os.path.splitext(os.path.basename(filepath))
    episode_number = get_episode_number(filename)

    if episode_number == 'NA':
        print(f"Error: Can't find episode number in the file name: {filename}")
        return

    td = datetime.timedelta(seconds=timecode)
    human_timecode = td.__str__().replace(':', '_')

    path_name = f"{human_timecode}-{filename}-{episode_number}.{file_type}"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_path = os.path.join(output_dir, path_name)

    (
        ffmpeg
        .input(filepath, ss=timecode)
        .output(output_path, vframes=1)
        .overwrite_output()
        .run_async(pipe_stdin=True, quiet=True)
    )

    print(f"Frame extracted (Timecode: {td}) and saved to '{output_path}'")


def main():
    parser = argparse.ArgumentParser(
        description='Extracts images from TV shows and uploads them to slow.pics.(In the future)')
    parser.add_argument('source', type=str,
                        help='The path of the folder/file containing the TV show files')
    parser.add_argument('-c', '--comparisons_source', type=str, nargs='+', default=list(),
                        help='The path of the folder/file containing the TV show files you want to compare')
    parser.add_argument('-t', '--file_type', default='mkv', type=str,
                        help='The file type of the TV show files (e.g. mp4, avi, default: mkv)')
    parser.add_argument('-e', '--episodes', nargs='*', default=None, type=int,
                        help='A list of episode numbers to extract images from (e.g. 1 2 3) (Default: All)')
    parser.add_argument('--num_frames', default=1, type=int,
                        help='The number of frames to extract from the same TV show')
    args = parser.parse_args()

    source = args.source
    comparisons = args.comparisons_source
    num_frames = args.num_frames
    file_type = args.file_type
    episodes = args.episodes

    if not os.path.exists(source):
        print(f"Error: The folder/file path '{source}' does not exist.")
        return
    for comparison in comparisons:
        if not os.path.exists(comparison):
            print(f"Error: The folder/file path '{comparison}' does not exist.")
            return
        if comparison == source:
            print("The path of source cannot be the same as that of comparison !")
            return

    # Get a list of all files in the folder with the specified file type
    source_path = get_files_source(source, file_type)
    comparison_paths = [get_files_source(comparison, file_type) for comparison in comparisons]

    if episodes:
        # Filter the list of files to only include the specified episode
        source_files = get_episode_file(episodes, source_path)
        comparison_files = [get_episode_file(episodes, comparison) for comparison in comparison_paths]

    else:
        # Get all episodes TODO: Need to improve that to take in account the movies
        source_files = get_all_episodes(source_path)
        comparison_files = [get_all_episodes(comparison) for comparison in comparison_paths]

    for i, comparison_file in enumerate(comparison_files):
        if len(source_files) != len(comparison_file):
            print(f"Error: The source({len(source_files)}) and comparison {i}({len(comparison_file)}) do not contain the same number of files ! Use the --episodes instead of !?")
            return

    for i, source_file in enumerate(source_files):
        for f in range(num_frames):

            output_dir = os.path.abspath("./")
            duration_src, fps_src = extract_show_info(source_file)
            timecode = get_timecode_in_secs(duration_src)

            extract_frame(source_file, timecode, output_dir)

            # Compare source frame with comparison files
            for files in comparison_files:
                # Not necessary ?!
                # duration_cf, fps_cf = extract_show_info(files[i])
                # if duration_cf != duration_src or fps_cf != fps_src:
                #     print(f"[WARNING] '{os.path.basename(source_file)}' and '{os.path.basename(files[i])}' do not have the same duration and/or fps !")

                extract_frame(files[i], timecode, output_dir)
            print()

    print("Finished extracting images.")


if __name__ == '__main__':
    main()

    # file_1 = "S:\\downloads\\torrents\\others\\Hundred.S01.SUBFRENCH.1080p.WEB.x264-UwU\\Hundred.S01E08.SUBFRENCH.1080p.WEB.x264-UwU\\Hundred.S01E08.SUBFRENCH.1080p.WEB.x264-UwU.mkv"
    # file_2 = "S:\\downloads\\torrents\\others\\Hundred_(2016)_(BD_1080p_Hi10_FLAC)_[Dual-Audio]_[Rasetsu]\\[RASETSU]_Hundred_-_08_(BD_1080p_Hi10_FLACx2)_[C102A58D].mkv"
    #
    # frame_to_analyse = 1432
    # result = list()
    #
    # probe = ffmpeg.probe(file_1)
    #
    # video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    # width = int(video_info['width'])
    # height = int(video_info['height'])
    # num_frames = int(eval(video_info['r_frame_rate']))
    #
    # for file in [file_1, file_2]:
    #     out, _ = (
    #         ffmpeg
    #         .input(file_1)
    #         .filter('select', 'gte(n,{})'.format(frame_to_analyse))
    #         .output('pipe:', format='rawvideo', pix_fmt='rgb24', vframes=1)
    #         .run(capture_stdout=True, capture_stderr=True)
    #     )
    #     result.append(np.frombuffer(out, np.uint8).reshape([height, width, 3]))
    #
    # if np.array_equal(result[0], result[1]):
    #     print("The two frames are equals !")
    # else:
    #     print("The two frames are not equals !")
    #
    # # Extract Frame to see the diff or not
    # for i, file in enumerate([file_1, file_2]):
    #     # A utiliser ?!!
    #     (
    #         ffmpeg
    #         .input(file_1)
    #         .filter('select', 'gte(n,{})'.format(frame_to_analyse))
    #         .output(f'frame_gte_{i}.png', vframes=1)
    #         .overwrite_output()
    #         .run(quiet=True)
    #     )
    #
    #     # Moins précis à cause de la convertion ??!!
    #     (
    #         ffmpeg
    #         .input(file_1, ss=round(frame_to_analyse / num_frames, 2))
    #         .output(f'frame_ss_{i}.png', vframes=1)
    #         .overwrite_output()
    #         .run(quiet=True)
    #     )
