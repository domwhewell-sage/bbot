import json
import requests
from bbot.modules.base import BaseModule


class fileparser(BaseModule):
    watched_events = ["FILESYSTEM"]
    produced_events = ["RAW_DATA"]
    flags = ["passive"]
    meta = {
        "description": "Module to extract data from files",
        "created_date": "2024-06-03",
        "author": "@domwhewell-sage",
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
        return True

    async def filter_event(self, event):
        if "file" not in event.tags:
            return False, "Event is not a file"
        return True

    async def handle_event(self, event):
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
