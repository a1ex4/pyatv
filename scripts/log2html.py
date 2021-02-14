#!/usr/bin/env python3
"""Script converting pyatv logs to HTML."""

import re
import sys
import logging
import argparse

_LOGGER = logging.getLogger(__name__)

LOG_LINE_RE = r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) ([A-Z]+):(.*)"

HTML_TEMPLATE = """<head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>pyatv log</title>
  <style type="text/css" media="screen">
    .box_log {{
      margin: 5px;
      padding: 5px;
      border-color: #aaaaaa;
      border-radius: 5px;
      border-style: dotted;
      background: #cccccc;
    }}
    .box_log summary {{
      overflow: scroll;
      white-space: wrap;
    }}
    .box_log pre {{
      overflow-x: auto;
    }}
  </style>
</head>
<body>
  {logs}
</body>
"""

LOG_TEMPLATE = """    <div class="box_log">
    <details>
        <summary>{summary}</summary>
        <pre>{details}</pre>
    </details>
    </div>
"""


def parse_logs(stream):
    """Parse lines in a log and return entries."""
    current_date = None
    currenf_level = None
    current_first_line = None
    current_content = ""

    for line in stream:
        match = re.match(LOG_LINE_RE, line)
        if not match:
            current_content += line
            continue

        if current_date:
            yield current_date, currenf_level, current_first_line, current_content

        current_date, currenf_level, current_content = match.groups()
        current_first_line = current_content
        current_content += "\n"

    if current_date:
        yield current_date, currenf_level, current_first_line, current_content


def generate_log_page(stream, output):
    """Generate HTML output for log output."""
    logs = []
    for logpoint in parse_logs(stream):
        date = logpoint[0]
        first_line = logpoint[2]
        content = logpoint[3]

        summary = date + " " + first_line[first_line.find(" ") :]
        logs.append(LOG_TEMPLATE.format(summary=summary, details=content))

    if not logs:
        _LOGGER.warning("No log points found, not generating output")
        return

    page = HTML_TEMPLATE.format(logs="\n".join(logs))
    if not output:
        print(page)
    else:
        with open(output, "w") as out:
            out.write(page)


def main():
    """Script starts here."""

    def _markdown_parser():
        """Look for markup start and end in input.

        This will look for input between tags looking like this:

        ```log

        ```
        """
        found = False
        for line in sys.stdin:
            if line.startswith("```log"):
                found = True
            elif line.startswith("```"):
                break
            elif found:
                yield line

    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="log file")
    parser.add_argument("-o", "--output", default=None, help="output file")
    args = parser.parse_args()

    if args.file == "-":
        generate_log_page(sys.stdin, args.output)
    elif args.file == "...":
        generate_log_page(_markdown_parser(), args.output)
    else:
        with open(args.file) as stream:
            generate_log_page(stream, args.output)


if __name__ == "__main__":
    main()
