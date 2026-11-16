# Security policy

## Supported versions

Only the latest commit on the default branch receives fixes. There are
no maintained release branches.

## Reporting a vulnerability

Please do not open a public issue for a security problem.

Report it privately through GitHub: open the repository's **Security**
tab and choose **Report a vulnerability**. Include the command you ran,
the input that triggers the problem (or a minimal reproduction), and
what you expected to happen.

You should get an acknowledgement within 14 days. Once a fix is ready,
the report will be credited in the fix commit unless you ask otherwise.

## Scope

voyant reads local text files and writes reports or one offline HTML
file. Issues that matter most here:

- input text that makes `view` produce HTML which runs script or loads
  remote content when opened
- crafted file names or contents that make the reader escape the given
  paths or write outside `--output`
- input that causes unbounded memory or time use out of proportion to
  its size
