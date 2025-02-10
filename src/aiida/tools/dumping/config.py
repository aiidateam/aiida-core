from dataclasses import dataclass


@dataclass
class ProfileDumpConfig:
    dump_processes: bool = True
    symlink_duplicates: bool = True  #
    delete_missing: bool = False  # profile
    extra_calc_dirs: bool = False  # collection
    organize_by_groups: bool = True  # profile

