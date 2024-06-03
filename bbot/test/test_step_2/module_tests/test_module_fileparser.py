from pathlib import Path
from .base import ModuleTestBase


class TestFileParser(ModuleTestBase):
    targets = ["http://127.0.0.1:8888"]
    modules_overrides = ["fileparser", "filedownload", "httpx", "excavate", "speculate"]
    config_overrides = {"web_spider_distance": 2, "web_spider_depth": 2}

    pdf_data = """%PDF-1.3
%���� ReportLab Generated PDF document http://www.reportlab.com
1 0 obj
<<
/F1 2 0 R
>>
endobj
2 0 obj
<<
/BaseFont /Helvetica /Encoding /WinAnsiEncoding /Name /F1 /Subtype /Type1 /Type /Font
>>
endobj
3 0 obj
<<
/Contents 7 0 R /MediaBox [ 0 0 595.2756 841.8898 ] /Parent 6 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
4 0 obj
<<
/PageMode /UseNone /Pages 6 0 R /Type /Catalog
>>
endobj
5 0 obj
<<
/Author (anonymous) /CreationDate (D:20240603185816+00'00') /Creator (ReportLab PDF Library - www.reportlab.com) /Keywords () /ModDate (D:20240603185816+00'00') /Producer (ReportLab PDF Library - www.reportlab.com) 
  /Subject (unspecified) /Title (untitled) /Trapped /False
>>
endobj
6 0 obj
<<
/Count 1 /Kids [ 3 0 R ] /Type /Pages
>>
endobj
7 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 107
>>
stream
GapQh0E=F,0U\H3T\pNYT^QKk?tc>IP,;W#U1^23ihPEM_?CW4KISi90MjG^2,FS#<RC5+c,n)Z;$bK$b"5I[<!^TD#gi]&=5X,[5@Y@V~>endstream
endobj
xref
0 8
0000000000 65535 f 
0000000073 00000 n 
0000000104 00000 n 
0000000211 00000 n 
0000000414 00000 n 
0000000482 00000 n 
0000000778 00000 n 
0000000837 00000 n 
trailer
<<
/ID 
[<80d9f5b964fc99284501deb7a6a637f7><80d9f5b964fc99284501deb7a6a637f7>]
% ReportLab generated PDF document -- digest (http://www.reportlab.com)

/Info 5 0 R
/Root 4 0 R
/Size 8
>>
startxref
1034
%%EOF"""

    tika_response = {
        "pdf:unmappedUnicodeCharsPerPage": "0",
        "pdf:PDFVersion": "1.3",
        "pdf:docinfo:title": "untitled",
        "xmp:CreatorTool": "ReportLab PDF Library - www.reportlab.com",
        "pdf:hasXFA": "false",
        "access_permission:modify_annotations": "true",
        "access_permission:can_print_degraded": "true",
        "X-TIKA:Parsed-By-Full-Set": ["org.apache.tika.parser.DefaultParser", "org.apache.tika.parser.pdf.PDFParser"],
        "dc:creator": "anonymous",
        "pdf:num3DAnnotations": "0",
        "dcterms:created": "2024-06-03T18:58:16Z",
        "dcterms:modified": "2024-06-03T18:58:16Z",
        "dc:format": "application/pdf; version=1.3",
        "pdf:docinfo:creator_tool": "ReportLab PDF Library - www.reportlab.com",
        "pdf:overallPercentageUnmappedUnicodeChars": "0.0",
        "access_permission:fill_in_form": "true",
        "pdf:docinfo:modified": "2024-06-03T18:58:16Z",
        "pdf:hasCollection": "false",
        "pdf:encrypted": "false",
        "dc:title": "untitled",
        "pdf:containsNonEmbeddedFont": "true",
        "Content-Length": "1426",
        "pdf:docinfo:subject": "unspecified",
        "pdf:hasMarkedContent": "false",
        "Content-Type": "application/pdf",
        "pdf:docinfo:creator": "anonymous",
        "pdf:producer": "ReportLab PDF Library - www.reportlab.com",
        "dc:subject": "unspecified",
        "pdf:totalUnmappedUnicodeChars": "0",
        "access_permission:extract_for_accessibility": "true",
        "access_permission:assemble_document": "true",
        "xmpTPg:NPages": "1",
        "pdf:hasXMP": "false",
        "pdf:charsPerPage": "13",
        "access_permission:extract_content": "true",
        "access_permission:can_print": "true",
        "pdf:docinfo:trapped": "False",
        "X-TIKA:Parsed-By": ["org.apache.tika.parser.DefaultParser", "org.apache.tika.parser.pdf.PDFParser"],
        "X-TIKA:content": '<html xmlns="http://www.w3.org/1999/xhtml">\n<head>\n<meta name="pdf:PDFVersion" content="1.3" />\n<meta name="pdf:docinfo:title" content="untitled" />\n<meta name="xmp:CreatorTool" content="ReportLab PDF Library - www.reportlab.com" />\n<meta name="pdf:hasXFA" content="false" />\n<meta name="access_permission:modify_annotations" content="true" />\n<meta name="access_permission:can_print_degraded" content="true" />\n<meta name="dc:creator" content="anonymous" />\n<meta name="dcterms:created" content="2024-06-03T18:58:16Z" />\n<meta name="dcterms:modified" content="2024-06-03T18:58:16Z" />\n<meta name="dc:format" content="application/pdf; version=1.3" />\n<meta name="pdf:docinfo:creator_tool" content="ReportLab PDF Library - www.reportlab.com" />\n<meta name="access_permission:fill_in_form" content="true" />\n<meta name="pdf:docinfo:modified" content="2024-06-03T18:58:16Z" />\n<meta name="pdf:hasCollection" content="false" />\n<meta name="pdf:encrypted" content="false" />\n<meta name="dc:title" content="untitled" />\n<meta name="Content-Length" content="1426" />\n<meta name="pdf:docinfo:subject" content="unspecified" />\n<meta name="pdf:hasMarkedContent" content="false" />\n<meta name="Content-Type" content="application/pdf" />\n<meta name="pdf:docinfo:creator" content="anonymous" />\n<meta name="pdf:producer" content="ReportLab PDF Library - www.reportlab.com" />\n<meta name="dc:subject" content="unspecified" />\n<meta name="access_permission:extract_for_accessibility" content="true" />\n<meta name="access_permission:assemble_document" content="true" />\n<meta name="xmpTPg:NPages" content="1" />\n<meta name="pdf:hasXMP" content="false" />\n<meta name="access_permission:extract_content" content="true" />\n<meta name="access_permission:can_print" content="true" />\n<meta name="pdf:docinfo:trapped" content="False" />\n<meta name="X-TIKA:Parsed-By" content="org.apache.tika.parser.DefaultParser" />\n<meta name="X-TIKA:Parsed-By" content="org.apache.tika.parser.pdf.PDFParser" />\n<meta name="access_permission:can_modify" content="true" />\n<meta name="pdf:docinfo:producer" content="ReportLab PDF Library - www.reportlab.com" />\n<meta name="pdf:docinfo:created" content="2024-06-03T18:58:16Z" />\n<title>untitled</title>\n</head>\n<body><div class="page"><p />\n<p>Hello, World!</p>\n<p />\n</div>\n</body></html>',
        "access_permission:can_modify": "true",
        "pdf:docinfo:producer": "ReportLab PDF Library - www.reportlab.com",
        "pdf:docinfo:created": "2024-06-03T18:58:16Z",
        "pdf:containsDamagedFont": "false",
    }

    async def setup_after_prep(self, module_test):
        module_test.set_expect_requests(
            dict(uri="/"),
            dict(response_data='<a href="/Test_PDF"/>'),
        )
        module_test.set_expect_requests(
            dict(uri="/Test_PDF"),
            dict(response_data=self.pdf_data, headers={"Content-Type": "application/pdf"}),
        )

    def check(self, module_test, events):
        filesystem_events = [e for e in events if e.type == "FILESYSTEM"]
        assert 1 == len(filesystem_events), filesystem_events
        filesystem_event = filesystem_events[0]
        file = Path(filesystem_event.data["path"])
        assert file.is_file(), "Destination file doesn't exist"
        assert open(file).read() == self.pdf_data, f"File at {file} does not contain the correct content"
        raw_data_events = [e for e in events if e.type == "RAW_DATA"]
        assert 1 == len(raw_data_events), "Failed to emmit RAW_DATA event"
        assert (
            raw_data_events[0].data == self.tika_response
        ), f"Text extracted from PDF is incorrect, got {raw_data_events[0].data}"
