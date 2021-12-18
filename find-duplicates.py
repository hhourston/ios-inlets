import fnmatch
import logging
import os

import ios_shell.shell as ios


def main():
    ids = {}
    shell_exts = ["bot", "che", "cdt", "ubc", "med", "xbt"]
    to_exclude = ["HISTORY", "old", "Archive", "Bottle", "BOTTLE"]
    print("Files included in", ", ".join(to_exclude), "subdirectories were not compared for duplicates")
    # make a list of all elements in shell_exts followed by their str.upper() versions
    exts = [item for sublist in [[ext, ext.upper()] for ext in shell_exts] for item in sublist]
    for root, dirs, files in os.walk("data"):
        for ext in exts:
            for item in fnmatch.filter(files, f"*.{ext}"):
                file_name = os.path.join(root, item)
                try:
                    shell = ios.ShellFile.fromfile(file_name, process_data=False)
                except Exception as e:
                    logging.exception(f"Failed to read {file_name}: {e}")
                    continue
                id = shell.file.start_time.strftime("%Y/%m/%dT%H:%M:%S") +\
                    shell.administration.mission +\
                    shell.location.station +\
                    str(shell.location.event_number)
                if id in ids:
                    print(file_name, "may be a duplicate of", ids[id])
                ids[id] = file_name
        for exclude in to_exclude:
            if exclude in dirs:
                dirs.remove(exclude)


if __name__ == "__main__":
    main()
