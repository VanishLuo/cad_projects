# Provider Start Option Configuration

## Goal

Make provider-specific startup option configurable without code changes.

Current command assembly logic:

`<start_executable_path> <start_file_option> [<log_option> <date_log_file>] <license_file_path>`

Example for FlexNet:

`C:/flexnet/lmgrd.exe -c -l C:/licenses/2026-03-23.log C:/licenses/prod_a.lic`

## Config File

Path:

`src/license_management/config/provider_start_options.json`

Schema:

```json
{
  "default": {
    "start_file_option": "-c",
    "log_option": "",
    "log_file_template": ""
  },
  "providers": {
    "flexnet": {
      "start_file_option": "-c",
      "log_option": "-l",
      "log_file_template": "{license_dir}/{date}.log"
    },
    "mathworks": {
      "start_file_option": "-c",
      "log_option": "",
      "log_file_template": ""
    }
  }
}
```

## How Matching Works

1. Read `provider` from record.
2. Normalize with lowercase and trim spaces.
3. Find `providers[provider]` in JSON.
4. If missing, use `default.start_file_option`, `default.log_option`, and `default.log_file_template`.
5. If record has `start_option_override`, it overrides config option tokens for this record.

## Add New Provider (No Code Change)

If a new provider needs different option, only update JSON:

```json
{
  "default": { "start_file_option": "-c", "log_option": "", "log_file_template": "" },
  "providers": {
    "flexnet": { "start_file_option": "-c", "log_option": "-l", "log_file_template": "{license_dir}/{date}.log" },
    "myprovider": { "start_file_option": "--license-file", "log_option": "", "log_file_template": "" }
  }
}
```

Then set record `provider` to `myprovider` and keep filling:
- `start_executable_path`
- `license_file_path`

No Python source change is required.

## Data Format Requirement

Legacy `start_command` is removed.

New payload must include:
- `start_executable_path`
- `license_file_path`

Optional:
- `start_option_override`

`start_option_override` can override JSON mapping for special single-record cases.

## FlexNet Fixed Pattern Example

If FlexNet should always use `-c` and `-l` with date log file in the same directory as license file, configure:

```json
{
  "providers": {
    "flexnet": {
      "start_file_option": "-c",
      "log_option": "-l",
      "log_file_template": "{license_dir}/{date}.log"
    }
  }
}
```

Generated command becomes:

`C:/flexnet/lmgrd.exe -c -l C:/licenses/2026-03-23.log C:/licenses/prod_a.lic`

Supported placeholders:

- `{date}`: current date in `YYYY-MM-DD`
- `{license_dir}`: directory of `license_file_path`
