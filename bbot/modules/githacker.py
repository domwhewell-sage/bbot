from pathlib import Path
from subprocess import CalledProcessError
from bbot.modules.base import BaseModule


class githacker(BaseModule):
    watched_events = ["CODE_REPOSITORY"]
    produced_events = ["FILESYSTEM"]
    flags = ["passive", "safe", "slow", "code-enum"]
    meta = {
        "description": "Download a leaked .git folder recursively or by fuzzing common names",
        "created_date": "",
        "author": "@domwhewell-sage",
    }
    options = {
        "output_folder": "",
        "brute": False,
        "max_semanic_version": 10,
    }
    options_desc = {
        "output_folder": "Folder to download repositories to",
        "brute": "Brute force branch/tag names",
        "max_semanic_version": "Max number to brute force to",
    }

    deps_apt = ["git"]

    scope_distance_modifier = 2

    async def setup(self):
        output_folder = self.config.get("output_folder")
        if output_folder:
            self.output_dir = Path(output_folder) / "git_repos"
        else:
            self.output_dir = self.scan.home / "git_repos"
        self.helpers.mkdir(self.output_dir)
        self.tempdir = self.helpers.temp_dir / "git_directories"
        self.helpers.mkdir(self.tempdir)
        self.brute = self.config.get("brute", False)
        self.git_files = [
            ".git/",
            "config",
            "hooks/",
            "hooks/applypatch-msg",
            "hooks/commit-msg",
            "hooks/fsmonitor-watchman",
            "hooks/post-update",
            "hooks/pre-applypatch",
            "hooks/pre-commit",
            "hooks/pre-merge-commit",
            "hooks/pre-push",
            "hooks/pre-rebase",
            "hooks/pre-receive",
            "hooks/prepare-commit-msg",
            "hooks/update",
            "COMMIT_EDITMSG",
            "description",
            "FETCH_HEAD",
            "HEAD",
            "index",
            "info/",
            "info/exclude",
            "logs",
            "logs/HEAD",
            "logs/refs/",
            "logs/refs/remotes/",
            "logs/refs/remotes/origin/",
            "logs/refs/remotes/origin/HEAD",
            "logs/refs/stash",
            "ORIG_HEAD",
            "packed-refs",
            "refs/",
            "refs/remotes/",
            "refs/remotes/origin/",
            "refs/remotes/origin/HEAD",
            "refs/stash",
            "objects/",
            "objects/info/",
            "objects/info/alternates",
            "objects/info/http-alternates",
            "objects/info/packs",
        ]
        if self.brute:
            for major in range(self.max_semanic_version):
                for minor in range(self.max_semanic_version):
                    for patch in range(self.max_semanic_version):
                        self.git_files.append(f"refs/tags/v{major}.{minor}.{patch}")
                        self.git_files.append(f"refs/tags/{major}.{minor}.{patch}")
        else:
            self.git_files.extend(
                [
                    "refs/tags/v0.0.1",
                    "refs/tags/0.0.1",
                    "refs/tags/v1.0.0",
                    "refs/tags/1.0.0",
                ]
            )
        return await super().setup()

    async def filter_event(self, event):
        if event.type == "CODE_REPOSITORY":
            if "git-directory" not in event.tags:
                return False, "event is not a leaked .git directory"
            else:
                url = self.helpers.urljoin(event.data.get("url"), "HEAD")
                response = await self.helpers.request(url, method="HEAD")
                if response.status_code != 200:
                    return False, f"The target url({url}) is not a git repository"
        return True

    async def handle_event(self, event):
        repo_url = event.data.get("url")
        self.verbose(f"Processing leaked .git directory at {repo_url}")
        repo_folder = self.helpers.tagify(repo_url)
        dir_listing = await self.directory_listing_enabled(repo_url)
        if dir_listing:
            tmp_dir = await self.recursive_dir_list(dir_listing)
        else:
            tmp_dir = await self.git_fuzz(repo_url, repo_folder)
        # tmp_dir = await self.download_files(urls, repo_folder)
        if tmp_dir:
            repo_path = await self.clone_git_repository(tmp_dir, repo_folder)
            if repo_path:
                codebase_event = self.make_event({"path": str(repo_path)}, "FILESYSTEM", tags=["git"], parent=event)
                await self.emit_event(
                    codebase_event,
                    context=f"{{module}} cloned git repo at {repo_url} to {{event.type}}: {str(repo_path)}",
                )

    async def directory_listing_enabled(self, repo_url):
        response = await self.helpers.request(repo_url)
        if "<title>Index of" in response.text:
            self.info(f"Directory listing enabled at {repo_url}")
            return response
        return None

    async def recursive_dir_list(self, dir_listing):
        file_list = []
        soup = self.helpers.beautifulsoup(dir_listing.text, "html.parser")
        links = soup.find_all("a")
        for link in links:
            href = link["href"]
            if href == "../" or href == "/":
                continue
            file_url = self.helpers.urljoin(str(dir_listing.url), href)
            url = self.helpers.urlparse(file_url)
            if url.path.endswith("/"):
                response = await self.helpers.request(file_url)
                if response.status_code == 200:
                    file_list.extend(await self.recursive_dir_list(response))
            else:
                # Ensure the file is in the same domain as the directory listing
                if file_url.startswith(str(dir_listing.url)):
                    url = self.helpers.urlparse(file_url)
                    file_list.append(url)
        return file_list

    async def git_fuzz(self, repo_url, folder):
        containing_folder = self.tempdir / folder
        self.helpers.mkdir(containing_folder)
        self.info(f"Directory listing not enabled, fuzzing {repo_url} for git files")
        for file in self.git_files:
            file_url = self.helpers.urljoin(repo_url, file)
            git_index = file_url.path.find(".git")
            if file.endswith("/"):
                self.helpers.mkdir(containing_folder / file_url.path[git_index:])
            else:
                filename = str(containing_folder / file_url.path[git_index:])
                self.debug(f"Downloading {file_url} to {filename}")
                await self.helpers.download(file_url, filename=filename)
        if containing_folder.iterdir():
            return containing_folder
        else:
            self.verbose(f"No files downloaded, removing temp directory {containing_folder}")
            self.helpers.rm_rf(containing_folder)
            return None

    async def download_files(self, urls, folder):
        containing_folder = self.tempdir / folder
        self.helpers.mkdir(containing_folder)
        self.verbose(f"Downloading the files to the temp directory {containing_folder}")
        for url in urls:
            git_index = url.path.find(".git")
            if url.path.endswith("/"):
                self.helpers.mkdir(containing_folder / url.path[git_index:])
            else:
                file_url = url.geturl()
                filename = str(containing_folder / url.path[git_index:])
                self.debug(f"Downloading {file_url} to {filename}")
                await self.helpers.download(file_url, filename=filename)
        if containing_folder.iterdir():
            return containing_folder
        else:
            self.verbose(f"No files downloaded, removing temp directory {containing_folder}")
            self.helpers.rm_rf(containing_folder)
            return None

    async def clone_git_repository(self, tmp_dir, dst_dir):
        folder = self.output_dir / dst_dir
        self.helpers.mkdir(folder)
        self.verbose(f"Using git clone to reconstruct the repository at {folder}")
        command = ["git", "-C", folder, "clone", f"file://{tmp_dir}"]
        try:
            output = await self.run_process(command, env={"GIT_TERMINAL_PROMPT": "0"}, check=True)
        except CalledProcessError as e:
            self.debug(f"Error cloning {tmp_dir}. STDERR: {repr(e.stderr)}")
            return

        folder_name = output.stderr.split("Cloning into '")[1].split("'")[0]
        self.helpers.rm_rf(tmp_dir)
        return folder / folder_name

    async def cleanup(self):
        self.helpers.rm_rf(self.tempdir)
        pass
