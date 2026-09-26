import os
import itertools


class DownloadQueue:
    """A named collection of downloads with its own concurrency limit,
    target directory and pause/resume state.

    Download thread objects are shared with the parent's flat `self.downloads`
    list, so existing iteration over all downloads keeps working unchanged.
    """

    def __init__(self, queue_id, name, target_directory, max_concurrent, parent,
                 state="active"):
        self.queue_id = queue_id
        self.name = name
        self.target_directory = target_directory or ""
        self.max_concurrent = max_concurrent
        self.state = state  # "active" | "paused"
        self.parent = parent
        self.downloads = []

    # -- lifecycle ---------------------------------------------------------
    def add_download(self, download_thread):
        if download_thread not in self.downloads:
            self.downloads.append(download_thread)
        download_thread.queue_id = self.queue_id
        flat = self.parent.downloads
        if download_thread not in flat:
            flat.append(download_thread)

    def remove_download(self, download_thread):
        if download_thread in self.downloads:
            self.downloads.remove(download_thread)
        if hasattr(download_thread, "queue_id"):
            download_thread.queue_id = None

    # -- state -------------------------------------------------------------
    def pause_all(self):
        self.state = "paused"
        for dt in list(self.downloads):
            if _is_active(dt):
                dt.pause(False)

    def resume_all(self):
        self.state = "active"
        for dt in list(self.downloads):
            if _is_active(dt):
                dt.resume(False)

    # -- directory resolution ---------------------------------------------
    def get_effective_directory(self):
        """Empty target_directory means 'inherit global download directory'."""
        if self.target_directory and self.target_directory.strip():
            return self.target_directory.strip()
        return self.parent.appconf["download_directory"]

    def get_effective_torrent_directory(self):
        """Resolve torrent directory: queue override > global torrent dir > global dir."""
        if self.target_directory and self.target_directory.strip():
            return self.target_directory.strip()
        conf = self.parent.appconf
        if (conf.get("torrent_download_directory_custom_enabled") == "1"
                and conf.get("torrent_download_directory")):
            return conf["torrent_download_directory"]
        return conf["download_directory"]

    # -- serialization -----------------------------------------------------
    def to_dict(self):
        return {
            "id": self.queue_id,
            "name": self.name,
            "target_directory": self.target_directory,
            "max_concurrent": self.max_concurrent,
            "state": self.state,
        }

    @classmethod
    def from_dict(cls, data, parent):
        return cls(
            queue_id=data.get("id"),
            name=data.get("name", "Queue"),
            target_directory=data.get("target_directory", ""),
            max_concurrent=data.get("max_concurrent", 4),
            parent=parent,
            state=data.get("state", "active"),
        )


class QueueManager:
    """Manages the set of DownloadQueue objects.

    A single 'In-Flow' queue always exists and cannot be deleted; standalone
    queues are user-created. The active queue receives newly added downloads.
    """

    INFLOW_ID = "infow"

    def __init__(self, parent):
        self.parent = parent
        self.queues = {}
        self.active_queue_id = self.INFLOW_ID

        infow = DownloadQueue(
            queue_id=self.INFLOW_ID,
            name=_queue_name("In-Flow"),
            target_directory="",
            max_concurrent=parent.appconf.get("download_simultaneous_amount", 4),
            parent=parent,
            state="active",
        )
        self.queues[infow.queue_id] = infow

    # -- accessors ---------------------------------------------------------
    def get_active_queue(self):
        return self.queues.get(self.active_queue_id) or self.queues[self.INFLOW_ID]

    def get_queue(self, queue_id):
        return self.queues.get(queue_id)

    def switch_queue(self, queue_id):
        if queue_id in self.queues:
            self.active_queue_id = queue_id
            return True
        return False

    def get_all_queue_ids(self):
        return list(self.queues.keys())

    def get_downloads_for_queue(self, queue_id):
        q = self.queues.get(queue_id)
        return list(q.downloads) if q else []

    # -- downloads ---------------------------------------------------------
    def add_download(self, download_thread):
        self.get_active_queue().add_download(download_thread)

    def move_download(self, download_thread, target_queue_id):
        target = self.queues.get(target_queue_id)
        if target is None:
            return False
        for q in self.queues.values():
            q.remove_download(download_thread)
        target.add_download(download_thread)
        return True

    # -- queue lifecycle ---------------------------------------------------
    def create_queue(self, name, target_directory="", max_concurrent=4):
        queue = DownloadQueue(
            queue_id=_new_id(self.queues),
            name=name,
            target_directory=target_directory,
            max_concurrent=max_concurrent,
            parent=self.parent,
            state="active",
        )
        self.queues[queue.queue_id] = queue
        self.active_queue_id = queue.queue_id
        return queue

    def delete_queue(self, queue_id):
        """Remove a standalone queue. Returns False if the queue holds active
        downloads — the caller must finish/cancel them first."""
        if queue_id == self.INFLOW_ID:
            return False
        queue = self.queues.get(queue_id)
        if queue is None:
            return False
        if any(_is_active(dt) for dt in queue.downloads):
            return False
        for dt in list(queue.downloads):
            queue.remove_download(dt)
        del self.queues[queue_id]
        if self.active_queue_id == queue_id:
            self.active_queue_id = self.INFLOW_ID
        return True

    def pause_queue(self, queue_id):
        queue = self.queues.get(queue_id)
        if queue:
            queue.pause_all()

    def resume_queue(self, queue_id):
        queue = self.queues.get(queue_id)
        if queue:
            queue.resume_all()

    # -- serialization -----------------------------------------------------
    def to_dict(self):
        return {"queues": [q.to_dict() for q in self.queues.values()]}

    @classmethod
    def from_dict(cls, data, parent):
        mgr = cls(parent)
        if not data or "queues" not in data:
            return mgr
        mgr.queues = {}
        for item in data["queues"]:
            queue = DownloadQueue.from_dict(item, parent)
            mgr.queues[queue.queue_id] = queue
        if mgr.INFLOW_ID not in mgr.queues:
            mgr.queues[mgr.INFLOW_ID] = DownloadQueue(
                queue_id=mgr.INFLOW_ID,
                name=_queue_name("In-Flow"),
                target_directory="",
                max_concurrent=parent.appconf.get("download_simultaneous_amount", 4),
                parent=parent,
                state="active",
            )
        if mgr.active_queue_id not in mgr.queues:
            mgr.active_queue_id = mgr.INFLOW_ID
        return mgr


# -- helpers ---------------------------------------------------------------
def _is_active(download_thread):
    """A download is 'active' (pausable/resumable) unless complete or cancelled."""
    return not getattr(download_thread, "is_complete", False) and \
        not getattr(download_thread, "cancelled", False)


def _queue_name(name):
    """Translate the In-Flow default name if gettext is available."""
    try:
        from stringstorage import gettext as _
        return _(name)
    except Exception:
        return name


def _new_id(queues):
    for i in itertools.count(1):
        candidate = "queue" + str(i)
        if candidate not in queues:
            return candidate
