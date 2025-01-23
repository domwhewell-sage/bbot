from .base import ModuleTestBase


class TestGitHacker(ModuleTestBase):
    targets = ["http://127.0.0.1:8888/"]

    modules_overrides = ["git", "githacker", "httpx"]

    index_html = """<html>
        <head>
            <title>Index of /.git</title>
        </head>
        <body>
            <h1>Index of /.git</h1>
            <table>
                <tr><th>Name</th><th>Size</th></tr>
                <tr><td><a href='/.git/branches/'>&lt;branches&gt;</a></td><td></td></tr>
                <tr><td><a href='/.git/config'>config</a></td><td>157B</td></tr>
                <tr><td><a href='/.git/description'>description</a></td><td>73B</td></tr>
                <tr><td><a href='/.git/HEAD'>HEAD</a></td><td>23B</td></tr>
                <tr><td><a href='/.git/hooks/'>&lt;hooks&gt;</a></td><td></td></tr>
                <tr><td><a href='/.git/info/'>&lt;info&gt;</a></td><td></td></tr>
                <tr><td><a href='/.git/objects/'>&lt;objects&gt;</a></td><td></td></tr>
                <tr><td><a href='/.git/refs/'>&lt;refs&gt;</a></td><td></td></tr>
            </table>
        </body>
    </html>"""

    info_index = """<html>
        <head>
            <title>Index of /.git/info</title>
        </head>
        <body>
            <h1>Index of /.git/info</h1>
            <table>
                <tr><th>Name</th><th>Size</th></tr>
                <tr><td><a href='../'>[..]</a></td><td></td></tr>
                <tr><td><a href='/.git/info/exclude'>exclude</a></td><td>240B</td></tr>
            </table>
        </body>
    </html>"""

    objects_index = """<html>
        <head>
            <title>Index of /.git/objects</title>
        </head>
        <body>
            <h1>Index of /.git/objects</h1>
            <table>
                <tr><th>Name</th><th>Size</th></tr>
                <tr><td><a href='../'>[..]</a></td><td></td></tr>
                <tr><td><a href='/.git/objects/pack/'>&lt;pack&gt;</a></td><td></td></tr>
                <tr><td><a href='/.git/objects/info/'>&lt;info&gt;</a></td><td></td></tr>
            </table>
        </body>
    </html>"""

    refs_index = """<html>
        <head>
            <title>Index of /.git/refs</title>
        </head>
        <body>
            <h1>Index of /.git/refs</h1>
            <table>
                <tr><th>Name</th><th>Size</th></tr>
                <tr><td><a href='../'>[..]</a></td><td></td></tr>
                <tr><td><a href='/.git/refs/heads/'>&lt;heads&gt;</a></td><td></td></tr>
                <tr><td><a href='/.git/refs/tags/'>&lt;tags&gt;</a></td><td></td></tr>
            </table>
        </body>
    </html>
    """

    empty_index = """<html>
        <head>
            <title>Index of /.git/...</title>
        </head>
        <body>
            <h1>Index of /.git/...</h1>
            <table>
                <tr><th>Name</th><th>Size</th></tr>
                <tr><td><a href='../'>[..]</a></td><td></td></tr>
            </table>
        </body>
    </html>"""

    git_head = "ref: refs/heads/master"

    git_description = "Unnamed repository; edit this file 'description' to name the repository."

    git_config = """[core]
    repositoryformatversion = 0
    filemode = true
    bare = false
    logallrefupdates = true"""

    git_exclude = """# git ls-files --others --exclude-from=.git/info/exclude
    # Lines that start with '#' are comments.
    # For a project mostly in C, the following would be a good set of
    # exclude patterns (uncomment them if you want to use them):
    # *.[oa]
    # *~"""

    async def setup_after_prep(self, module_test):
        module_test.set_expect_requests(expect_args={"uri": "/.git/"}, respond_args={"response_data": self.index_html})
        module_test.set_expect_requests(
            expect_args={"uri": "/.git/config"}, respond_args={"response_data": self.git_config}
        )
        module_test.set_expect_requests(
            expect_args={"uri": "/.git/branches/"}, respond_args={"response_data": self.empty_index}
        )
        module_test.set_expect_requests(
            expect_args={"uri": "/.git/description"}, respond_args={"response_data": self.git_description}
        )
        module_test.set_expect_requests(
            expect_args={"uri": "/.git/HEAD"}, respond_args={"response_data": self.git_head}
        )
        module_test.set_expect_requests(
            expect_args={"uri": "/.git/hooks/"}, respond_args={"response_data": self.empty_index}
        )
        module_test.set_expect_requests(
            expect_args={"uri": "/.git/info/"}, respond_args={"response_data": self.info_index}
        )
        module_test.set_expect_requests(
            expect_args={"uri": "/.git/info/exclude"}, respond_args={"response_data": self.git_exclude}
        )
        module_test.set_expect_requests(
            expect_args={"uri": "/.git/objects/"}, respond_args={"response_data": self.objects_index}
        )
        module_test.set_expect_requests(
            expect_args={"uri": "/.git/objects/info/"}, respond_args={"response_data": self.empty_index}
        )
        module_test.set_expect_requests(
            expect_args={"uri": "/.git/objects/pack/"}, respond_args={"response_data": self.empty_index}
        )
        module_test.set_expect_requests(
            expect_args={"uri": "/.git/refs/"}, respond_args={"response_data": self.refs_index}
        )
        module_test.set_expect_requests(
            expect_args={"uri": "/.git/refs/heads/"}, respond_args={"response_data": self.empty_index}
        )
        module_test.set_expect_requests(
            expect_args={"uri": "/.git/refs/tags/"}, respond_args={"response_data": self.empty_index}
        )

    def check(self, module_test, events):
        assert any(
            e.type == "CODE_REPOSITORY"
            and "git_directory" in e.tags
            and e.data["url"] == "http://127.0.0.1:8888/.git/"
            for e in events
        )
        assert any(
            e.type == "FILESYSTEM" and "git_directory" in e.tags and e.data["url"] == "http://127.0.0.1:8888/.git/"
            for e in events
        )
