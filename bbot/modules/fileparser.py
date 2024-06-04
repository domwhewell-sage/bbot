import json
import requests
from pathlib import Path

from bbot.modules.base import BaseModule


class fileparser(BaseModule):
    watched_events = ["FILESYSTEM"]
    produced_events = ["FILESYSTEM", "RAW_DATA"]
    flags = ["passive"]
    meta = {
        "description": "Module to extract data from files",
        "created_date": "2024-06-03",
        "author": "@domwhewell-sage",
    }
    options = {
        "extensions": [
            "bak",  #  Backup File
            "bash",  #  Bash Script or Configuration
            "bashrc",  #  Bash Script or Configuration
            "conf",  #  Configuration File
            "cfg",  #  Configuration File
            "crt",  #  Certificate File
            "csv",  #  Comma Separated Values File
            "db",  #  SQLite Database File
            "sqlite",  #  SQLite Database File
            "doc",  #  Microsoft Word Document (Old Format)
            "docx",  #  Microsoft Word Document
            "exe",  #  Windows PE executable
            "ica",  #  Citrix Independent Computing Architecture File
            "indd",  #  Adobe InDesign Document
            "ini",  #  Initialization File
            "jar",  #  Java Archive
            "key",  #  Private Key File
            "pub",  #  Public Key File
            "log",  #  Log File
            "markdown",  #  Markdown File
            "md",  #  Markdown File
            "msi",  # Windows setup file
            "odg",  #  OpenDocument Graphics (LibreOffice, OpenOffice)
            "odp",  #  OpenDocument Presentation (LibreOffice, OpenOffice)
            "ods",  #  OpenDocument Spreadsheet (LibreOffice, OpenOffice)
            "odt",  #  OpenDocument Text (LibreOffice, OpenOffice)
            "pdf",  #  Adobe Portable Document Format
            "pem",  #  Privacy Enhanced Mail (SSL certificate)
            "pps",  #  Microsoft PowerPoint Slideshow (Old Format)
            "ppsx",  #  Microsoft PowerPoint Slideshow
            "ppt",  #  Microsoft PowerPoint Presentation (Old Format)
            "pptx",  #  Microsoft PowerPoint Presentation
            "ps1",  #  PowerShell Script
            "raw",  #  Raw Image File Format
            "rdp",  #  Remote Desktop Protocol File
            "sh",  #  Shell Script
            "sql",  #  SQL Database Dump
            "swp",  #  Swap File (temporary file, often Vim)
            "sxw",  #  OpenOffice.org Writer document
            "tar",  #  Tar Archive
            "tar.gz",  # Gzip-Compressed Tar Archive
            "zip",  #  Zip Archive
            "txt",  #  Plain Text Document
            "vbs",  #  Visual Basic Script
            "wpd",  #  WordPerfect Document
            "xls",  #  Microsoft Excel Spreadsheet (Old Format)
            "xlsx",  #  Microsoft Excel Spreadsheet
            "xml",  #  eXtensible Markup Language File
            "yml",  #  YAML Ain't Markup Language
            "yaml",  #  YAML Ain't Markup Language
        ],
    }
    options_desc = {
        "extensions": "File extensions to parse",
    }

    deps_ansible = [
        {
            "name": "Check if Docker is already installed",
            "command": "docker --version",
            "register": "docker_installed",
            "ignore_errors": True,
        },
        {
            "name": "Install Docker (Non-Debian)",
            "package": {"name": "docker", "state": "present"},
            "become": True,
            "when": "ansible_facts['os_family'] != 'Debian' and docker_installed.rc != 0",
        },
        {
            "name": "Install Docker (Debian)",
            "package": {
                "name": "docker.io",
                "state": "present",
            },
            "become": True,
            "when": "ansible_facts['os_family'] == 'Debian' and docker_installed.rc != 0",
        },
    ]

    async def setup(self):
        await self.run_process("systemctl", "start", "docker", sudo=True)
        await self.run_process(
            "docker", "run", "-d", "-p", "9998:9998", "--name", "apache_tika", "--rm", "apache/tika:latest", sudo=True
        )
        docker_ip = await self.get_docker_ip()
        self.tika_url = f"http://{docker_ip}:9998/tika"
        self.extensions = list(set([e.lower().strip(".") for e in self.config.get("extensions", [])]))
        return True

    async def filter_event(self, event):
        if "file" not in event.tags and "folder" not in event.tags:
            return False, "Event is not a file or folder"
        if not any(event.data["path"].endswith(f".{ext}") for ext in self.extensions):
            return False, "File extension not in the allowed list"
        return True

    async def handle_event(self, event):
        if "folder" in event.tags:
            folder_path = Path(event.data["path"])
            for file_path in folder_path.rglob("*"):
                if any(file_path.name.endswith(f".{ext}") for ext in self.extensions):
                    file_event = self.make_event(
                        {"path": str(file_path)}, "FILESYSTEM", tags=["parsed_folder", "file"], source=event
                    )
                    file_event.scope_distance = event.scope_distance
                    await self.emit_event(file_event)
        elif "file" in event.tags:
            file_path = event.data["path"]
            content = await self.extract_text(file_path)
            if content:
                raw_data_event = self.make_event(
                    content,
                    "RAW_DATA",
                    source=event,
                )
                await self.emit_event(raw_data_event)

    async def extract_text(self, file_path):
        """
        extract_text Extracts plaintext from a document path using Tika.

        :param file_path: The path of the file to extract text from.
        :return: ASCII-encoded plaintext extracted from the document.
        """

        with open(file_path, "rb") as f:
            resp = requests.put(self.tika_url, f, headers={"Accept": "application/json"})
            if resp.status_code == 200:
                return resp.json()

    async def get_docker_ip(self):
        docker_ip = "172.17.0.1"
        try:
            ip_output = await self.run_process(["ip", "-j", "-4", "a", "show", "dev", "docker0"])
            interface_json = json.loads(ip_output.stdout)
            docker_ip = interface_json[0]["addr_info"][0]["local"]
        except Exception:
            pass
        return docker_ip

    async def finish(self):
        await self.run_process("docker", "stop", "apache_tika", sudo=True)
        return
