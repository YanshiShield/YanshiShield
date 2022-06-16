#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Automatically Monitor and clear the storage of the specified dir.

   Typical usage example:

   monitor_path = '/monitor/path'
   filter = lambda name: name.startswith('train')
   quota = 1024  # MB
   manager = StorageManager(monitor_path, filter, quota)
   manager.start()
   manager.assert_storage_sufficient()
   manager.stop()
"""

import collections
import os
from os.path import basename, join, getmtime, exists, isfile, getsize
import shutil

from absl import logging as log
from watchdog.events import FileSystemEventHandler, EVENT_TYPE_MOVED, \
    EVENT_TYPE_CREATED, EVENT_TYPE_DELETED, \
    EVENT_TYPE_MODIFIED, FileCreatedEvent
from watchdog.observers import Observer


class StorageInsufficient(Exception):
    """The storage usage of the directory exceeds the quota.
    """


class StorageManager:  # pylint:disable=too-many-instance-attributes
    """Automatically monitor and clear the storage of the directory.

    The priority strategy for deletion is to delete the oldest file
    first, the smallest deletion granularity is the entire secondary
    dir or file of the specified directory, and the termination
    condition for deletion is that the storage space is sufficient.

    Attributes:
        quota: Storage quota for the directory.
        monitor: A file system monitor for the directory.
    """

    # pylint:disable=too-many-arguments
    def __init__(self, monitor_path, cleanable_file_matcher,
                 quota=10240, healthy_rate=0.7, alarm_rate=0.9):
        """
        Args:
            monitor_path: The directory for storage management.
            cleanable_file_matcher:
                It is called during the process of cleaning up storage
                space to determine whether the file can be deleted,
                based on whether the file name matches.
            quota:
                Maximum available storage space of the directory.
                (unit: MB)
            healthy_rate:
                When the occupancy rate is lower than this value, the
                storage manager is in a healthy state.
            alarm_rate:
                When the occupancy rate is higher than this value, the
                storage manager is in an alarm state and starts
                cleaning operations.
        """
        super().__init__()

        self.__is_path_cleanable = cleanable_file_matcher

        self.quota = quota * 1024 * 1024
        self.__healthy_size = int(self.quota * healthy_rate)
        self.__alarm_size = int(self.quota * alarm_rate)

        self.__is_storage_sufficient = True

        self.monitor = DirMonitor(
            monitor_path, self.__judge_and_clear)

        self.__health_msg = ('Storage is sufficient. %d/{}(%.3f). '
                             '(byte)').format(self.quota)
        self.__warn_msg = ('Storage is insufficient. %d/{}(%.3f). '
                           '(byte)').format(self.quota)

    def start(self):
        """Start storage manager.
        """
        self.monitor.start()

    def stop(self):
        """Stop storage manager.
        """
        self.monitor.stop()

    def assert_storage_sufficient(self):
        """A checker for storage usage state.

        Raises:
            StorageInsufficient: Storage is insufficient.
        """
        if not self.__is_storage_sufficient:
            raise StorageInsufficient()

        log.info(self.__health_msg,
                 self.monitor.occupied_size,
                 self.monitor.occupied_size / self.quota)

    def __judge_and_clear(self, event, occupied_size, delta_size):
        self.__refresh_storage_flag(occupied_size)

        if self.__is_cleanup_condition_satisfied(
                event, occupied_size, delta_size):
            self.__is_storage_sufficient = self.__do_clear(
                occupied_size)

    def __is_cleanup_condition_satisfied(
            self, event, occupied_size, delta_size):
        return occupied_size > self.__alarm_size and \
            (delta_size > 0
             or event.event_type == EVENT_TYPE_MOVED
             and not self.__is_second_dir_cleanable(event.src_path)
             and self.__is_second_dir_cleanable(event.dest_path))

    def __is_second_dir_cleanable(self, path):
        return self.__is_path_cleanable(
            basename(self.monitor.parse_second_level_dir(path)))

    def __do_clear(self, occupied_size):
        clear_bytes = occupied_size - self.__healthy_size

        log.info('Start to clear. To be cleaned bytes: %s',
                 str(clear_bytes))
        is_success = _clear_files(self.monitor.metadatas,
                                  clear_bytes,
                                  self.__is_path_cleanable)
        log.info('Do clear %s', 'success' if is_success else 'failed')
        return is_success

    def __refresh_storage_flag(self, occupied_size):
        if occupied_size > self.quota:
            log.warning(self.__warn_msg,
                        occupied_size, occupied_size / self.quota)
            self.__is_storage_sufficient = False
        else:
            self.__is_storage_sufficient = True


class DirMonitor(FileSystemEventHandler):
    """A file system monitor for a directory.

    All files operation under the dir, as an event back to observers.

    Attributes:
        monitor_path: The top directory of the monitored directory tree.
        occupied_size: Occupied storage space in the directory.
        metadatas: A dict. Cache file path and size of all files in the
            directory. For example:

            {'./dir0/dir1':
                ({'./dir0/dir1': 4096, './dir0/dir1/file': 1}, 4097),
            './dir0/dir2':
                ({'./dir0/dir2': 4096, './dir0/dir2/file': 4}, 4100),
            }
    """

    def __init__(self, monitor_path, event_callback):
        self.monitor_path = monitor_path
        self.occupied_size = 0

        self.metadatas = collections.OrderedDict()

        self.__observer = Observer()
        self.__observer.schedule(
            event_handler=self, path=monitor_path, recursive=True)

        self.__handle_event = event_callback

    def start(self):
        """Start monitoring.
        """
        self.__init_metadatas()
        self.__handle_event(FileCreatedEvent(self.monitor_path),
                            self.occupied_size,
                            self.occupied_size)

        self.__init_metadatas()
        # TODO: Determine whether the watcher is working immediately
        self.__observer.start()

    def stop(self):
        """Stop monitoring.
        """
        self.__observer.stop()
        self.__observer.join()

    def dispatch(self, event):
        """Dispatch the file system events.

        The events in the queue are processed in a serial.

        Args:
            event: The event object representing the file system event.
        """
        delta_size = {
            EVENT_TYPE_CREATED: self.__on_created,
            EVENT_TYPE_DELETED: self.__on_deleted,
            EVENT_TYPE_MODIFIED: self.__on_modified,
            EVENT_TYPE_MOVED: self.__on_moved,
        }[event.event_type](event)

        self.occupied_size += delta_size

        self.__handle_event(event, self.occupied_size, delta_size)

    def __on_created(self, event):
        """Handle CREATE event.

        WATCHDOG BUG: The operation of creating a file will generate
        multiple CREATE events.
        """
        file_size = _get_size(event.src_path)
        return self.__push_file(event.src_path, file_size)

    def __on_deleted(self, event):
        return self.__pop_file(event.src_path)

    def __on_modified(self, event):
        if not exists(event.src_path) or isfile(event.src_path):
            file_size = _get_size(event.src_path)
            delta_size = self.__push_file(event.src_path, file_size)
        else:
            delta_size = 0

        return delta_size

    def __on_moved(self, event):
        """Handle MOVE event.

        The DEST_PATH is in the monitoring range by default. Do not
        consider move to be outside the monitoring range. WATCHDOG BUG:
        Cannot trigger event when the scope of the MV operation is
        outside the observed directory.
        """
        delta_size = self.__pop_file(event.src_path)

        file_size = _get_size(event.dest_path)
        delta_size += self.__push_file(event.dest_path, file_size)

        return delta_size

    def __push_file(self, path, file_size):
        second_dir = self.parse_second_level_dir(path)

        sub_tree, sub_tree_size = self.metadatas.get(second_dir, ({}, 0))

        o_file_size = sub_tree.get(path, 0)
        sub_tree[path] = file_size

        delta_size = file_size - o_file_size
        sub_tree_size += delta_size

        self.metadatas[second_dir] = (sub_tree, sub_tree_size)

        return delta_size

    def __pop_file(self, path):
        second_dir = self.parse_second_level_dir(path)

        sub_tree, sub_tree_size = self.metadatas.pop(second_dir)

        file_size = sub_tree.pop(path)

        if sub_tree:
            sub_tree_size -= file_size
            self.metadatas[second_dir] = (sub_tree, sub_tree_size)

        return -file_size

    def __init_metadatas(self):
        """Initial metadata of all files in the directory.

        Attention: Total size does not include the size of the top dir.

        Raises:
            FileNotFoundError: Monitor path unexist.
        """
        paths = [join(self.monitor_path, name)
                 for name in os.listdir(self.monitor_path)]
        # pylint:disable=unnecessary-lambda
        paths.sort(key=lambda path: getmtime(path))

        self.metadatas.clear()
        self.occupied_size = 0
        for path in paths:
            sub_tree, sub_tree_size = _get_node_size_mapping(path)
            self.metadatas[path] = (sub_tree, sub_tree_size)
            self.occupied_size += sub_tree_size

    def parse_second_level_dir(self, path):
        """Parse the second-level directory of the path with the
        monitoring directory as the first-level directory.

        Args:
            path: File path to be parsed in the monitoring directory.

        Returns:
            A path string.
        """
        r_path = path.replace(self.monitor_path, '', 1)
        for name in r_path.split('/'):
            if name:
                path_basename = name
                break
        secondary_path = join(self.monitor_path, path_basename)
        return secondary_path

    @property
    def observer(self):
        """File system observer.
        """
        return self.__observer


def _get_node_size_mapping(tree_root):
    """Recursively get the mapping of the node path and size in the root.

    Args:
        tree_root: Top path of the file tree.

    Returns:
        A tuple about node_size mapping and tree size. For example:
        ({}, 0). Attention: When the type of tree_root is file,
        the return is empty.
    """
    if os.path.isfile(tree_root):
        tree_size = getsize(tree_root)
        return {tree_root: tree_size}, tree_size

    tree_size = 0
    node_size_mapping = {}
    for sub_root, _, nodes in os.walk(tree_root):
        node_size = getsize(sub_root)
        tree_size += node_size
        node_size_mapping[sub_root] = node_size
        for name in nodes:
            node_size = getsize(join(sub_root, name))
            tree_size += node_size
            node_size_mapping[join(sub_root, name)] = node_size
    return node_size_mapping, tree_size


def _get_size(path):
    """Get file or dir size.

    Returns:
        bytes. If path not exist, return 0.
    """
    try:
        file_size = getsize(path)
    except FileNotFoundError as err:
        log.debug(str(err))
        file_size = 0

    return file_size


def _clear_files(metadatas, clear_bytes, is_cleanable):
    """Clean up some files in the collection.

    Delete in the order of the collection until clear_bytes is reached.

    Args:
        metadatas: A collection about metadata. For example:

            {'./dir0/dir1':
                ({'./dir0/dir1': 4096, './dir0/dir1/file': 1}, 4097),
            './dir0/dir2':
                ({'./dir0/dir2': 4096, './dir0/dir2/file': 4}, 4100),
            }

        is_cleanable: It is called to judge whether the file can be
            deleted by the file name.

    Returns:
        A boolean. if clear_bytes is reached.
    """
    is_done = False

    for path, (_, sub_tree_size) in metadatas.items():
        if clear_bytes < 0:
            is_done = True
            break

        if is_cleanable(basename(path)):
            shutil.rmtree(path, ignore_errors=True)
            log.info('Delete dir tree: %s, %d', path, sub_tree_size)
            clear_bytes -= sub_tree_size
        else:
            log.debug('Ignore discleanable path: %s', path)

    log.info('Uncleaned bytes: %d', clear_bytes)
    return is_done
