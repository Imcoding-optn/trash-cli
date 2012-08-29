import os, sys

def main(argv):
    from trashcli.trash import FileSystemReader, TrashDirs, Harvester
    environ     = os.environ
    getuid      = os.getuid
    file_reader = FileSystemReader()
    trashdirs   = TrashDirs(environ, getuid, fs     = file_reader)
    harvester   = Harvester(trashdirs, file_reader)
    print 'ciao'
    import sys
    sys.stderr.write('xxxxxx')
    pass
    return 8


class TrashRmCmd:

    def __init__(self, trash_contents, trashcan):
        self.trash_contents = trash_contents
        self.delete = TrashCanCleaner(trashcan)

    def clean_up_matching(self, pattern):
        self.filter = Pattern(pattern, self.delete)
        self.trash_contents.list_files_to(self.filter)

import fnmatch
class Pattern:
    def __init__(self, pattern, delete):
        self.delete = delete
        self.pattern = pattern
    def garbage(self, original_path, info):
        basename = os.path.basename(original_path)
        if fnmatch.fnmatchcase(basename, self.pattern):
            self.delete.garbage(original_path, info)

class TrashCanCleaner:
    def __init__(self, trashcan):
        self.trashcan = trashcan
    def garbage(self, original_path, info_file, backup_copy=None):
        self.trashcan.release(info_file)

if __name__ == '__main__':
    sys.exit(main(sys.argv))