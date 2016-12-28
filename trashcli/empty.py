from .trash import TopTrashDirRules
from .trash import TrashDirs
from .trash import Harvester
from .trash import EX_OK
from .trash import Parser
from .trash import PrintHelp
from .trash import PrintVersion
from .trash import EX_USAGE
from .trash import ParseTrashInfo
from .trash import CleanableTrashcan

class EmptyCmd:
    def __init__(self,
                 out,
                 err,
                 environ,
                 list_volumes,
                 now,
                 file_reader,
                 getuid,
                 file_remover,
                 version):

        self.out          = out
        self.err          = err
        self.file_reader  = file_reader
        top_trashdir_rules = TopTrashDirRules(file_reader)
        self.trashdirs = TrashDirs(environ, getuid,
                                   list_volumes = list_volumes,
                                   top_trashdir_rules = top_trashdir_rules)
        self.version      = version
        self.trashcan     = CleanableTrashcan(file_remover)
        self._now         = now
        self._expiry_date = ExpiryDate(self.file_reader,
                                       self._now,
                                       self.trashcan)

    def run(self, *argv):
        self.exit_code     = EX_OK

        parse = Parser()
        parse.on_help(PrintHelp(self.description, self.println))
        parse.on_version(PrintVersion(self.println, self.version))
        parse.on_argument(self._expiry_date.set_max_age_in_days)
        parse.as_default(self._empty_all_trashdirs)
        parse.on_invalid_option(self.report_invalid_option_usage)

        parse(argv)

        return self.exit_code

    def report_invalid_option_usage(self, program_name, option):
        self.err.write(
            "{program_name}: invalid option -- '{option}'\n".format(**locals()))
        self.exit_code |= EX_USAGE

    def description(self, program_name, printer):
        printer.usage('Usage: %s [days]' % program_name)
        printer.summary('Purge trashed files.')
        printer.options(
           "  --version   show program's version number and exit",
           "  -h, --help  show this help message and exit")
        printer.bug_reporting()
    def _empty_all_trashdirs(self):
        harvester = Harvester(self.file_reader)
        harvester.on_trashinfo_found = self._expiry_date.delete_if_expired
        harvester.on_orphan_found = self.trashcan.delete_orphan
        self.trashdirs.on_trash_dir_found = harvester.analize_trash_directory
        self.trashdirs.list_trashdirs()
    def println(self, line):
        self.out.write(line + '\n')

class DeleteAccordingDate:
    def __init__(self, contents_of, now, max_age_in_days):
        self._contents_of            = contents_of
        self._now                    = now
        self.max_age_in_days         = max_age_in_days
    def delete_if_ok(self, trashinfo_path, trashcan):
        contents = self._contents_of(trashinfo_path)
        ParseTrashInfo(
            on_deletion_date=IfDate(
                OlderThan(self.max_age_in_days, self._now),
                lambda: trashcan.delete_trashinfo_and_backup_copy(trashinfo_path)
            ),
        )(contents)
class DeleteAlways:
    def delete_if_ok(self, trashinfo_path, trashcan):
        trashcan.delete_trashinfo_and_backup_copy(trashinfo_path)

class ExpiryDate:
    def __init__(self, file_reader, now, trashcan):
        self.file_reader = file_reader
        self._now        = now
        self._dustman    = DeleteAlways()
        self.trashcan    = trashcan
    def set_max_age_in_days(self, arg):
        max_age_in_days = int(arg)
        self._dustman = DeleteAccordingDate(self.file_reader.contents_of,
                                                 self._now,
                                                 max_age_in_days)
    def delete_if_expired(self, trashinfo_path):
        self._dustman.delete_if_ok(trashinfo_path, self.trashcan)

class IfDate:
    def __init__(self, date_criteria, then):
        self.date_criteria = date_criteria
        self.then          = then
    def __call__(self, date2):
        if self.date_criteria(date2):
            self.then()
class OlderThan:
    def __init__(self, days_ago, now):
        from datetime import timedelta
        self.limit_date = now() - timedelta(days=days_ago)
    def __call__(self, deletion_date):
        return deletion_date < self.limit_date
