# daylog

A text-file based time logging system.

## Dependencies

### Shell

- vim (Perhaps the editor will be configurable in the future)

## Setup

1. **Change the path variable**, `LOG_PATH`,  hardcoded into the top of
   `util.py`. This is where the hierarchy of text log files will be stored on
   your system.

An example file hierarchy looks like this:

```raw
2020/
├── Jan_time_sheet/
...
├── Nov_time_sheet/
└── Dec_time_sheet/
2021/
├── Jan_time_sheet/
|   ├── log01_04.txt
│   ├── log01_05.txt
│   ├── log01_06.txt
│   ├── log01_07.txt
│   ├── log01_08.txt
│   ├── log01_11.txt
|   ...
├── Feb_time_sheet/
├── Mar_time_sheet/
└── Apr_time_sheet/
```

2. (Optonal) **Create an Alias** to both `daysum.py` and `daylog.py`. I suggest
the shortened terms, `dsum` and `dlog` personally.

**Note**: These scripts will be referred to by their alias from now on.

## Usage

There are two Python scripts that make up the meat of this repo. That is the
two listed above, with the dedicated aliases, `dsum` and `dlog`.

- `dlog`

This is a thin wrapper for calling `vim`. The magic here is just choosing
the correct file path to open for editing. Simply invoke the script to open
today's daylog file:

```sh
dlog
```

An arbitrary date can also be entered for editing (e.g. April 1st, this year):

```sh
dlog 4 1
```

- `dsum`

This script is used to display summaries of the the day logs.

Invoke the script alone for a one-line picture of progress for the day:

```sh
dsum

|############################   | 7 hours

```

Try the `-w` or `-d` args for weekly views on your daylogs.

## Notes

Sadly, some of the help is outdated, mainly the `-v` and `-q` options for both
scripts. Also, their is a pretty significant refactor in the works, that is 
just upstream. It may change the way files are named.
