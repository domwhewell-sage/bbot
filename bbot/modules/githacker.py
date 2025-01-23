from GitHacker import GitHacker, remove_suffixes, md5

from pathlib import Path
from bbot.modules.base import BaseModule


class githacker(BaseModule):
    watched_events = ["CODE_REPOSITORY"]
    produced_events = ["FILESYSTEM"]
    flags = ["passive", "safe", "slow", "code-enum"]
    meta = {
        "description": "Download a leaked .git folder recursively or by bruteforcing common names",
        "created_date": "",
        "author": "@domwhewell-sage",
    }
    options = {
        "output_folder": "",
        "brute": False,
        "enable_manually_check_dangerous_git_files": False,
        "threads": 4,
        "delay": 0,
    }
    options_desc = {
        "output_folder": "Folder to download repositories to",
        "brute": "Brute force branch/tag names",
        "enable_manually_check_dangerous_git_files": "Disable manually checking for dangerous git files",
        "threads": "Number of threads to use",
        "delay": "Number of seconds between HTTP requests",
    }

    deps_pip = ["GitHacker~=1.1.7"]

    scope_distance_modifier = 2

    async def setup(self):
        output_folder = self.config.get("output_folder")
        if output_folder:
            self.output_dir = Path(output_folder) / "git_repos"
        else:
            self.output_dir = self.scan.home / "git_repos"
        self.helpers.mkdir(self.output_dir)
        self.brute = self.config.get("brute", False)
        self.disable_manually_check = self.config.get("enable_manually_check_dangerous_git_files", False)
        self.threads = self.config.get("threads", 4)
        self.delay = self.config.get("delay", 0)
        return await super().setup()

    async def filter_event(self, event):
        if event.type == "CODE_REPOSITORY":
            if "git-directory" not in event.tags:
                return False, "event is not a leaked .git directory"
        return True

    async def handle_event(self, event):
        repo_url = event.data.get("url")
        # repo_path = await self.scan.helpers.run_in_executor(self.githacker, repo_url)
        # if repo_path:
        #     self.verbose(f"Downloaded {repo_url} to {repo_path}")
        #     codebase_event = self.make_event({"path": str(repo_path)}, "FILESYSTEM", tags=["git"], parent=event)
        #     await self.emit_event(
        #         codebase_event,
        #         context=f"{{module}} downloaded git repo at {repo_url} to {{event.type}}: {repo_path}",
        #     )